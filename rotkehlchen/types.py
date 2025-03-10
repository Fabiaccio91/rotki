import typing
from collections.abc import Sequence
from enum import Enum, auto
from typing import (
    TYPE_CHECKING,
    Any,
    Final,
    Literal,
    NamedTuple,
    NewType,
    Optional,
    TypeVar,
    Union,
    get_args,
)

from eth_typing import ChecksumAddress
from hexbytes import HexBytes as Web3HexBytes

from rotkehlchen.errors.misc import InputError
from rotkehlchen.errors.serialization import DeserializationError
from rotkehlchen.fval import FVal
from rotkehlchen.utils.hexbytes import HexBytes
from rotkehlchen.utils.mixins.enums import (
    DBCharEnumMixIn,
    SerializableEnumNameMixin,
    SerializableEnumValueMixin,
)

from rotkehlchen.chain.substrate.types import SubstrateAddress  # isort:skip

if TYPE_CHECKING:
    from rotkehlchen.accounting.structures.types import HistoryEventSubType, HistoryEventType
    from rotkehlchen.chain.evm.decoding.types import EventCategory

ModuleName = Literal[
    'makerdao_dsr',
    'makerdao_vaults',
    'aave',
    'compound',
    'yearn_vaults',
    'yearn_vaults_v2',
    'uniswap',
    'loopring',
    'balancer',
    'eth2',
    'sushiswap',
    'liquity',
    'pickle_finance',
    'nfts',
]

# TODO: Turn this into some kind of light data structure and not just a mapping
# This is a mapping of module ids to human readable names
AVAILABLE_MODULES_MAP = {
    'makerdao_dsr': 'MakerDAO DSR',
    'makerdao_vaults': 'MakerDAO Vaults',
    'aave': 'Aave',
    'compound': 'Compound',
    'yearn_vaults': 'Yearn Vaults',
    'yearn_vaults_v2': 'Yearn V2 Vaults',
    'uniswap': 'Uniswap',
    'loopring': 'Loopring',
    'balancer': 'Balancer',
    'eth2': 'Eth2',
    'sushiswap': 'Sushiswap',
    'liquity': 'Liquity',
    'pickle_finance': 'Pickle Finance',
    'nfts': 'NFTs',
}

DEFAULT_OFF_MODULES = {'makerdao_dsr', 'yearn_vaults'}


UNISWAP_PROTOCOL: Final = 'UNI-V2'
SUSHISWAP_PROTOCOL: Final = 'SLP'
# this variable is used in the decoders and maps to the protocol field used in the database
# for yearn vaults v1
YEARN_VAULTS_V1_PROTOCOL = 'yearn_vaults_v1'
YEARN_VAULTS_V2_PROTOCOL = 'yearn_vaults_v2'
CURVE_POOL_PROTOCOL = 'curve_pool'
PICKLE_JAR_PROTOCOL = 'pickle_jar'
SPAM_PROTOCOL = 'spam'


# The protocols for which we know how to calculate their prices
ProtocolsWithPriceLogic = (
    UNISWAP_PROTOCOL,
    YEARN_VAULTS_V2_PROTOCOL,
    CURVE_POOL_PROTOCOL,
)


T_Timestamp = int
Timestamp = NewType('Timestamp', T_Timestamp)

T_TimestampMS = int
TimestampMS = NewType('TimestampMS', T_TimestampMS)

T_ApiKey = str
ApiKey = NewType('ApiKey', T_ApiKey)

T_ApiSecret = bytes
ApiSecret = NewType('ApiSecret', T_ApiSecret)

T_B64EncodedBytes = bytes
B64EncodedBytes = NewType('B64EncodedBytes', T_B64EncodedBytes)

T_B64EncodedString = str
B64EncodedString = NewType('B64EncodedString', T_B64EncodedString)

T_HexColorCode = str
HexColorCode = NewType('HexColorCode', T_HexColorCode)


class ExternalService(SerializableEnumNameMixin):
    ETHERSCAN = 0
    CRYPTOCOMPARE = 1
    BEACONCHAIN = 2
    LOOPRING = 3
    OPENSEA = 4
    COVALENT = 5
    OPTIMISM_ETHERSCAN = 6
    POLYGON_POS_ETHERSCAN = 7


class ExternalServiceApiCredentials(NamedTuple):
    """Represents Credentials for various External APIs. Etherscan, Cryptocompare e.t.c.

    The Api in question must at least have an API key.
    """
    service: ExternalService
    api_key: ApiKey

    def serialize_for_db(self) -> tuple[str, str]:
        return (self.service.name.lower(), self.api_key)


T_TradePair = str
TradePair = NewType('TradePair', T_TradePair)

T_EvmAddres = str
EvmAddress = NewType('EvmAddress', T_EvmAddres)

ChecksumEvmAddress = ChecksumAddress

T_EVMTxHash = HexBytes
EVMTxHash = NewType('EVMTxHash', T_EVMTxHash)


def deserialize_evm_tx_hash(val: Union[Web3HexBytes, bytearray, bytes, str]) -> EVMTxHash:
    """Super lightweight wrapper to forward arguments to HexBytes and return an EVMTxHash

    HexBytes constructor handles the deserialization from whatever is given as input.

    May raise DeserializationError if there is an error at deserialization

    NB: Does not actually check that it's 32 bytes. This should happen at reading
    data from outside such as in the marshmallow field validation
    """
    return EVMTxHash(HexBytes(val))


T_BTCAddress = str
BTCAddress = NewType('BTCAddress', T_BTCAddress)

T_Eth2PubKey = str
Eth2PubKey = NewType('Eth2PubKey', T_Eth2PubKey)

BlockchainAddress = Union[
    BTCAddress,
    ChecksumEvmAddress,
    SubstrateAddress,
]
AnyBlockchainAddress = TypeVar(
    'AnyBlockchainAddress',
    BTCAddress,
    ChecksumEvmAddress,
    SubstrateAddress,
)
ListOfBlockchainAddresses = Union[
    list[BTCAddress],
    list[ChecksumEvmAddress],
    list[SubstrateAddress],
]
TuplesOfBlockchainAddresses = Union[
    tuple[BTCAddress, ...],
    tuple[ChecksumEvmAddress, ...],
    tuple[SubstrateAddress, ...],
]


T_Fee = FVal
Fee = NewType('Fee', T_Fee)

T_Price = FVal
Price = NewType('Price', T_Price)

T_AssetAmount = FVal
AssetAmount = NewType('AssetAmount', T_AssetAmount)

T_TradeID = str
TradeID = NewType('TradeID', T_TradeID)


class ChainID(Enum):
    """This class maps each EVM chain to their chain id. This is used to correctly identify EVM
    assets and use it where these ids are needed.

    This enum implements custom serialization/deserialization so it does not inherit from the
    DBIntEnumMixIn since it may differ a bit. TODO: Try it
    """
    ETHEREUM = 1
    OPTIMISM = 10
    BINANCE = 56
    GNOSIS = 100
    POLYGON_POS = 137
    FANTOM = 250
    ARBITRUM_ONE = 42161
    AVALANCHE = 43114
    CELO = 42220

    @classmethod
    def deserialize_from_db(cls, value: int) -> 'ChainID':
        try:
            return cls(value)
        except ValueError as e:
            raise DeserializationError(f'Could not deserialize ChainID from value {value}') from e

    def serialize_for_db(self) -> int:
        return self.value

    def serialize(self) -> int:
        return self.value

    @classmethod
    def deserialize(cls, value: int) -> 'ChainID':
        return cls.deserialize_from_db(value)

    def to_name(self) -> str:
        """The name to be used to/from the api instead of the chain id"""
        return self.name.lower()

    def name_and_label(self) -> tuple[str, str]:
        """A label to be used by the frontend.

        Also returns the name since the only place where label is currently used
        the name is also needed. To avoid 1 extra call to name"""
        name = self.to_name()
        if self == ChainID.POLYGON_POS:
            label = 'Polygon POS'
        elif self == ChainID.BINANCE:
            label = 'Binance Smart Chain'
        elif self == ChainID.ARBITRUM_ONE:
            label = 'Arbitrum One'
        else:
            label = name.capitalize()

        return name, label

    def __str__(self) -> str:
        return self.to_name()

    @classmethod
    def deserialize_from_name(cls, value: str) -> 'ChainID':
        """May raise DeserializationError if the given value can't be deserialized"""
        if not isinstance(value, str):
            raise DeserializationError(
                f'Failed to deserialize evm chain value from non string value: {value}',
            )

        upper_value = value.replace(' ', '_').upper()
        try:
            return getattr(cls, upper_value)
        except AttributeError as e:
            raise DeserializationError(f'Failed to deserialize evm chain value {value}') from e  # noqa: E501

    def to_blockchain(self) -> 'SupportedBlockchain':
        return CHAINID_TO_SUPPORTED_BLOCKCHAIN[self]


SUPPORTED_CHAIN_IDS = Literal[ChainID.ETHEREUM, ChainID.OPTIMISM, ChainID.POLYGON_POS]


class EvmTransaction(NamedTuple):
    """Represent an EVM transaction"""
    tx_hash: EVMTxHash
    chain_id: ChainID
    timestamp: Timestamp
    block_number: int
    from_address: ChecksumEvmAddress
    to_address: Optional[ChecksumEvmAddress]
    value: int
    gas: int
    gas_price: int
    gas_used: int
    input_data: bytes
    nonce: int

    def serialize(self) -> dict[str, Any]:
        result = self._asdict()  # pylint: disable=no-member
        result['tx_hash'] = result['tx_hash'].hex()
        result['evm_chain'] = result.pop('chain_id').to_name()
        result['input_data'] = '0x' + result['input_data'].hex()

        # Most integers are turned to string to be sent via the API
        result['value'] = str(result['value'])
        result['gas'] = str(result['gas'])
        result['gas_price'] = str(result['gas_price'])
        result['gas_used'] = str(result['gas_used'])
        return result

    def __hash__(self) -> int:
        return hash(self.identifier)

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, EvmTransaction):
            return False

        return hash(self) == hash(other)

    @property
    def identifier(self) -> str:
        return str(self.chain_id.value) + self.tx_hash.hex()


class EvmInternalTransaction(NamedTuple):
    """Represent an internal EVM transaction"""
    parent_tx_hash: EVMTxHash
    chain_id: ChainID
    trace_id: int
    from_address: ChecksumEvmAddress
    to_address: Optional[ChecksumEvmAddress]
    value: int

    def serialize(self) -> dict[str, Any]:
        result = self._asdict()  # pylint: disable=no-member
        result['tx_hash'] = result['tx_hash'].hex()
        result['chain_id'] = result['chain_id'].serialize()
        result['value'] = str(result['value'])
        return result

    def __hash__(self) -> int:
        return hash(self.identifier)

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, EvmInternalTransaction):
            return False

        return hash(self) == hash(other)

    @property
    def identifier(self) -> str:
        return str(self.chain_id.serialize()) + self.parent_tx_hash.hex() + str(self.trace_id)  # noqa: E501


class CovalentTransaction(NamedTuple):
    """Represent a transaction in covalent"""
    tx_hash: str
    timestamp: Timestamp
    block_number: int
    from_address: ChecksumEvmAddress
    to_address: Optional[ChecksumEvmAddress]
    value: int
    gas: int
    gas_price: int
    gas_used: int
    # Input data and nonce is decoded, default is 0x and 0, encoded in future
    input_data: str
    nonce: int

    def serialize(self) -> dict[str, Any]:
        result = {
            'tx_hash': self.tx_hash,
            'timestamp': self.timestamp,
            'block_number': self.block_number,
            'from_address': self.from_address,
            'to_address': self.to_address,
            'value': self.value,
            'gas': self.gas,
            'gas_price': self.gas_price,
            'gas_used': self.gas_used,
            'input_data': self.input_data,
            'nonce': self.nonce,
        }

        return result

    def __hash__(self) -> int:
        return hash(self.identifier)

    def __eq__(self, other: Any) -> bool:
        if other is None or not isinstance(other, CovalentTransaction):
            return False

        return hash(self) == hash(other)

    @property
    def identifier(self) -> str:
        return self.tx_hash + self.from_address.replace('0x', '') + str(self.nonce)


class SupportedBlockchain(SerializableEnumValueMixin):
    """
    These are the currently supported chains in any capacity in rotki
    """
    ETHEREUM = 'ETH'
    ETHEREUM_BEACONCHAIN = 'ETH2'
    BITCOIN = 'BTC'
    BITCOIN_CASH = 'BCH'
    KUSAMA = 'KSM'
    AVALANCHE = 'AVAX'
    POLKADOT = 'DOT'
    OPTIMISM = 'OPTIMISM'
    POLYGON_POS = 'POLYGON_POS'

    def __str__(self) -> str:
        return SUPPORTED_BLOCKCHAIN_NAMES_MAPPING.get(self, super().__str__())

    def serialize(self) -> str:
        """
        Serialize is used expose the enum to the frontend. For consistency we expose the key that
        that is used in the backend that is compatible with the default deserialize method.
        """
        return self.get_key()

    def get_key(self) -> str:
        """Returns the key to be used as attribute for this chain in the code"""
        return self.value.lower()

    def is_evm(self) -> bool:
        return self in get_args(SUPPORTED_EVM_CHAINS)

    def is_bitcoin(self) -> bool:
        return self in get_args(SUPPORTED_BITCOIN_CHAINS)

    def is_substrate(self) -> bool:
        return self in get_args(SUPPORTED_SUBSTRATE_CHAINS)

    def get_native_token_id(self) -> str:
        """Returns the string identifier of the native token for the chain"""
        if self == SupportedBlockchain.OPTIMISM:
            return 'ETH'
        if self == SupportedBlockchain.POLYGON_POS:
            return 'eip155:137/erc20:0x0000000000000000000000000000000000001010'

        return self.value

    def get_chain_type(self) -> str:
        """Chain type to return to the API supported chains endpoint"""
        if self.is_evm():
            return 'evm'
        if self.is_substrate():
            return 'substrate'
        if self.is_bitcoin():
            return 'bitcoin'
        # else
        return 'eth2'  # the outlier

    def ens_coin_type(self) -> int:
        """Return the CoinType number according to EIP-2304, multichain address
        resolution for ENS domains.

        https://eips.ethereum.org/EIPS/eip-2304
        """
        if self == SupportedBlockchain.ETHEREUM:
            return 60
        if self == SupportedBlockchain.BITCOIN:
            return 0
        if self == SupportedBlockchain.BITCOIN_CASH:
            return 145
        if self == SupportedBlockchain.KUSAMA:
            return 434
        if self == SupportedBlockchain.POLKADOT:
            return 354
        if self == SupportedBlockchain.AVALANCHE:
            return 9000
        raise AssertionError(f'Invalid SupportedBlockchain value: {self}')

    def to_chain_id(self) -> ChainID:
        return SUPPORTED_BLOCKCHAIN_TO_CHAINID[self]

    def to_range_prefix(self, range_type: Literal['txs', 'internaltxs', 'tokentxs']) -> str:
        """Provide the appropriate range prefix for the DB for this chain"""
        return f'{self.value}{range_type}'


SUPPORTED_BLOCKCHAIN_NAMES_MAPPING = {
    SupportedBlockchain.ETHEREUM_BEACONCHAIN: 'Ethereum Staking',
    SupportedBlockchain.POLYGON_POS: 'Polygon PoS',
}

EVM_CHAINS_WITH_TRANSACTIONS_TYPE = Literal[
    SupportedBlockchain.ETHEREUM,
    SupportedBlockchain.OPTIMISM,
    SupportedBlockchain.POLYGON_POS,
]

EVM_CHAINS_WITH_TRANSACTIONS: tuple[EVM_CHAINS_WITH_TRANSACTIONS_TYPE, ...] = typing.get_args(EVM_CHAINS_WITH_TRANSACTIONS_TYPE)  # noqa: E501

EVM_CHAIN_IDS_WITH_TRANSACTIONS_TYPE = Literal[
    ChainID.ETHEREUM,
    ChainID.OPTIMISM,
    ChainID.POLYGON_POS,
]

EVM_CHAIN_IDS_WITH_TRANSACTIONS: tuple[EVM_CHAIN_IDS_WITH_TRANSACTIONS_TYPE, ...] = typing.get_args(EVM_CHAIN_IDS_WITH_TRANSACTIONS_TYPE)  # noqa: E501

SUPPORTED_EVM_CHAINS = Literal[
    SupportedBlockchain.ETHEREUM,
    SupportedBlockchain.OPTIMISM,
    SupportedBlockchain.AVALANCHE,
    SupportedBlockchain.POLYGON_POS,
]

SUPPORTED_NON_BITCOIN_CHAINS = Literal[
    SupportedBlockchain.ETHEREUM,
    SupportedBlockchain.ETHEREUM_BEACONCHAIN,
    SupportedBlockchain.KUSAMA,
    SupportedBlockchain.AVALANCHE,
    SupportedBlockchain.POLKADOT,
    SupportedBlockchain.OPTIMISM,
    SupportedBlockchain.POLYGON_POS,
]

SUPPORTED_BITCOIN_CHAINS = Literal[
    SupportedBlockchain.BITCOIN,
    SupportedBlockchain.BITCOIN_CASH,
]

SUPPORTED_SUBSTRATE_CHAINS = Literal[
    SupportedBlockchain.POLKADOT,
    SupportedBlockchain.KUSAMA,
]

SUPPORTED_BLOCKCHAIN_TO_CHAINID = {
    SupportedBlockchain.ETHEREUM: ChainID.ETHEREUM,
    SupportedBlockchain.OPTIMISM: ChainID.OPTIMISM,
    SupportedBlockchain.AVALANCHE: ChainID.AVALANCHE,
    SupportedBlockchain.POLYGON_POS: ChainID.POLYGON_POS,
}
CHAINID_TO_SUPPORTED_BLOCKCHAIN = {
    value: key
    for key, value in SUPPORTED_BLOCKCHAIN_TO_CHAINID.items()
}
NON_EVM_CHAINS = set(SupportedBlockchain) - set(SUPPORTED_BLOCKCHAIN_TO_CHAINID.keys())

CHAINS_WITH_CHAIN_MANAGER = Literal[
    SupportedBlockchain.ETHEREUM,
    SupportedBlockchain.OPTIMISM,
    SupportedBlockchain.POLYGON_POS,
    SupportedBlockchain.AVALANCHE,
    SupportedBlockchain.POLKADOT,
    SupportedBlockchain.KUSAMA,
]


class TradeType(DBCharEnumMixIn):
    BUY = 1
    SELL = 2
    SETTLEMENT_BUY = 3
    SETTLEMENT_SELL = 4

    @classmethod
    def deserialize(cls: type['TradeType'], symbol: str) -> 'TradeType':
        """Overriding deserialize here since it can have different wordings for the same type
        so the automatic deserialization does not work
        """
        if not isinstance(symbol, str):
            raise DeserializationError(
                f'Failed to deserialize trade type symbol from {type(symbol)} entry',
            )

        if symbol in ('buy', 'LIMIT_BUY', 'BUY', 'Buy'):
            return TradeType.BUY
        if symbol in ('sell', 'LIMIT_SELL', 'SELL', 'Sell'):
            return TradeType.SELL
        if symbol in ('settlement_buy', 'settlement buy'):
            return TradeType.SETTLEMENT_BUY
        if symbol in ('settlement_sell', 'settlement sell'):
            return TradeType.SETTLEMENT_SELL

        # else
        raise DeserializationError(
            f'Failed to deserialize trade type symbol. Unknown symbol {symbol} for trade type',
        )


class Location(DBCharEnumMixIn):
    """Supported Locations"""
    EXTERNAL = 1
    KRAKEN = 2
    POLONIEX = 3
    BITTREX = 4
    BINANCE = 5
    BITMEX = 6
    COINBASE = 7
    TOTAL = 8
    BANKS = 9
    BLOCKCHAIN = 10
    COINBASEPRO = 11
    GEMINI = 12
    EQUITIES = 13
    REALESTATE = 14
    COMMODITIES = 15
    CRYPTOCOM = 16
    UNISWAP = 17
    BITSTAMP = 18
    BINANCEUS = 19
    BITFINEX = 20
    BITCOINDE = 21
    ICONOMI = 22
    KUCOIN = 23
    BALANCER = 24
    LOOPRING = 25
    FTX = 26  # FTX is dead but we keep the location for historical reasons
    NEXO = 27
    BLOCKFI = 28
    INDEPENDENTRESERVE = 29
    GITCOIN = 30
    SUSHISWAP = 31
    SHAPESHIFT = 32
    UPHOLD = 33
    BITPANDA = 34
    BISQ = 35
    FTXUS = 36
    OKX = 37
    ETHEREUM = 38  # on-chain ethereum events
    OPTIMISM = 39  # on-chain optimism events
    POLYGON_POS = 40  # on-chain Polygon POS events

    @staticmethod
    def from_chain_id(chain_id: EVM_CHAIN_IDS_WITH_TRANSACTIONS_TYPE) -> 'Location':
        if chain_id == ChainID.ETHEREUM:
            return Location.ETHEREUM

        if chain_id == ChainID.OPTIMISM:
            return Location.OPTIMISM
        # else
        return Location.POLYGON_POS

    def to_chain_id(self) -> int:
        """EVMLocation to chain id

        Dealing directly with ints since it's used as integers mostly and helps with import hell
        """
        assert self in EVM_LOCATIONS
        if self == Location.ETHEREUM:
            return 1
        if self == Location.OPTIMISM:
            return 10
        assert self == Location.POLYGON_POS, 'should have only been polygon pos here'
        return 137


EVM_LOCATIONS_TYPE_ = Literal[Location.ETHEREUM, Location.OPTIMISM, Location.POLYGON_POS]
EVM_LOCATIONS: tuple[EVM_LOCATIONS_TYPE_, ...] = typing.get_args(EVM_LOCATIONS_TYPE_)


class LocationDetails(NamedTuple):
    """Information about Location enum values to display them to the user"""
    label: Optional[str] = None
    icon: Optional[str] = None
    image: Optional[str] = None

    def serialize(self) -> dict[str, str]:
        data = {}
        if self.label is not None:
            data = {'label': self.label}

        if self.icon is not None:
            return data | {'icon': self.icon}
        if self.image is not None:
            return data | {'image': self.image}

        raise InputError('Location details has neither an icon nor an image')


class AssetMovementCategory(DBCharEnumMixIn):
    """Supported Asset Movement Types so far only deposit and withdrawals"""
    DEPOSIT = 1
    WITHDRAWAL = 2


class ExchangeAuthCredentials(NamedTuple):
    """
    Data structure that is used for editing credentials of exchanges.
    If a certain field is not None, it is modified in the exchange, otherwise
    the current value is kept.
    """
    api_key: Optional[ApiKey]
    api_secret: Optional[ApiSecret]
    passphrase: Optional[str]


class ExchangeApiCredentials(NamedTuple):
    """Represents Credentials for Exchanges

    The Api in question must at least have an API key and an API secret.
    """
    name: str  # A unique name to identify this particular Location credentials
    location: Location
    api_key: ApiKey
    api_secret: ApiSecret
    passphrase: Optional[str] = None


EXTERNAL_EXCHANGES = (
    Location.CRYPTOCOM,
    Location.BLOCKFI,
    Location.NEXO,
    Location.SHAPESHIFT,
    Location.UPHOLD,
    Location.BISQ,
)


class ExchangeLocationID(NamedTuple):
    name: str
    location: Location

    def serialize(self) -> dict:
        return {'name': self.name, 'location': self.location.serialize()}

    @classmethod
    def deserialize(
            cls: type['ExchangeLocationID'],
            data: dict['str', Any],
    ) -> 'ExchangeLocationID':
        """May raise DeserializationError"""
        try:
            return cls(
                name=data['name'],
                location=Location.deserialize(data['location']),
            )
        except KeyError as e:
            raise DeserializationError(f'Missing key {e!s}') from e


class EnsMapping(NamedTuple):
    address: ChecksumEvmAddress
    name: str
    last_update: Timestamp = Timestamp(0)


class CostBasisMethod(SerializableEnumNameMixin):
    FIFO = auto()
    LIFO = auto()
    HIFO = auto()
    ACB = auto()


class AddressbookEntry(NamedTuple):
    address: ChecksumEvmAddress
    name: str
    blockchain: Optional[SupportedBlockchain]

    def serialize(self) -> dict[str, Optional[str]]:
        return {
            'address': self.address,
            'name': self.name,
            'blockchain': self.blockchain.serialize() if self.blockchain is not None else None,
        }

    def serialize_for_db(self) -> tuple[str, str, Optional[str]]:
        blockchain = self.blockchain.value if self.blockchain is not None else None
        return (self.address, self.name, blockchain)

    @classmethod
    def deserialize(cls: type['AddressbookEntry'], data: dict[str, Any]) -> 'AddressbookEntry':
        """May raise:
        -KeyError if required keys are missing
        """
        return cls(
            address=data['address'],
            name=data['name'],
            blockchain=SupportedBlockchain.deserialize(data['blockchain']) if data['blockchain'] is not None else None,  # noqa: E501
        )

    def __str__(self) -> str:
        return f'Addressbook entry with name "{self.name}", address "{self.address}" and blockchain {str(self.blockchain) if self.blockchain is not None else None}'  # noqa: E501


class OptionalChainAddress(NamedTuple):
    address: ChecksumAddress
    blockchain: Optional[SupportedBlockchain]


class ChainAddress(OptionalChainAddress):
    blockchain: SupportedBlockchain


class AddressbookType(SerializableEnumNameMixin):
    GLOBAL = 1
    PRIVATE = 2


class UserNote(NamedTuple):
    identifier: int
    title: str
    content: str
    location: str
    last_update_timestamp: Timestamp
    is_pinned: bool

    def serialize(self) -> dict[str, Union[str, int]]:
        """Serialize a `UserNote` object into a dict."""
        return {
            'identifier': self.identifier,
            'title': self.title,
            'content': self.content,
            'location': self.location,
            'last_update_timestamp': self.last_update_timestamp,
            'is_pinned': self.is_pinned,
        }

    @classmethod
    def deserialize(cls, entry: dict[str, Any]) -> 'UserNote':
        """Turns a dict into a `UserNote` object.
        May raise:
        - DeserializationError if required keys are missing.
        """
        try:
            return cls(
                identifier=entry['identifier'],
                title=entry['title'],
                content=entry['content'],
                location=entry['location'],
                last_update_timestamp=entry['last_update_timestamp'],
                is_pinned=entry['is_pinned'],
            )
        except KeyError as e:
            raise DeserializationError(f'Failed to deserialize dict due to missing key: {e!s}') from e  # noqa: E501

    @classmethod
    def deserialize_from_db(cls, entry: tuple[int, str, str, str, int, int]) -> 'UserNote':
        """Turns a `user_note` db entry into a `UserNote` object."""
        return cls(
            identifier=entry[0],
            title=entry[1],
            content=entry[2],
            location=entry[3],
            last_update_timestamp=Timestamp(entry[4]),
            is_pinned=bool(entry[5]),
        )


class EvmTokenKind(DBCharEnumMixIn):
    ERC20 = auto()
    ERC721 = auto()
    UNKNOWN = auto()


class GeneralCacheType(Enum):
    CURVE_LP_TOKENS = auto()
    CURVE_POOL_ADDRESS = auto()  # get pool addr by lp token
    CURVE_POOL_TOKENS = auto()  # get pool tokens by pool addr
    YEARN_VAULTS = auto()  # get yearn vaults information
    MAKERDAO_VAULT_ILK = auto()  # ilk(collateral type) to info (underlying_asset, join address)
    CURVE_GAUGE_ADDRESS = auto()  # get gauge address by pool address
    CURVE_POOL_UNDERLYING_TOKENS = auto()  # get underlying tokens by pool address

    def serialize(self) -> str:
        # Using custom serialize method instead of SerializableEnumMixin since mixin replaces
        # `_` with ` ` and we don't need spaces here
        return self.name


class OracleSource(SerializableEnumNameMixin):
    """
    Abstraction to represent a variable that could be either HistoricalPriceOracle
    or CurrentPriceOracle. Can't have any member since you can't override them later
    """


AddressNameSource = Literal[
    'blockchain_account',
    'ens_names',
    'ethereum_tokens',
    'global_addressbook',
    'hardcoded_mappings',
    'private_addressbook',
]

DEFAULT_ADDRESS_NAME_PRIORITY: Sequence[AddressNameSource] = (
    'private_addressbook',
    'blockchain_account',
    'global_addressbook',
    'ethereum_tokens',
    'hardcoded_mappings',
    'ens_names',
)

EventMappingType = dict[
    'HistoryEventType',
    dict['HistoryEventSubType', 'EventCategory'],
]
LocationEventMappingType = dict[Location, EventMappingType]
DecoderEventMappingType = dict[str, EventMappingType]


class HistoryEventQueryType(SerializableEnumNameMixin):
    """Locations to query for history events"""
    ETH_WITHDRAWALS = auto()
    BLOCK_PRODUCTIONS = auto()
    EXCHANGES = auto()
