<script setup lang="ts">
const { t } = useI18n();
</script>

<template>
  <import-source source="uphold_transactions">
    <template #upload-title>
      <i18n tag="span" path="import_data.uphold.import">
        <strong>{{ t('import_data.uphold.import_trade') }}</strong>
      </i18n>
    </template>
    <i18n tag="span" path="import_data.note">
      <strong>{{ t('import_data.uphold.name') }}</strong>
    </i18n>
    <ul>
      <li>{{ t('import_data.uphold.line_one') }}</li>
      <li>{{ t('import_data.uphold.line_two') }}</li>
    </ul>
  </import-source>
</template>
