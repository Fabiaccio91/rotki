import logging
from typing import TYPE_CHECKING, Any, Callable, Optional

from rotkehlchen.accounting.structures.types import HistoryEventSubType, HistoryEventType
from rotkehlchen.chain.ethereum.modules.balancer.constants import BALANCER_LABEL, CPT_BALANCER_V1
from rotkehlchen.chain.ethereum.modules.balancer.types import BalancerV1EventTypes
from rotkehlchen.chain.evm.decoding.interfaces import DecoderInterface
from rotkehlchen.chain.evm.decoding.structures import (
    FAILED_ENRICHMENT_OUTPUT,
    EnricherContext,
    TransferEnrichmentOutput,
)
from rotkehlchen.chain.evm.decoding.types import CounterpartyDetails, EventCategory
from rotkehlchen.chain.evm.decoding.utils import maybe_reshuffle_events
from rotkehlchen.chain.evm.structures import EvmTxReceiptLog
from rotkehlchen.logging import RotkehlchenLogsAdapter
from rotkehlchen.types import DecoderEventMappingType, EvmTransaction
from rotkehlchen.utils.misc import hex_or_bytes_to_address, hex_or_bytes_to_int

if TYPE_CHECKING:
    from rotkehlchen.accounting.structures.evm_event import EvmEvent
    from rotkehlchen.chain.evm.decoding.base import BaseDecoderTools
    from rotkehlchen.chain.evm.node_inquirer import EvmNodeInquirer
    from rotkehlchen.user_messages import MessagesAggregator

JOIN_V1 = b'c\x98-\xf1\x0e\xfd\x8d\xfa\xaa\xa0\xfc\xc7\xf5\x0b-\x93\xb7\xcb\xa2l\xccH\xad\xee(s"\rH]\xc3\x9a'  # noqa: E501
EXIT_V1 = b'\xe7L\x91U+d\xc2\xe2\xe7\xbd%V9\xe0\x04\xe6\x93\xbd>\x1d\x01\xcc3\xe6V\x10\xb8j\xfc\xc1\xff\xed'  # noqa: E501

logger = logging.getLogger(__name__)
log = RotkehlchenLogsAdapter(logger)


class Balancerv1Decoder(DecoderInterface):

    def __init__(
            self,
            evm_inquirer: 'EvmNodeInquirer',
            base_tools: 'BaseDecoderTools',
            msg_aggregator: 'MessagesAggregator',
    ) -> None:
        super().__init__(
            evm_inquirer=evm_inquirer,
            base_tools=base_tools,
            msg_aggregator=msg_aggregator,
        )

    def _decode_v1_pool_event(self, all_logs: list[EvmTxReceiptLog]) -> Optional[list[dict[str, Any]]]:  # noqa: E501
        """Read the list of logs in search for a Balancer v1 event and return the information
        needed to decode the transfers made in the transaction to/from the ds proxy
        """
        # The transfer event appears after the debt generation event, so we need to transform it
        target_logs = []
        for tx_log in all_logs:
            if tx_log.topics[0] == JOIN_V1 or tx_log.topics[0] == EXIT_V1:
                target_logs.append(tx_log)

        if len(target_logs) == 0:
            return None

        events_information = []
        for target_log in target_logs:
            token_address = hex_or_bytes_to_address(target_log.topics[2])
            amount = hex_or_bytes_to_int(target_log.data[0:32])
            if target_log.topics[0] == JOIN_V1:
                balancer_event_type = BalancerV1EventTypes.JOIN
                ds_address = hex_or_bytes_to_address(target_log.topics[1])
            else:
                balancer_event_type = BalancerV1EventTypes.EXIT
                ds_address = target_log.address

            proxy_event_information = {
                'ds_address': ds_address,
                'token_address': token_address,
                'amount': amount,
                'type': balancer_event_type,
            }
            events_information.append(proxy_event_information)

        return events_information

    def _maybe_enrich_balancer_v1_events(
            self,
            context: EnricherContext,
    ) -> TransferEnrichmentOutput:
        """
        Enrich balancer v1 transfer to read pool events of:
        - Depositing in the pool
        - Withdrawing from the pool

        In balancer v1 pools are managed using a DSProxy so the account doesn't interact
        directly with the pools.
        """
        events_information = self._decode_v1_pool_event(all_logs=context.all_logs)
        if events_information is None:
            return FAILED_ENRICHMENT_OUTPUT

        for proxied_event in events_information:
            if proxied_event['ds_address'] != context.event.address:
                continue

            if proxied_event['type'] == BalancerV1EventTypes.JOIN:
                if (
                    context.event.event_type == HistoryEventType.RECEIVE and
                    context.event.event_subtype == HistoryEventSubType.NONE
                ):
                    context.event.event_subtype = HistoryEventSubType.RECEIVE_WRAPPED
                    context.event.counterparty = CPT_BALANCER_V1
                    context.event.notes = f'Receive {context.event.balance.amount} {context.token.symbol} from a Balancer v1 pool'  # noqa: E501
                    return TransferEnrichmentOutput(matched_counterparty=CPT_BALANCER_V1)
                if (
                    context.event.event_type == HistoryEventType.SPEND and
                    context.event.event_subtype == HistoryEventSubType.NONE
                ):
                    context.event.event_type = HistoryEventType.DEPOSIT
                    context.event.event_subtype = HistoryEventSubType.DEPOSIT_ASSET
                    context.event.counterparty = CPT_BALANCER_V1
                    context.event.notes = f'Deposit {context.event.balance.amount} {context.token.symbol} to a Balancer v1 pool'  # noqa: E501
                    return TransferEnrichmentOutput(matched_counterparty=CPT_BALANCER_V1)
            elif proxied_event['type'] == BalancerV1EventTypes.EXIT:
                if (
                    context.event.event_type == HistoryEventType.RECEIVE and
                    context.event.event_subtype == HistoryEventSubType.NONE
                ):
                    context.event.event_type = HistoryEventType.WITHDRAWAL
                    context.event.event_subtype = HistoryEventSubType.REMOVE_ASSET
                    context.event.counterparty = CPT_BALANCER_V1
                    context.event.notes = f'Receive {context.event.balance.amount} {context.token.symbol} after removing liquidity from a Balancer v1 pool'  # noqa: E501
                    return TransferEnrichmentOutput(matched_counterparty=CPT_BALANCER_V1)
                if (
                    context.event.event_type == HistoryEventType.SPEND and
                    context.event.event_subtype == HistoryEventSubType.NONE
                ):
                    context.event.event_subtype = HistoryEventSubType.RETURN_WRAPPED
                    context.event.counterparty = CPT_BALANCER_V1
                    context.event.notes = f'Return {context.event.balance.amount} {context.token.symbol} to a Balancer v1 pool'  # noqa: E501
                    return TransferEnrichmentOutput(matched_counterparty=CPT_BALANCER_V1)

        return FAILED_ENRICHMENT_OUTPUT

    def _check_refunds_v1(
            self,
            transaction: EvmTransaction,  # pylint: disable=unused-argument
            decoded_events: list['EvmEvent'],
            all_logs: list[EvmTxReceiptLog],  # pylint: disable=unused-argument
    ) -> list['EvmEvent']:
        """
        It can happen that after sending tokens to the DSProxy in balancer V1 the amount of tokens
        required for the deposit is lower than the amount sent and then those tokens are returned
        to the DSProxy and then to the user.
        """
        deposited_assets = set()

        for event in decoded_events:
            if event.counterparty != CPT_BALANCER_V1:
                continue

            if (
                event.event_type == HistoryEventType.DEPOSIT and
                event.event_subtype == HistoryEventSubType.DEPOSIT_ASSET
            ):
                deposited_assets.add(event.asset)
            elif (
                event.event_type == HistoryEventType.RECEIVE and
                event.event_subtype == HistoryEventSubType.RECEIVE_WRAPPED and
                event.asset in deposited_assets
            ):
                # in this case we got refunded one of the assets deposited
                event.event_subtype = HistoryEventSubType.REMOVE_ASSET
                asset = event.asset.resolve_to_asset_with_symbol()
                event.notes = f'Refunded {event.balance.amount} {asset.symbol} after depositing in Balancer V1 pool'  # noqa: E501

        return decoded_events

    def _check_deposits_withdrawals_v1(
            self,
            transaction: EvmTransaction,  # pylint: disable=unused-argument
            decoded_events: list['EvmEvent'],
            all_logs: list[EvmTxReceiptLog],  # pylint: disable=unused-argument
    ) -> list['EvmEvent']:
        """
        Check for accounting in v1 that the deposits/withdrawals events have the needed information
        to process them during accounting.
        """
        related_events: list['EvmEvent'] = []
        related_events_map: dict['EvmEvent', list['EvmEvent']] = {}
        # last event is only tracked in the case of exiting a pool and contains the event
        # sending the BPT token
        last_event = None
        for event in decoded_events:
            if event.counterparty != CPT_BALANCER_V1:
                continue

            # When joining a pool first we spend the assets and then we receive the BPT token.
            # In the case of exiting the pool first we return the BPT token and then we receive
            # the assets.
            # To handle the case of multiple events happening in the same transaction properly we
            # accumulate them in the current list of events and then we empty it in the
            # related_events map
            if (
                event.event_type == HistoryEventType.RECEIVE and
                event.event_subtype == HistoryEventSubType.RECEIVE_WRAPPED
            ):
                if len(related_events) != 0:
                    related_events_map[event] = related_events
                    related_events = []
                    last_event = None

            elif (
                event.event_type == HistoryEventType.SPEND and
                event.event_subtype == HistoryEventSubType.RETURN_WRAPPED
            ):
                related_events = []
                last_event = event

            elif (
                (
                    event.event_type == HistoryEventType.DEPOSIT and
                    event.event_subtype == HistoryEventSubType.DEPOSIT_ASSET
                ) or
                (
                    event.event_type == HistoryEventType.RECEIVE and
                    event.event_subtype == HistoryEventSubType.REMOVE_ASSET
                )
            ):
                # In the case that we are handling a join that comes after an exit we have to
                # check if there is a change in the direction of the assets (from spending them)
                # to receiving them
                if last_event is not None:
                    # save the exit event and reset the related events
                    related_events_map[last_event] = related_events
                    last_event = None
                    related_events = []

                related_events.append(event)

            elif (
                event.event_type == HistoryEventType.WITHDRAWAL and
                event.event_subtype == HistoryEventSubType.REMOVE_ASSET
            ):
                related_events.append(event)

        # in the case of returning the BPT token we have to see if we had any pending operation
        if last_event is not None:
            related_events_map[last_event] = related_events

        if len(related_events_map) == 0:
            # it was not a balancer v1 related transaction so exit early
            return decoded_events

        for pool_token_event, token_related_events in related_events_map.items():
            if pool_token_event.event_type == HistoryEventType.RECEIVE:
                pool_token_event.extra_data = {'deposit_events_num': len(token_related_events)}
            else:
                pool_token_event.extra_data = {'withdrawal_events_num': len(token_related_events)}

            # sort the events so the send/receive of the wrapped token comes first
            # and then the related events
            maybe_reshuffle_events(
                ordered_events=[pool_token_event] + token_related_events,
                events_list=decoded_events,
            )

        return decoded_events

    # -- DecoderInterface methods

    def possible_events(self) -> DecoderEventMappingType:
        return {
            CPT_BALANCER_V1: {
                HistoryEventType.RECEIVE: {
                    HistoryEventSubType.RECEIVE_WRAPPED: EventCategory.RECEIVE,
                    HistoryEventSubType.REMOVE_ASSET: EventCategory.REFUND,
                },
                HistoryEventType.SPEND: {
                    HistoryEventSubType.RETURN_WRAPPED: EventCategory.SEND,
                },
                HistoryEventType.WITHDRAWAL: {
                    HistoryEventSubType.REMOVE_ASSET: EventCategory.WITHDRAW,
                },
                HistoryEventType.DEPOSIT: {
                    HistoryEventSubType.DEPOSIT_ASSET: EventCategory.DEPOSIT,
                },
            },
        }

    def enricher_rules(self) -> list[Callable]:
        return [
            self._maybe_enrich_balancer_v1_events,
        ]

    def counterparties(self) -> list[CounterpartyDetails]:
        return [CounterpartyDetails(
            identifier=CPT_BALANCER_V1,
            label=BALANCER_LABEL,
            image='balancer.svg',
        )]

    def post_decoding_rules(self) -> dict[str, list[tuple[int, Callable]]]:
        return {
            CPT_BALANCER_V1: [
                (0, self._check_refunds_v1),
                (1, self._check_deposits_withdrawals_v1),
            ],
        }
