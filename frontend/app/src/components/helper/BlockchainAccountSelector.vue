<script setup lang="ts">
import uniqBy from 'lodash/uniqBy';
import { type GeneralAccount } from '@rotki/common/lib/account';
import {
  Blockchain,
  type BlockchainSelection
} from '@rotki/common/lib/blockchain';
import { type ComputedRef } from 'vue';

type AccountWithChain = GeneralAccount<BlockchainSelection>;

const props = withDefaults(
  defineProps<{
    label?: string;
    hint?: boolean;
    loading?: boolean;
    usableAddresses?: string[];
    multiple?: boolean;
    value: AccountWithChain[];
    chains: Blockchain[];
    outlined?: boolean;
    dense?: boolean;
    noPadding?: boolean;
    hideOnEmptyUsable?: boolean;
    multichain?: boolean;
    unique?: boolean;
    hideChainIcon?: boolean;
  }>(),
  {
    label: '',
    hint: false,
    loading: false,
    usableAddresses: () => [],
    multiple: false,
    chains: () => [],
    outlined: false,
    dense: false,
    noPadding: false,
    hideOnEmptyUsable: false,
    multichain: false,
    unique: false,
    hideChainIcon: false
  }
);

const emit = defineEmits<{
  (e: 'input', value: AccountWithChain[]): void;
}>();

const {
  chains,
  value,
  usableAddresses,
  hideOnEmptyUsable,
  multiple,
  multichain,
  unique
} = toRefs(props);

const search = ref('');
const { t } = useI18n();

const { accounts } = useAccountBalances();

const internalValue = computed(() => {
  const accounts = get(value);
  if (get(multiple)) {
    return accounts;
  }

  if (!accounts) {
    return null;
  }
  if (accounts.length === 1) {
    return accounts[0];
  }
});

const selectableAccounts: ComputedRef<AccountWithChain[]> = computed(() => {
  const filteredChains = get(chains);
  const blockchainAccounts: AccountWithChain[] = get(unique)
    ? uniqBy(get(accounts), 'address')
    : get(accounts);

  const filteredAccounts =
    filteredChains.length === 0
      ? blockchainAccounts
      : blockchainAccounts.filter(
          ({ chain }) => chain === 'ALL' || filteredChains.includes(chain)
        );

  if (get(multichain)) {
    const entries: Record<string, number> = {};
    filteredAccounts.forEach(account => {
      if (entries[account.address]) {
        entries[account.address] += 1;
      } else {
        entries[account.address] = 1;
      }
    });

    for (const address in entries) {
      const count = entries[address];
      if (count > 1) {
        filteredAccounts.push({
          address,
          label: '',
          tags: [],
          chain: 'ALL'
        });
      }
    }
  }

  return filteredAccounts;
});

const hintText = computed(() => {
  const all = t('blockchain_account_selector.all').toString();
  const selection = get(value);
  if (Array.isArray(selection)) {
    return selection.length > 0 ? selection.length.toString() : all;
  }
  return selection ? '1' : all;
});

const displayedAccounts: ComputedRef<AccountWithChain[]> = computed(() => {
  const addresses = get(usableAddresses);
  const accounts = get(selectableAccounts);
  if (addresses.length > 0) {
    return accounts.filter(({ address }) => addresses.includes(address));
  }
  return get(hideOnEmptyUsable) ? [] : accounts;
});

const { addressNameSelector } = useAddressesNamesStore();

const filter = (item: AccountWithChain, queryText: string) => {
  const chain = item.chain === 'ALL' ? Blockchain.ETH : item.chain;
  const text = (
    get(addressNameSelector(item.address, chain)) ?? ''
  ).toLowerCase();
  const address = item.address.toLocaleLowerCase();
  const query = queryText.toLocaleLowerCase();

  const labelMatches = text.includes(query);
  const addressMatches = address.includes(query);

  const tagMatches = item.tags
    .map(tag => tag.toLocaleLowerCase())
    .join(' ')
    .includes(query);

  return labelMatches || tagMatches || addressMatches;
};

function filterOutElements(
  lastElement: GeneralAccount<BlockchainSelection>,
  nextValue: AccountWithChain[]
): AccountWithChain[] {
  if (lastElement.chain === 'ALL') {
    return nextValue.filter(
      x => x.address !== lastElement.address || x.chain === 'ALL'
    );
  }
  return nextValue.filter(
    x => x.address !== lastElement.address || x.chain !== 'ALL'
  );
}

const input = (nextValue: null | AccountWithChain | AccountWithChain[]) => {
  const previousValue = get(value);
  let result: AccountWithChain[];
  if (Array.isArray(nextValue)) {
    const lastElement = nextValue[nextValue.length - 1];
    if (lastElement && nextValue.length > previousValue.length) {
      result = filterOutElements(lastElement, nextValue);
    } else {
      result = nextValue;
    }
  } else {
    result = nextValue ? [nextValue] : [];
  }

  emit('input', result);
};

const { dark } = useTheme();

const getItemKey = (item: AccountWithChain) => item.address + item.chain;
</script>

<template>
  <v-card v-bind="$attrs">
    <div :class="noPadding ? null : 'mx-4 pt-2'">
      <v-autocomplete
        :value="internalValue"
        :items="displayedAccounts"
        :filter="filter"
        auto-select-first
        :search-input.sync="search"
        :multiple="multiple"
        :loading="loading"
        :disabled="loading"
        hide-details
        hide-selected
        :hide-no-data="!hideOnEmptyUsable"
        return-object
        chips
        single-line
        clearable
        :dense="dense"
        :outlined="outlined"
        :item-text="getItemKey"
        :open-on-clear="false"
        :label="label ? label : t('blockchain_account_selector.default_label')"
        :class="outlined ? 'blockchain-account-selector--outlined' : null"
        class="blockchain-account-selector"
        @input="input($event)"
      >
        <template #no-data>
          <span class="text-caption px-2">
            {{ t('blockchain_account_selector.no_data') }}
          </span>
        </template>
        <template #selection="data">
          <v-chip
            v-if="multiple"
            :key="data.item.chain + data.item.address"
            v-bind="data.attrs"
            :input-value="data.selected"
            :click="data.select"
            filter
            close
            close-label="overflow-x-hidden"
            @click:close="data.parent.selectItem(data.item)"
          >
            <account-display
              :account="data.item"
              :hide-chain-icon="hideChainIcon"
            />
          </v-chip>
          <div v-else class="overflow-x-hidden">
            <account-display
              :account="data.item"
              :hide-chain-icon="hideChainIcon"
              class="pr-2"
            />
          </div>
        </template>
        <template #item="data">
          <div
            class="blockchain-account-selector__list__item d-flex align-center justify-space-between flex-grow-1"
          >
            <div class="blockchain-account-selector__list__item__address-label">
              <v-chip
                :color="dark ? null : 'grey lighten-3'"
                filter
                class="text-truncate"
              >
                <account-display
                  :account="data.item"
                  :hide-chain-icon="hideChainIcon"
                />
              </v-chip>
            </div>
            <tag-display class="mb-1" :tags="data.item.tags" :small="true" />
          </div>
        </template>
      </v-autocomplete>
    </div>
    <v-card-text v-if="hint">
      {{ t('blockchain_account_selector.hint', { hintText }) }}
      <slot />
    </v-card-text>
  </v-card>
</template>

<style scoped lang="scss">
.blockchain-account-selector {
  &__list {
    &__item {
      max-width: 100%;
    }
  }

  /* stylelint-disable selector-class-pattern,selector-nested-pattern */

  :deep(.v-select__selections) {
    padding: 2px;

    .v-chip {
      margin: 2px;
    }

    input {
      min-width: 0;
    }
  }

  /* stylelint-enable selector-class-pattern,selector-nested-pattern */
}
</style>
