<script setup lang="ts">
import {
  type XswapAsset,
  type XswapBalance
} from '@rotki/common/lib/defi/xswap';
import { type PropType } from 'vue';
import { Zero } from '@/utils/bignumbers';

defineProps({
  balance: { required: true, type: Object as PropType<XswapBalance> }
});

const details = ref<boolean>(false);

const { currencySymbol } = storeToRefs(useGeneralSettingsStore());
const { t } = useI18n();

const getTotal = ({ totalAmount, usdPrice }: XswapAsset) =>
  usdPrice.multipliedBy(totalAmount ?? One);
</script>

<template>
  <v-dialog v-model="details" scrollable max-width="450px">
    <template #activator="{ on, attrs }">
      <v-tooltip open-delay="400" top>
        <template #activator="{ on: tipOn, attrs: tipAttrs }">
          <v-btn
            icon
            small
            v-bind="{ ...tipAttrs, ...attrs }"
            v-on="{ ...on, ...tipOn }"
          >
            <v-icon small color="primary">mdi-launch</v-icon>
          </v-btn>
        </template>
        <span>{{ t('liquidity_pool_details.tooltip') }}</span>
      </v-tooltip>
    </template>
    <card>
      <template #title>{{ t('liquidity_pool_details.title') }}</template>
      <template v-for="(token, key) in balance.assets">
        <v-divider v-if="key > 0" :key="token.asset + 'divider'" class="my-3" />
        <v-row :key="token.asset" align="center">
          <v-col cols="auto" class="pr-2">
            <asset-icon :identifier="token.asset" size="24px" />
          </v-col>
          <v-col>
            <v-row>
              <v-col md="6">
                <div class="text--secondary text-body-2">
                  {{ t('liquidity_pool_details.total_amount') }}
                </div>
                <div class="d-flex font-weight-bold">
                  <amount-display
                    :asset="token.asset"
                    :value="token.totalAmount ?? Zero"
                  />
                </div>
              </v-col>
              <v-col md="6">
                <div class="text--secondary text-body-2">
                  {{
                    t('liquidity_pool_details.total_value_in_symbol', {
                      symbol: currencySymbol
                    })
                  }}
                </div>
                <div class="d-flex font-weight-bold">
                  <amount-display
                    fiat-currency="USD"
                    :value="getTotal(token)"
                  />
                </div>
              </v-col>
            </v-row>
          </v-col>
        </v-row>
      </template>
      <div v-if="balance.totalSupply" class="d-flex pt-6">
        <div class="text--secondary text-body-2">
          {{ t('liquidity_pool_details.liquidity') }}:
        </div>
        <div class="pl-2 font-weight-bold">
          <amount-display :value="balance.totalSupply" />
        </div>
      </div>
    </card>
  </v-dialog>
</template>
