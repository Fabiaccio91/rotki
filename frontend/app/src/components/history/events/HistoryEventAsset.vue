<script setup lang="ts">
import { type HistoryEventEntry } from '@/types/history/events';
import { CURRENCY_USD } from '@/types/currencies';

const props = defineProps<{
  event: HistoryEventEntry;
}>();

const { event } = toRefs(props);
const { assetSymbol } = useAssetInfoRetrieval();

const { getEventType } = useHistoryEventMappings();

const showBalance = computed<boolean>(() => {
  const type = get(getEventType(event));
  return !type || !['approval', 'informational'].includes(type);
});

const eventAsset = useRefMap(event, ({ asset }) => asset);

const symbol = assetSymbol(eventAsset);
</script>

<template>
  <div>
    <div class="py-2 d-flex align-center">
      <div class="mr-2">
        <asset-link :asset="event.asset" icon>
          <asset-icon size="32px" :identifier="event.asset" />
        </asset-link>
      </div>
      <div v-if="showBalance">
        <div>
          <amount-display :value="event.balance.amount" :asset="event.asset" />
        </div>
        <div>
          <amount-display
            :key="event.timestamp"
            :amount="event.balance.amount"
            :value="event.balance.usdValue"
            :price-asset="event.asset"
            :fiat-currency="CURRENCY_USD"
            class="grey--text"
            :timestamp="event.timestamp"
          />
        </div>
      </div>
      <div v-else>
        {{ symbol }}
      </div>
    </div>
  </div>
</template>
