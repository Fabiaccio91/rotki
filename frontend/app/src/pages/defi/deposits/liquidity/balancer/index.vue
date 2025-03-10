<script setup lang="ts">
import { BalancerBalances } from '@/premium/premium';
import { Module } from '@/types/modules';
import { Section } from '@/types/status';

const modules: Module[] = [Module.BALANCER];

const { fetchBalances, fetchEvents } = useBalancerStore();
const { isModuleEnabled } = useModules();
const { shouldShowLoadingScreen, isLoading } = useStatusStore();

const premium = usePremium();
const isEnabled = computed(() => isModuleEnabled(modules[0]));
const balancesLoading = shouldShowLoadingScreen(Section.DEFI_BALANCER_BALANCES);
const eventsLoading = shouldShowLoadingScreen(Section.DEFI_BALANCER_EVENTS);
const loading = computed(() => get(balancesLoading) && get(eventsLoading));
const balancesRefreshing = isLoading(Section.DEFI_BALANCER_BALANCES);
const eventsRefreshing = isLoading(Section.DEFI_BALANCER_EVENTS);
const refreshing = computed(
  () => get(balancesRefreshing) || get(eventsRefreshing)
);

const { t } = useI18n();

onMounted(async () => {
  await Promise.allSettled([fetchBalances(false), fetchEvents(false)]);
});
</script>

<template>
  <no-premium-placeholder v-if="!premium" :text="t('balancer.premium')" />
  <module-not-active v-else-if="!isEnabled" :modules="modules" />
  <progress-screen v-else-if="loading">
    <template #message>
      {{ t('balancer.loading') }}
    </template>
  </progress-screen>
  <div v-else>
    <balancer-balances class="mt-4" :refreshing="refreshing">
      <template #modules>
        <active-modules :modules="modules" />
      </template>
    </balancer-balances>
  </div>
</template>
