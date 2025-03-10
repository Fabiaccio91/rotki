<script setup lang="ts">
import { LedgerActionType } from '@/types/history/ledger-action/ledger-actions-type';

const defaultTaxable: () => TaxableState = () => {
  const status: any = {};
  for (const action of Object.values(LedgerActionType)) {
    status[action] = false;
  }

  return status as TaxableState;
};

type TaxableState = { [key in LedgerActionType]: boolean };

const taxable = ref<TaxableState>(defaultTaxable());

const { ledgerActionsData } = useLedgerActionData();

const changed = async (update: (value: any) => void) => {
  const taxableActions: LedgerActionType[] = [];
  for (const actionType in get(taxable)) {
    if (get(taxable)[actionType as LedgerActionType]) {
      taxableActions.push(actionType as LedgerActionType);
    }
  }

  update(taxableActions);
};

const { taxableLedgerActions } = storeToRefs(useAccountingSettingsStore());

onMounted(() => {
  for (const taxableAction of get(taxableLedgerActions)) {
    taxable.value[taxableAction] = true;
  }
});

const { t } = useI18n();
</script>

<template>
  <setting-category>
    <template #title>{{ t('ledger_action_settings.title') }}</template>
    <template #subtitle>
      {{ t('ledger_action_settings.subtitle') }}
    </template>
    <settings-option
      #default="{ error, success, update }"
      setting="taxableLedgerActions"
    >
      <v-sheet outlined rounded>
        <v-simple-table dense>
          <thead>
            <tr>
              <th>{{ t('ledger_action_settings.header.ledger_action') }}</th>
              <th>{{ t('ledger_action_settings.header.taxable') }}</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="entry in ledgerActionsData" :key="entry.identifier">
              <td>{{ entry.label }}</td>
              <td>
                <v-checkbox
                  v-model="taxable[entry.identifier]"
                  hide-details
                  class="my-2 pt-0"
                  @change="changed(update)"
                />
              </td>
            </tr>
          </tbody>
        </v-simple-table>
      </v-sheet>
      <action-status-indicator class="mt-4" :status="{ error, success }" />
    </settings-option>
  </setting-category>
</template>
