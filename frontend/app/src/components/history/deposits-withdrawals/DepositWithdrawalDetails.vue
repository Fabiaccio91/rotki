<script setup lang="ts">
import { type PropType } from 'vue';
import { type AssetMovementEntry } from '@/types/history/asset-movements';

defineProps({
  span: {
    type: Number,
    required: true
  },
  item: {
    required: true,
    type: Object as PropType<AssetMovementEntry>
  }
});

const { t } = useI18n();
</script>

<template>
  <table-expand-container visible :colspan="span">
    <template #title>
      {{ t('deposits_withdrawals.details.title') }}
    </template>
    <movement-links v-if="item.address || item.transactionId" :item="item" />
    <div v-else class="font-weight-medium pa-4" :class="$style.empty">
      {{ t('deposits_withdrawals.details.no_details') }}
    </div>
  </table-expand-container>
</template>

<style module lang="scss">
.empty {
  height: 100px;
}
</style>
