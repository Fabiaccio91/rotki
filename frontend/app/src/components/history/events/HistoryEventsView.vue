<script setup lang="ts">
import { type Account, type GeneralAccount } from '@rotki/common/lib/account';
import {
  type Blockchain,
  type BlockchainSelection
} from '@rotki/common/lib/blockchain';
import isEqual from 'lodash/isEqual';
import { type ComputedRef, type Ref } from 'vue';
import { not } from '@vueuse/math';
import { type HistoryEventEntryType } from '@rotki/common/lib/history/events';
import { type DataTableHeader } from '@/types/vuetify';
import { type Collection } from '@/types/collection';
import { SavedFilterLocation } from '@/types/filtering';
import { IgnoreActionType } from '@/types/history/ignored';
import {
  type EvmChainAndTxHash,
  type EvmHistoryEvent,
  type HistoryEvent,
  type HistoryEventEntry,
  type HistoryEventRequestPayload
} from '@/types/history/events';
import { RouterAccountsSchema } from '@/types/route';
import { Section } from '@/types/status';
import { TaskType } from '@/types/task-type';
import { type Writeable } from '@/types';
import HistoryEventsAction from '@/components/history/events/HistoryEventsAction.vue';
import type { Filters, Matcher } from '@/composables/filters/events';

const { t } = useI18n();

const props = withDefaults(
  defineProps<{
    location?: string;
    protocols?: string[];
    eventTypes?: string[];
    eventSubTypes?: string[];
    entryTypes?: HistoryEventEntryType[];
    period?: { fromTimestamp?: string; toTimestamp?: string };
    validators?: number[];
    externalAccountFilter?: Account[];
    useExternalAccountFilter?: boolean;
    sectionTitle?: string;
    mainPage?: boolean;
    onlyChains?: Blockchain[];
  }>(),
  {
    location: undefined,
    protocols: () => [],
    eventTypes: () => [],
    eventSubTypes: () => [],
    entryTypes: undefined,
    period: undefined,
    validators: undefined,
    externalAccountFilter: () => [],
    useExternalAccountFilter: false,
    sectionTitle: '',
    mainPage: false,
    onlyChains: () => []
  }
);

const {
  location,
  protocols,
  entryTypes,
  period,
  validators,
  useExternalAccountFilter,
  externalAccountFilter,
  sectionTitle,
  eventTypes,
  eventSubTypes,
  mainPage,
  onlyChains
} = toRefs(props);

const editableItem: Ref<EvmHistoryEvent | null> = ref(null);
const selectedTransaction: Ref<EvmHistoryEvent | null> = ref(null);
const eventToDelete: Ref<HistoryEventEntry | null> = ref(null);
const transactionToIgnore: Ref<HistoryEventEntry | null> = ref(null);
const accounts: Ref<GeneralAccount[]> = ref([]);
const locationOverview = ref(get(location));

const usedTitle: ComputedRef<string> = computed(
  () => get(sectionTitle) || t('transactions.title')
);

const usedAccounts: ComputedRef<Account<BlockchainSelection>[]> = computed(
  () => {
    if (get(useExternalAccountFilter)) {
      return get(externalAccountFilter);
    }
    const accountsVal = get(accounts);
    return accountsVal.length > 0 ? [accountsVal[0]] : accountsVal;
  }
);

const tableHeaders = computed<DataTableHeader[]>(() => [
  {
    text: '',
    value: 'ignoredInAccounting',
    sortable: false,
    class: 'pa-0',
    cellClass: 'pa-0',
    width: '0px'
  },
  {
    text: t('transactions.events.headers.event_identifier'),
    value: 'txHash',
    sortable: false,
    width: '60%'
  },
  {
    text: t('common.datetime'),
    value: 'timestamp',
    cellClass: 'text-no-wrap',
    align: 'end'
  },
  {
    text: '',
    value: 'action',
    width: '20px',
    align: 'end',
    sortable: false
  }
]);

const { isTaskRunning } = useTaskStore();
const { txEvmChains, getEvmChainName } = useSupportedChains();
const txChains = useArrayMap(txEvmChains, x => x.id);

const { fetchHistoryEvents } = useHistoryEvents();

const { refreshTransactions, fetchTransactionEvents, deleteTransactionEvent } =
  useHistoryTransactions();

const {
  options,
  selected,
  isLoading: isEventsGroupHeaderLoading,
  userAction,
  state: eventsHeader,
  filters,
  matchers,
  setPage,
  setOptions,
  setFilter,
  updateFilter,
  fetchData
} = usePaginationFilters<
  HistoryEvent,
  HistoryEventRequestPayload,
  HistoryEventEntry,
  Collection<HistoryEventEntry>,
  Filters,
  Matcher
>(
  null,
  mainPage,
  () =>
    useHistoryEventFilter(
      {
        protocols: get(protocols).length > 0,
        locations: !!get(location),
        period: !!get(period),
        validators: !!get(validators)
      },
      entryTypes
    ),
  fetchHistoryEvents,
  {
    onUpdateFilters(query) {
      const parsedAccounts = RouterAccountsSchema.parse(query);
      const accountsParsed = parsedAccounts.accounts;
      if (!accountsParsed) {
        set(accounts, []);
      } else {
        set(accounts, accountsParsed.length > 0 ? [accountsParsed[0]] : []);
      }
    },
    extraParams: computed(() => ({
      accounts: get(usedAccounts).map(
        account => `${account.address}#${account.chain}`
      )
    })),
    defaultParams: computed<Partial<HistoryEventRequestPayload> | undefined>(
      () => {
        if (isDefined(entryTypes)) {
          return {
            entryTypes: {
              values: get(entryTypes)
            }
          };
        }
        return undefined;
      }
    ),
    customPageParams: computed<Partial<HistoryEventRequestPayload>>(() => {
      const params: Writeable<Partial<HistoryEventRequestPayload>> = {
        counterparties: get(protocols),
        eventTypes: get(eventTypes),
        eventSubtypes: get(eventSubTypes),
        groupByEventIds: true
      };

      const accounts = get(usedAccounts);

      if (isDefined(get(locationOverview))) {
        params.location = toSnakeCase(get(locationOverview));
      }

      if (accounts.length > 0) {
        params.locationLabels = accounts.map(({ address }) => address);
      }

      if (isDefined(period)) {
        const { fromTimestamp, toTimestamp } = get(period);
        params.fromTimestamp = fromTimestamp;
        params.toTimestamp = toTimestamp;
      }

      if (isDefined(validators)) {
        params.validatorIndices = get(validators).map(v => v.toString());
      }

      return params;
    })
  }
);

const { data } = getCollectionData<HistoryEventEntry>(eventsHeader);

const isEventsLoading: Ref<boolean> = ref(false);

const allEvents: Ref<HistoryEventEntry[]> = asyncComputed(
  async () => {
    const eventsHeaderData = get(data);

    if (eventsHeaderData.length === 0) {
      return [];
    }

    const response = await fetchHistoryEvents({
      limit: -1,
      offset: 0,
      eventIdentifiers: eventsHeaderData.map(item => item.eventIdentifier),
      groupByEventIds: false
    });

    return response.data;
  },
  [],
  {
    lazy: true,
    evaluating: isEventsLoading
  }
);

const onFilterAccountsChanged = (acc: Account<BlockchainSelection>[]) => {
  set(userAction, true);
  set(accounts, acc.length > 0 ? [acc[0]] : []);
};

const redecodeAllEvmEvents = () => {
  show(
    {
      title: t('transactions.redecode_events.title'),
      message: t('transactions.redecode_events.confirmation')
    },
    () => redecodeAllEvmEventsHandler()
  );
};

const redecodeAllEvmEventsHandler = async () => {
  const chains = get(onlyChains);
  const evmChains: { evmChain: string }[] = [];

  if (chains.length > 0) {
    chains.forEach(item => {
      const evmChain = getEvmChainName(item);
      if (evmChain) {
        evmChains.push({ evmChain });
      }
    });
  }

  await fetchTransactionEvents(chains.length === 0 ? null : evmChains, true);
};

const forceRedecodeEvmEvents = async (data: EvmChainAndTxHash) => {
  await fetchTransactionEvents([data], true);
};

const resetEventsHandler = async (data: EvmHistoryEvent) => {
  const eventIds = get(allEvents)
    .filter(
      event =>
        isEvmEvent(event) && event.txHash === data.txHash && event.customized
    )
    .map(event => event.identifier);

  if (eventIds.length > 0) {
    await deleteTransactionEvent(eventIds, true);
  }

  await forceRedecodeEvmEvents(toEvmChainAndTxHash(data));
  await fetchData();
};

const resetEvents = (data: EvmHistoryEvent) => {
  show(
    {
      title: t('transactions.events.confirmation.reset.title'),
      message: t('transactions.events.confirmation.reset.message')
    },
    () => resetEventsHandler(data)
  );
};

const { ignore } = useIgnore<HistoryEventEntry>(
  {
    actionType: IgnoreActionType.EVM_TRANSACTIONS,
    toData: (item: HistoryEventEntry) => toEvmChainAndTxHash(item)
  },
  selected,
  fetchData
);

const toggleIgnore = async (item: HistoryEventEntry) => {
  set(selected, [item]);
  await ignore(!item.ignoredInAccounting);
};

const { setOpenDialog, setPostSubmitFunc } = useHistoryEventsForm();

setPostSubmitFunc(() => {
  const tx = get(selectedTransaction);
  if (tx) {
    fetchDataAndRefreshEvents(toEvmChainAndTxHash(tx));
  }
});

const addEvent = (tx: EvmHistoryEvent) => {
  set(selectedTransaction, tx);
  set(editableItem, null);
  setOpenDialog(true);
};

const editEventHandler = (event: EvmHistoryEvent, tx: EvmHistoryEvent) => {
  set(selectedTransaction, tx);
  set(editableItem, event);
  setOpenDialog(true);
};

const promptForDelete = ({
  item,
  canDelete
}: {
  item: HistoryEventEntry;
  canDelete: boolean;
}) => {
  if (canDelete) {
    set(eventToDelete, item);
  } else {
    set(transactionToIgnore, item);
  }
  showDeleteConfirmation();
};

const deleteEventHandler = async () => {
  const txToIgnore = get(transactionToIgnore);
  if (txToIgnore) {
    set(selected, [txToIgnore]);
    await ignore(true);
  }

  const eventToDeleteVal = get(eventToDelete);
  const id = eventToDeleteVal?.identifier;

  if (eventToDeleteVal && id) {
    const { success } = await deleteTransactionEvent([id]);
    if (!success) {
      return;
    }
    await fetchDataAndRefreshEvents(toEvmChainAndTxHash(eventToDeleteVal));
  }

  set(eventToDelete, null);
  set(transactionToIgnore, null);
};

const getItemClass = (item: HistoryEventEntry) =>
  item.ignoredInAccounting ? 'darken-row' : '';

watch(
  [filters, usedAccounts],
  async ([filters, usedAccounts], [oldFilters, oldAccounts]) => {
    const filterChanged = !isEqual(filters, oldFilters);
    const accountsChanged = !isEqual(usedAccounts, oldAccounts);

    if (!(filterChanged || accountsChanged)) {
      return;
    }

    if (accountsChanged && usedAccounts.length > 0) {
      const updatedFilter = { ...get(filters) };
      updateFilter(updatedFilter);
    }

    if (filterChanged || accountsChanged) {
      set(locationOverview, filters.location);
      set(options, { ...get(options), page: 1 });
    }
  }
);

const premium = usePremium();
const { isLoading: isSectionLoading } = useStatusStore();
const sectionLoading = isSectionLoading(Section.TX);
const eventTaskLoading = isTaskRunning(TaskType.TX_EVENTS);
const onlineHistoryEventsLoading = isTaskRunning(TaskType.QUERY_ONLINE_EVENTS);

const { isAllFinished: isQueryingTxsFinished } = toRefs(
  useTxQueryStatusStore()
);
const { isAllFinished: isQueryingOnlineEventsFinished } = toRefs(
  useEventsQueryStatusStore()
);

const refreshing = logicOr(
  sectionLoading,
  eventTaskLoading,
  onlineHistoryEventsLoading
);

const querying = not(
  logicOr(isQueryingTxsFinished, isQueryingOnlineEventsFinished)
);

const shouldFetchEventsRegularly = logicOr(querying, refreshing);

const loading = refThrottled(
  logicOr(isEventsGroupHeaderLoading, isEventsLoading),
  300
);

const { fetchAssociatedLocations } = useHistoryStore();
const { pause, resume, isActive } = useIntervalFn(() => {
  fetchData();
  fetchAssociatedLocations();
}, 20000);

watch(shouldFetchEventsRegularly, shouldFetchEventsRegularly => {
  const active = get(isActive);
  if (shouldFetchEventsRegularly && !active) {
    resume();
  } else if (!shouldFetchEventsRegularly && active) {
    pause();
  }
});

const { show } = useConfirmStore();

const resetPendingDeletion = () => {
  set(eventToDelete, null);
  set(transactionToIgnore, null);
};

const showDeleteConfirmation = () => {
  show(
    get(transactionToIgnore)
      ? {
          title: t('transactions.events.confirmation.ignore.title'),
          message: t('transactions.events.confirmation.ignore.message'),
          primaryAction: t('transactions.events.confirmation.ignore.action')
        }
      : {
          title: t('transactions.events.confirmation.delete.title'),
          message: t('transactions.events.confirmation.delete.message'),
          primaryAction: t('common.actions.confirm')
        },
    deleteEventHandler,
    resetPendingDeletion
  );
};

onMounted(async () => {
  startPromise(Promise.all([fetchData(), fetchAssociatedLocations()]));
  await refresh();
});

const refresh = async (userInitiated = false) => {
  await refreshTransactions(get(onlyChains), userInitiated);
  await fetchData();
};

onUnmounted(() => {
  pause();
});

watch(eventTaskLoading, async (isLoading, wasLoading) => {
  if (!isLoading && wasLoading) {
    await fetchData();
  }
});

const {
  setOpenDialog: setTxFormOpenDialog,
  setPostSubmitFunc: setTxFormPostSubmitFunc
} = useHistoryTransactionsForm();

setTxFormPostSubmitFunc(payload => {
  if (payload) {
    fetchDataAndRefreshEvents(payload, true);
  }
});

const addTransactionHash = () => {
  setTxFormOpenDialog(true);
};

const fetchDataAndRefreshEvents = async (
  data: EvmChainAndTxHash,
  reDecodeEvents = false
) => {
  await fetchData();
  if (reDecodeEvents) {
    await forceRedecodeEvmEvents(data);
  }
};

const includeEvmEvents: ComputedRef<boolean> = useEmptyOrSome(
  entryTypes,
  type => isEvmEventType(type)
);

const includeOnlineEvents: ComputedRef<boolean> = useEmptyOrSome(
  entryTypes,
  type => isOnlineHistoryEventType(type)
);

const { locationData } = useLocations();
</script>

<template>
  <div>
    <card class="mt-8" outlined-body>
      <v-btn
        v-if="mainPage"
        absolute
        fab
        top
        right
        dark
        color="primary"
        data-cy="ledger-actions__add"
        @click="addTransactionHash()"
      >
        <v-icon>mdi-plus</v-icon>
      </v-btn>
      <template #title>
        <refresh-button
          :disabled="refreshing"
          :tooltip="t('transactions.refresh_tooltip')"
          @refresh="refresh(true)"
        />
        {{ usedTitle }}
      </template>
      <template #actions>
        <v-row>
          <v-col cols="12" md="5">
            <v-row>
              <v-col v-if="includeEvmEvents" cols="auto">
                <v-tooltip top>
                  <template #activator="{ on }">
                    <v-btn
                      color="primary"
                      depressed
                      height="40px"
                      small
                      :loading="eventTaskLoading"
                      :disabled="refreshing"
                      v-on="on"
                      @click="redecodeAllEvmEvents()"
                    >
                      <v-icon> mdi-select-compare </v-icon>
                    </v-btn>
                  </template>
                  <span>
                    {{ t('transactions.redecode_events.title') }}
                  </span>
                </v-tooltip>
              </v-col>
              <v-col v-if="!useExternalAccountFilter">
                <div>
                  <blockchain-account-selector
                    :value="accounts"
                    :chains="txChains"
                    dense
                    :label="t('transactions.filter.account')"
                    outlined
                    no-padding
                    multichain
                    hide-chain-icon
                    unique
                    flat
                    @input="onFilterAccountsChanged($event)"
                  />
                </div>
              </v-col>
            </v-row>
          </v-col>
          <v-col cols="12" md="7">
            <div>
              <table-filter
                :matches="filters"
                :matchers="matchers"
                :location="SavedFilterLocation.HISTORY_EVENTS"
                :disabled="!premium"
                @update:matches="setFilter($event)"
              >
                <template #tooltip>
                  <i18n tag="span" path="transactions.filtering_premium_hint">
                    <template #link>
                      <b>
                        <external-link url="https://rotki.com/products">
                          {{ t('common.website') }}
                        </external-link>
                      </b>
                    </template>
                  </i18n>
                </template>
              </table-filter>
            </div>
          </v-col>
        </v-row>
      </template>

      <collection-handler
        :collection="eventsHeader"
        @set-page="setPage($event)"
      >
        <template
          #default="{
            data: eventsData,
            itemLength,
            showUpgradeRow,
            limit,
            total
          }"
        >
          <data-table
            :expanded="eventsData"
            :headers="tableHeaders"
            :items="eventsData"
            :loading="loading"
            :options="options"
            :server-items-length="itemLength"
            :single-select="false"
            :item-class="getItemClass"
            :class="$style.table"
            @update:options="setOptions($event)"
          >
            <template #item.ignoredInAccounting="{ item, isMobile }">
              <div v-if="item.ignoredInAccounting" class="pl-4">
                <badge-display v-if="isMobile" color="grey">
                  <v-icon small> mdi-eye-off</v-icon>
                  <span class="ml-2">
                    {{ t('common.ignored_in_accounting') }}
                  </span>
                </badge-display>
                <v-tooltip v-else bottom>
                  <template #activator="{ on }">
                    <badge-display color="grey" v-on="on">
                      <v-icon small> mdi-eye-off</v-icon>
                    </badge-display>
                  </template>
                  <span>
                    {{ t('common.ignored_in_accounting') }}
                  </span>
                </v-tooltip>
              </div>
            </template>
            <template #item.txHash="{ item }">
              <v-lazy>
                <div class="d-flex align-center">
                  <div class="mr-2">
                    <location-icon
                      icon
                      no-padding
                      :item="locationData(item.location)"
                      size="20px"
                    />
                  </div>
                  <history-events-identifier :event="item" />
                </div>
              </v-lazy>
            </template>
            <template #item.timestamp="{ item }">
              <v-lazy>
                <date-display :timestamp="item.timestamp" />
              </v-lazy>
            </template>
            <template #item.action="{ item }">
              <v-lazy>
                <history-events-action
                  :event="item"
                  :loading="eventTaskLoading"
                  @add-event="addEvent($event)"
                  @toggle-ignore="toggleIgnore($event)"
                  @redecode="forceRedecodeEvmEvents($event)"
                  @reset="resetEvents($event)"
                />
              </v-lazy>
            </template>
            <template #expanded-item="{ headers, item }">
              <history-events-list
                :all-events="allEvents"
                :event-group-header="item"
                :colspan="headers.length"
                :loading="sectionLoading || eventTaskLoading"
                @edit:event="editEventHandler($event, item)"
                @delete:event="promptForDelete($event)"
              />
            </template>
            <template #body.prepend="{ headers }">
              <transaction-query-status
                v-if="includeEvmEvents"
                :only-chains="onlyChains"
                :colspan="headers.length"
              />
              <history-events-query-status
                v-if="includeOnlineEvents"
                :locations="filters.location ? [filters.location] : []"
                :colspan="headers.length"
              />
              <upgrade-row
                v-if="showUpgradeRow"
                :limit="limit"
                :total="total"
                :colspan="headers.length"
                :label="t('common.events')"
              />
            </template>
          </data-table>
        </template>
      </collection-handler>
    </card>

    <history-event-form-dialog
      :loading="sectionLoading"
      :editable-item="editableItem"
      :transaction="selectedTransaction"
    />

    <transaction-form-dialog :loading="sectionLoading" />
  </div>
</template>

<style module lang="scss">
.table {
  :global {
    .v-data-table {
      &__expanded {
        &__content {
          td {
            &:first-child {
              padding-left: 0 !important;
              padding-right: 0 !important;
            }
          }
        }
      }
    }
  }
}
</style>
