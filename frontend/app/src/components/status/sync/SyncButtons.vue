<script setup lang="ts">
import {
  SYNC_DOWNLOAD,
  SYNC_UPLOAD,
  type SyncAction
} from '@/types/session/sync';

defineProps({
  pending: { required: true, type: Boolean }
});

const emit = defineEmits<{
  (event: 'action', action: SyncAction): void;
}>();

const { t } = useI18n();

const { premium } = storeToRefs(usePremiumStore());
const UPLOAD: SyncAction = SYNC_UPLOAD;
const DOWNLOAD: SyncAction = SYNC_DOWNLOAD;

const action = (action: SyncAction) => {
  emit('action', action);
};
</script>

<template>
  <div class="d-flex flex-wrap mx-n1">
    <v-tooltip top open-delay="400">
      <template #activator="{ on, attrs }">
        <v-btn
          v-bind="attrs"
          outlined
          depressed
          class="ma-1"
          color="primary"
          :disabled="!premium || pending"
          v-on="on"
          @click="action(UPLOAD)"
        >
          <v-icon>mdi-cloud-upload</v-icon>
          <span class="ml-2">{{ t('common.actions.push') }}</span>
        </v-btn>
      </template>
      <span>{{ t('sync_buttons.upload_tooltip') }}</span>
    </v-tooltip>

    <v-tooltip top open-delay="400">
      <template #activator="{ on, attrs }">
        <v-btn
          v-bind="attrs"
          outlined
          depressed
          class="ma-1"
          color="primary"
          :disabled="!premium || pending"
          v-on="on"
          @click="action(DOWNLOAD)"
        >
          <v-icon>mdi-cloud-download</v-icon>
          <span class="ml-2">{{ t('common.actions.pull') }}</span>
        </v-btn>
      </template>
      <span>{{ t('sync_buttons.download_tooltip') }}</span>
    </v-tooltip>
  </div>
</template>
