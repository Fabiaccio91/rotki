<script setup lang="ts">
const { t } = useI18n();

const emit = defineEmits<{ (e: 'proceed', approval: 'yes' | 'no'): void }>();

const { syncConflict } = storeToRefs(useSessionAuthStore());

const lastModified = useRefMap(syncConflict, conflict => {
  if (!conflict || !conflict.payload) {
    return null;
  }
  const { localLastModified, remoteLastModified } = conflict.payload;
  return {
    remote: remoteLastModified,
    local: localLastModified
  };
});
</script>

<template>
  <transition name="bounce">
    <login-action-alert
      v-if="syncConflict"
      icon="mdi-cloud-download"
      @cancel="emit('proceed', 'no')"
      @confirm="emit('proceed', 'yes')"
    >
      <template #title>{{ t('login.sync_error.title') }}</template>

      <div>{{ syncConflict.message }}</div>
      <ul v-if="lastModified" class="mt-2">
        <li>
          <i18n path="login.sync_error.local_modified">
            <div class="font-weight-medium">
              <date-display :timestamp="lastModified.local" />
            </div>
          </i18n>
        </li>
        <li class="mt-2">
          <i18n path="login.sync_error.remote_modified">
            <div class="font-weight-medium">
              <date-display :timestamp="lastModified.remote" />
            </div>
          </i18n>
        </li>
      </ul>
      <div class="mt-2">{{ t('login.sync_error.question') }}</div>
    </login-action-alert>
  </transition>
</template>
