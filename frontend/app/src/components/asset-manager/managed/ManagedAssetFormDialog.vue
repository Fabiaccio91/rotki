<script setup lang="ts">
import { type SupportedAsset } from '@rotki/common/lib/data';

const props = withDefaults(
  defineProps<{
    title: string;
    subtitle?: string;
    editableItem?: SupportedAsset | null;
  }>(),
  {
    subtitle: '',
    editableItem: null
  }
);

const { editableItem } = toRefs(props);
const { t } = useI18n();

const { openDialog, submitting, closeDialog, trySubmit } =
  useManagedAssetForm();
</script>

<template>
  <big-dialog
    :display="openDialog"
    :title="title"
    :subtitle="subtitle"
    :primary-action="t('common.actions.save')"
    :loading="submitting"
    @confirm="trySubmit()"
    @cancel="closeDialog()"
  >
    <managed-asset-form :editable-item="editableItem" />
  </big-dialog>
</template>
