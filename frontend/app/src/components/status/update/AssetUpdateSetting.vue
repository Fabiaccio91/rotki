<script setup lang="ts">
defineProps<{
  skipped: number;
  loading: boolean;
}>();

const emit = defineEmits<{ (e: 'check'): void }>();
const { t } = useI18n();
</script>

<template>
  <card class="mt-8">
    <template #title>{{ t('asset_update.manual.title') }}</template>
    <template #subtitle>{{ t('asset_update.manual.subtitle') }}</template>
    <div v-if="skipped" class="text-body-1">
      <i18n path="asset_update.manual.skipped">
        <template #skipped>
          <badge-display class="ml-2">{{ skipped }}</badge-display>
        </template>
      </i18n>
    </div>
    <template #buttons>
      <v-btn
        depressed
        color="primary"
        :loading="loading"
        @click="emit('check')"
      >
        {{ t('asset_update.manual.check') }}
      </v-btn>
    </template>
  </card>
</template>
