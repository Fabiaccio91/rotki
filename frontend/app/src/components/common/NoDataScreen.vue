<script setup lang="ts">
const FullSizeContent = defineAsyncComponent(
  () => import('@/components/common/FullSizeContent.vue')
);

withDefaults(defineProps<{ full?: boolean }>(), { full: true });

const slots = useSlots();
const css = useCssModule();
const { mobile } = useDisplay();
const remoteEmptyScreenLogo =
  'https://raw.githubusercontent.com/rotki/data/main/assets/icons/empty_screen_logo.png';
</script>

<template>
  <component :is="full ? FullSizeContent : 'div'">
    <v-row align="center" justify="center" :class="{ 'mb-10': !full }">
      <v-col cols="auto" :class="css.logo">
        <slot name="logo">
          <rotki-logo
            :width="mobile ? '100px' : '200px'"
            :url="remoteEmptyScreenLogo"
          />
        </slot>
      </v-col>
    </v-row>
    <v-row class="text-center">
      <v-col>
        <div v-if="slots.title" class="text-h5">
          <slot name="title" />
        </div>
        <slot />
      </v-col>
    </v-row>
  </component>
</template>

<style module lang="scss">
.logo {
  padding: 80px;
  border-radius: 50%;
  background-color: var(--v-rotki-light-grey-darken1);
}
</style>
