<script setup lang="ts">
import { type PropType } from 'vue';
import { type AaveLoan } from '@/types/defi/lending';

const props = defineProps({
  loan: {
    required: true,
    type: Object as PropType<AaveLoan>
  }
});

const { loan } = toRefs(props);
const { t } = useI18n();
const assetPadding = 5;
const totalCollateralUsd = totalCollateral(loan);
</script>

<template>
  <stat-card :title="t('loan_collateral.title')">
    <loan-row medium :title="t('loan_collateral.locked_collateral')">
      <amount-display
        :asset-padding="assetPadding"
        :value="totalCollateralUsd"
        fiat-currency="USD"
      />
    </loan-row>
    <v-divider class="my-4" />
    <loan-row
      v-if="loan.collateral.length > 0"
      :title="t('loan_collateral.per_asset')"
    >
      <v-row
        v-for="collateral in loan.collateral"
        :key="collateral.asset"
        no-gutters
      >
        <v-col>
          <balance-display :asset="collateral.asset" :value="collateral" />
        </v-col>
      </v-row>
    </loan-row>
    <v-divider v-if="loan.collateral.length > 0" class="my-4" />

    <loan-row :title="t('loan_collateral.stable_apr')" class="mb-2">
      <percentage-display :value="loan.stableApr ? loan.stableApr : null" />
    </loan-row>
    <loan-row :title="t('loan_collateral.variable_apr')">
      <percentage-display :value="loan.variableApr ? loan.variableApr : null" />
    </loan-row>
  </stat-card>
</template>
