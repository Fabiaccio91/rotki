<script setup lang="ts">
import { Blockchain } from '@rotki/common/lib/blockchain';
import { Module } from '@/types/modules';

const props = withDefaults(
  defineProps<{
    modelValue?: Blockchain | null;
    disabled?: boolean;
    dense?: boolean;
    evmOnly?: boolean;
  }>(),
  {
    modelValue: null,
    disabled: false,
    dense: false,
    evmOnly: false
  }
);

const rootAttrs = useAttrs();

const emit = defineEmits<{
  (e: 'update:model-value', blockchain: Blockchain | null): void;
}>();

const { evmOnly, modelValue } = toRefs(props);

const { isModuleEnabled } = useModules();

const { isEvm, supportedChains } = useSupportedChains();

const { t } = useI18n();

const search = ref<string | null>(null);

const items = computed(() => {
  const isEth2Enabled = get(isModuleEnabled(Module.ETH2));

  let data: string[] = get(supportedChains).map(({ id }) => id);

  if (!isEth2Enabled) {
    data = data.filter(symbol => symbol !== Blockchain.ETH2);
  }

  if (get(evmOnly)) {
    data = data.filter(symbol => get(isEvm(symbol as Blockchain)));
  }

  return data;
});

const clearSearch = () => {
  set(search, '');
};

const updateBlockchain = (blockchain: Blockchain) => {
  clearSearch();
  emit('update:model-value', blockchain);
};

const filter = (chain: Blockchain, queryText: string) => {
  const item = get(supportedChains).find(blockchain => blockchain.id === chain);
  if (!item) {
    return false;
  }

  const nameIncludes = item.name
    .toLocaleLowerCase()
    .includes(queryText.toLocaleLowerCase());

  const idIncludes = item.id
    .toLocaleLowerCase()
    .includes(queryText.toLocaleLowerCase());

  return nameIncludes || idIncludes;
};
</script>

<template>
  <v-autocomplete
    :dense="dense"
    :disabled="disabled"
    :filter="filter"
    :items="items"
    :label="t('account_form.labels.blockchain')"
    :search-input.sync="search"
    :value="modelValue"
    class="account-form__chain"
    clearable
    data-cy="account-blockchain-field"
    outlined
    single-line
    v-bind="rootAttrs"
    @change="updateBlockchain($event)"
    @blur="clearSearch()"
  >
    <template #selection="{ item }">
      <chain-display
        v-if="!search"
        :chain="item"
        :dense="dense"
        :full-width="false"
      />
    </template>
    <template #item="{ item }">
      <chain-display :chain="item" />
    </template>
  </v-autocomplete>
</template>
