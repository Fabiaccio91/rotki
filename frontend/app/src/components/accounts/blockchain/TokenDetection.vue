<script setup lang="ts">
import { type Blockchain } from '@rotki/common/lib/blockchain';

const props = defineProps<{
  address: string;
  loading: boolean;
  blockchain: Blockchain;
}>();

const { address, blockchain } = toRefs(props);

const { detectingTokens, detectedTokens, detectTokens } = useTokenDetection(
  blockchain,
  address
);

const { t } = useI18n();
</script>

<template>
  <div class="d-flex align-center justify-end">
    <div class="mr-2">
      {{ detectedTokens.total }}
    </div>
    <div>
      <v-tooltip top>
        <template #activator="{ on }">
          <v-btn
            text
            icon
            :disabled="detectingTokens || loading"
            v-on="on"
            @click="detectTokens()"
          >
            <v-progress-circular
              v-if="detectingTokens"
              indeterminate
              color="primary"
              width="2"
              size="20"
            />
            <v-icon v-else small>mdi-refresh</v-icon>
          </v-btn>
        </template>
        <div class="text-center">
          <div>
            {{ t('account_balances.detect_tokens.tooltip.redetect') }}
          </div>
          <div v-if="detectedTokens.timestamp">
            <i18n path="account_balances.detect_tokens.tooltip.last_detected">
              <template #time>
                <date-display :timestamp="detectedTokens.timestamp" />
              </template>
            </i18n>
          </div>
        </div>
      </v-tooltip>
    </div>
  </div>
</template>
