<script setup lang="ts">
const gasCosts = ref(false);
const { includeGasCosts } = storeToRefs(useAccountingSettingsStore());

onMounted(() => {
  set(gasCosts, get(includeGasCosts));
});

const { t } = useI18n();
</script>

<template>
  <settings-option
    #default="{ error, success, update }"
    setting="includeGasCosts"
    :error-message="t('account_settings.messages.gas_costs')"
  >
    <v-switch
      v-model="gasCosts"
      class="accounting-settings__include-gas-costs"
      :label="t('accounting_settings.labels.gas_costs')"
      :success-messages="success"
      :error-messages="error"
      color="primary"
      @change="update($event)"
    />
  </settings-option>
</template>
