<script setup lang="ts">
import { BigNumber } from '@rotki/common';
import { assetSymbolToIdentifierMap } from '@rotki/common/lib/data';
import Fragment from '@/components/helper/Fragment';

const props = defineProps({
  totalInterestOwed: {
    type: BigNumber,
    required: true
  },
  stabilityFee: {
    type: String,
    required: true
  },
  loading: {
    type: Boolean,
    required: true
  }
});

const premium = usePremium();
const { totalInterestOwed } = toRefs(props);
const { t } = useI18n();
const interest = computed(() => {
  if (get(totalInterestOwed).isNegative()) {
    return Zero;
  }
  return get(totalInterestOwed);
});

const dai: string = assetSymbolToIdentifierMap.DAI;
const assetPadding = 4;
</script>

<template>
  <fragment>
    <v-divider class="my-4" />
    <loan-row :title="t('makerdao_vault_debt.stability_fee')" class="mb-2">
      <percentage-display :value="stabilityFee" :asset-padding="assetPadding" />
    </loan-row>
    <loan-row :title="t('makerdao_vault_debt.total_lost')">
      <div v-if="premium">
        <amount-display
          :asset-padding="assetPadding"
          :value="interest"
          :loading="loading"
          :asset="dai"
        />
      </div>
      <div v-else>
        <premium-lock />
      </div>
    </loan-row>
  </fragment>
</template>
