<script setup lang="ts">
const haveCSVSummary = ref(false);
const { pnlCsvHaveSummary } = storeToRefs(useAccountingSettingsStore());

onMounted(() => {
  set(haveCSVSummary, get(pnlCsvHaveSummary));
});

const { t } = useI18n();
</script>

<template>
  <settings-option
    #default="{ error, success, update }"
    setting="pnlCsvHaveSummary"
    :error-message="t('account_settings.messages.have_csv_summary')"
  >
    <v-switch
      v-model="haveCSVSummary"
      class="csv_export_settings__haveCSVSummary"
      :label="t('account_settings.csv_export_settings.labels.have_csv_summary')"
      color="primary"
      :success-messages="success"
      :error-messages="error"
      @change="update($event)"
    />
  </settings-option>
</template>
