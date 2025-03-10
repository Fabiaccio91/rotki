import json
from collections.abc import Sequence
from dataclasses import dataclass, field, fields
from typing import Any, NamedTuple, Optional, Union

from rotkehlchen.accounting.ledger_actions import LedgerActionType
from rotkehlchen.assets.asset import Asset, AssetWithOracles
from rotkehlchen.chain.constants import LAST_EVM_ACCOUNTS_DETECT_KEY
from rotkehlchen.constants.assets import A_USD
from rotkehlchen.constants.timing import YEAR_IN_SECONDS
from rotkehlchen.data_migrations.manager import LAST_DATA_MIGRATION
from rotkehlchen.db.updates import LAST_DATA_UPDATES_KEY, UpdateType
from rotkehlchen.db.utils import str_to_bool
from rotkehlchen.errors.serialization import DeserializationError
from rotkehlchen.history.types import DEFAULT_HISTORICAL_PRICE_ORACLES_ORDER, HistoricalPriceOracle
from rotkehlchen.inquirer import DEFAULT_CURRENT_PRICE_ORACLES_ORDER, CurrentPriceOracle
from rotkehlchen.types import (
    AVAILABLE_MODULES_MAP,
    DEFAULT_ADDRESS_NAME_PRIORITY,
    DEFAULT_OFF_MODULES,
    AddressNameSource,
    CostBasisMethod,
    ExchangeLocationID,
    ModuleName,
    Timestamp,
)
from rotkehlchen.user_messages import MessagesAggregator

ROTKEHLCHEN_DB_VERSION = 38
ROTKEHLCHEN_TRANSIENT_DB_VERSION = 1
DEFAULT_TAXFREE_AFTER_PERIOD = YEAR_IN_SECONDS
DEFAULT_INCLUDE_CRYPTO2CRYPTO = True
DEFAULT_INCLUDE_GAS_COSTS = True
DEFAULT_PREMIUM_SHOULD_SYNC = False
DEFAULT_UI_FLOATING_PRECISION = 2
DEFAULT_BALANCE_SAVE_FREQUENCY = 24
DEFAULT_MAIN_CURRENCY = A_USD
DEFAULT_DATE_DISPLAY_FORMAT = '%d/%m/%Y %H:%M:%S %Z'
DEFAULT_SUBMIT_USAGE_ANALYTICS = True
DEFAULT_ACTIVE_MODULES = tuple(set(AVAILABLE_MODULES_MAP.keys()) - DEFAULT_OFF_MODULES)
DEFAULT_ACCOUNT_FOR_ASSETS_MOVEMENTS = True
DEFAULT_BTC_DERIVATION_GAP_LIMIT = 20
DEFAULT_CALCULATE_PAST_COST_BASIS = True
DEFAULT_DISPLAY_DATE_IN_LOCALTIME = True
DEFAULT_CURRENT_PRICE_ORACLES = DEFAULT_CURRENT_PRICE_ORACLES_ORDER
DEFAULT_HISTORICAL_PRICE_ORACLES = DEFAULT_HISTORICAL_PRICE_ORACLES_ORDER
DEFAULT_TAXABLE_LEDGER_ACTIONS = (
    LedgerActionType.INCOME,
    LedgerActionType.EXPENSE,
    LedgerActionType.LOSS,
    LedgerActionType.DIVIDENDS_INCOME,
    LedgerActionType.DONATION_RECEIVED,
    LedgerActionType.GRANT,
)
DEFAULT_PNL_CSV_WITH_FORMULAS = True
DEFAULT_PNL_CSV_HAVE_SUMMARY = False
DEFAULT_SSF_GRAPH_MULTIPLIER = 0
DEFAULT_LAST_DATA_MIGRATION = LAST_DATA_MIGRATION
DEFAULT_COST_BASIS_METHOD = CostBasisMethod.FIFO
DEFAULT_TREAT_ETH2_AS_ETH = True
DEFAULT_ETH_STAKING_TAXABLE_AFTER_WITHDRAWAL_ENABLED = True
DEFAULT_INCLUDE_FEES_IN_COST_BASIS = True
DEFAULT_INFER_ZERO_TIMED_BALANCES = False  # If True the asset amount and value chart shows the 0 balance periods for an asset  # noqa: E501


JSON_KEYS = (
    'current_price_oracles',
    'historical_price_oracles',
    'taxable_ledger_actions',
    'non_syncing_exchanges',
)
BOOLEAN_KEYS = (
    'have_premium',
    'include_crypto2crypto',
    'include_gas_costs',
    'premium_should_sync',
    'submit_usage_analytics',
    'account_for_assets_movements',
    'calculate_past_cost_basis',
    'display_date_in_localtime',
    'pnl_csv_with_formulas',
    'pnl_csv_have_summary',
    'treat_eth2_as_eth',
    'eth_staking_taxable_after_withdrawal_enabled',
    'include_fees_in_cost_basis',
    'infer_zero_timed_balances',
)
INTEGER_KEYS = (
    'version',
    'ui_floating_precision',
    'balance_save_frequency',
    'btc_derivation_gap_limit',
    'ssf_graph_multiplier',
    'last_data_migration',
)
STRING_KEYS = (
    'ksm_rpc_endpoint',
    'dot_rpc_endpoint',
    'date_display_format',
    'frontend_settings',
)
TIMESTAMP_KEYS = ('last_write_ts', 'last_data_upload_ts', 'last_balance_save')
IGNORED_KEYS = (LAST_EVM_ACCOUNTS_DETECT_KEY, LAST_DATA_UPDATES_KEY) + tuple(x.serialize() for x in UpdateType)  # noqa: E501


@dataclass(init=True, repr=True, eq=True, order=False, unsafe_hash=False, frozen=True)
class DBSettings:
    have_premium: bool = False
    version: int = ROTKEHLCHEN_DB_VERSION
    last_write_ts: Timestamp = field(default=Timestamp(0))
    premium_should_sync: bool = DEFAULT_PREMIUM_SHOULD_SYNC
    include_crypto2crypto: bool = DEFAULT_INCLUDE_CRYPTO2CRYPTO
    last_data_upload_ts: Timestamp = field(default=Timestamp(0))
    ui_floating_precision: int = DEFAULT_UI_FLOATING_PRECISION
    taxfree_after_period: Optional[int] = DEFAULT_TAXFREE_AFTER_PERIOD
    balance_save_frequency: int = DEFAULT_BALANCE_SAVE_FREQUENCY
    include_gas_costs: bool = DEFAULT_INCLUDE_GAS_COSTS
    ksm_rpc_endpoint: str = 'http://localhost:9933'
    dot_rpc_endpoint: str = ''  # same as kusama -- must be set by user
    main_currency: Asset = DEFAULT_MAIN_CURRENCY
    date_display_format: str = DEFAULT_DATE_DISPLAY_FORMAT
    last_balance_save: Timestamp = field(default=Timestamp(0))
    submit_usage_analytics: bool = DEFAULT_SUBMIT_USAGE_ANALYTICS
    active_modules: Sequence[ModuleName] = field(default=DEFAULT_ACTIVE_MODULES)  # type: ignore
    frontend_settings: str = ''
    account_for_assets_movements: bool = DEFAULT_ACCOUNT_FOR_ASSETS_MOVEMENTS
    btc_derivation_gap_limit: int = DEFAULT_BTC_DERIVATION_GAP_LIMIT
    calculate_past_cost_basis: bool = DEFAULT_CALCULATE_PAST_COST_BASIS
    display_date_in_localtime: bool = DEFAULT_DISPLAY_DATE_IN_LOCALTIME
    current_price_oracles: Sequence[CurrentPriceOracle] = field(default=DEFAULT_CURRENT_PRICE_ORACLES)  # noqa: E501
    historical_price_oracles: Sequence[HistoricalPriceOracle] = field(default=DEFAULT_HISTORICAL_PRICE_ORACLES)  # noqa: E501
    taxable_ledger_actions: Sequence[LedgerActionType] = field(default=DEFAULT_TAXABLE_LEDGER_ACTIONS)  # noqa: E501
    pnl_csv_with_formulas: bool = DEFAULT_PNL_CSV_WITH_FORMULAS
    pnl_csv_have_summary: bool = DEFAULT_PNL_CSV_HAVE_SUMMARY
    ssf_graph_multiplier: int = DEFAULT_SSF_GRAPH_MULTIPLIER
    last_data_migration: int = DEFAULT_LAST_DATA_MIGRATION
    non_syncing_exchanges: Sequence[ExchangeLocationID] = field(default_factory=list)
    cost_basis_method: CostBasisMethod = DEFAULT_COST_BASIS_METHOD
    treat_eth2_as_eth: bool = DEFAULT_TREAT_ETH2_AS_ETH
    eth_staking_taxable_after_withdrawal_enabled: bool = DEFAULT_ETH_STAKING_TAXABLE_AFTER_WITHDRAWAL_ENABLED  # noqa: 501
    address_name_priority: Sequence[AddressNameSource] = DEFAULT_ADDRESS_NAME_PRIORITY
    include_fees_in_cost_basis: bool = DEFAULT_INCLUDE_FEES_IN_COST_BASIS
    infer_zero_timed_balances: bool = DEFAULT_INFER_ZERO_TIMED_BALANCES

    def serialize(self) -> dict[str, Any]:
        settings_dict = {}
        for field_entry in fields(self):
            value = getattr(self, field_entry.name)
            if value is not None:
                serialized_value = serialize_db_setting(
                    value=value,
                    setting=field_entry.name,
                    is_modifiable=False,
                )
            else:
                serialized_value = value

            settings_dict[field_entry.name] = serialized_value

        return settings_dict


class ModifiableDBSettings(NamedTuple):
    premium_should_sync: Optional[bool] = None
    include_crypto2crypto: Optional[bool] = None
    ui_floating_precision: Optional[int] = None
    taxfree_after_period: Optional[int] = None
    balance_save_frequency: Optional[int] = None
    include_gas_costs: Optional[bool] = None
    ksm_rpc_endpoint: Optional[str] = None
    dot_rpc_endpoint: Optional[str] = None
    main_currency: Optional[AssetWithOracles] = None
    date_display_format: Optional[str] = None
    submit_usage_analytics: Optional[bool] = None
    active_modules: Optional[list[ModuleName]] = None
    frontend_settings: Optional[str] = None
    account_for_assets_movements: Optional[bool] = None
    btc_derivation_gap_limit: Optional[int] = None
    calculate_past_cost_basis: Optional[bool] = None
    display_date_in_localtime: Optional[bool] = None
    current_price_oracles: Optional[list[CurrentPriceOracle]] = None
    historical_price_oracles: Optional[list[HistoricalPriceOracle]] = None
    taxable_ledger_actions: Optional[list[LedgerActionType]] = None
    pnl_csv_with_formulas: Optional[bool] = None
    pnl_csv_have_summary: Optional[bool] = None
    ssf_graph_multiplier: Optional[int] = None
    non_syncing_exchanges: Optional[list[ExchangeLocationID]] = None
    cost_basis_method: Optional[CostBasisMethod] = None
    treat_eth2_as_eth: Optional[bool] = None
    eth_staking_taxable_after_withdrawal_enabled: Optional[bool] = None
    address_name_priority: Optional[list[AddressNameSource]] = None
    include_fees_in_cost_basis: Optional[bool] = None
    infer_zero_timed_balances: Optional[bool] = None

    def serialize(self) -> dict[str, Any]:
        settings_dict = {}
        for setting in ModifiableDBSettings._fields:
            value = getattr(self, setting)
            if value is not None:
                serialized_value = serialize_db_setting(
                    value=value,
                    setting=setting,
                    is_modifiable=True,
                )
                settings_dict[setting] = serialized_value
        return settings_dict


def read_boolean(value: Union[str, bool]) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return str_to_bool(value)
    # else
    raise DeserializationError(
        f'Failed to read a boolean from {value} which is of type {type(value)}',
    )


def db_settings_from_dict(
        settings_dict: dict[str, Any],
        msg_aggregator: MessagesAggregator,
) -> DBSettings:
    specified_args: dict[str, Any] = {}
    for key, value in settings_dict.items():
        if key in BOOLEAN_KEYS:
            specified_args[key] = read_boolean(value)
        elif key in INTEGER_KEYS:
            specified_args[key] = int(value)
        elif key in STRING_KEYS:
            specified_args[key] = str(value)
        elif key in IGNORED_KEYS:  # temp until https://github.com/rotki/rotki/issues/5684 is done
            continue  # some keys are using the settings table in lieu of a key-value cache
        elif key == 'taxfree_after_period':
            # taxfree_after_period can also be None, to signify disabled setting
            if value is None:
                specified_args[key] = value
            else:
                int_value = int(value)
                if int_value <= 0:
                    msg_aggregator.add_warning(
                        f'A negative or zero value ({int_value}) for taxfree_after_period '
                        f'ended up in the DB. Setting it to None. Please open an issue in '
                        f'Github: https://github.com/rotki/rotki/issues/new/choose',
                    )
                    int_value = None  # type: ignore[assignment]  # we do it on purpose
                specified_args[key] = int_value

        elif key == 'main_currency':
            specified_args[key] = Asset(str(value)).resolve_to_asset_with_oracles()
        elif key in TIMESTAMP_KEYS:
            specified_args[key] = Timestamp(int(value))
        elif key == 'active_modules':
            specified_args[key] = json.loads(value)
        elif key == 'current_price_oracles':
            oracles = json.loads(value)
            specified_args[key] = [CurrentPriceOracle.deserialize(oracle) for oracle in oracles]
        elif key == 'historical_price_oracles':
            oracles = json.loads(value)
            specified_args[key] = [HistoricalPriceOracle.deserialize(oracle) for oracle in oracles]
        elif key == 'taxable_ledger_actions':
            values = json.loads(value)
            specified_args[key] = [LedgerActionType.deserialize(x) for x in values]
        elif key == 'non_syncing_exchanges':
            values = json.loads(value)
            specified_args[key] = [ExchangeLocationID.deserialize(x) for x in values]
        elif key == 'cost_basis_method':
            specified_args[key] = CostBasisMethod.deserialize(value)
        elif key == 'address_name_priority':
            specified_args[key] = json.loads(value)
        else:
            if key == 'eth_rpc_endpoint':
                continue  # temporary since setting is removed in migration and may still get here

            msg_aggregator.add_warning(
                f'Unknown DB setting {key} given. Ignoring it. Should not '
                f'happen so please open an issue in Github.',
            )

    return DBSettings(**specified_args)


def serialize_db_setting(
        value: Any,
        setting: Any,
        is_modifiable: bool,
) -> Any:
    """Utility function to serialize a db setting.
    `is_modifiable` represents `ModifiableDBSettings` specific flag.
    """
    # We need to save booleans as strings in the DB
    if isinstance(value, bool) and is_modifiable is True:
        value = str(value)
    # taxfree_after_period of -1 by the user means disable the setting
    elif setting == 'taxfree_after_period' and value == -1 and is_modifiable is True:
        value = None
    elif setting == 'active_modules' and is_modifiable is True:
        value = json.dumps(value)
    elif setting in ('main_currency', 'cost_basis_method'):
        value = value.serialize()  # pylint: disable=no-member
    elif setting == 'address_name_priority' and is_modifiable is True:
        value = json.dumps(value)
    elif setting in JSON_KEYS:
        if is_modifiable is True:
            value = json.dumps([x.serialize() for x in value])
        else:
            value = [x.serialize() for x in value]
    return value
