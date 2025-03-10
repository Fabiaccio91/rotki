<script setup lang="ts">
import { helpers, required } from '@vuelidate/validators';
import { TRADE_LOCATION_EXTERNAL } from '@/data/defaults';
import { type TradeLocation } from '@/types/history/trade/location';
import { type ManualBalance } from '@/types/manual-balances';
import { toMessages } from '@/utils/validation';
import { BalanceType } from '@/types/balances';
import ManualBalancesPriceForm from '@/components/accounts/manual-balances/ManualBalancesPriceForm.vue';

const props = withDefaults(
  defineProps<{
    edit?: ManualBalance | null;
    context: BalanceType;
  }>(),
  {
    edit: null
  }
);

const emit = defineEmits<{
  (e: 'clear'): void;
}>();

const { t } = useI18n();

const { edit, context } = toRefs(props);

const errors: Ref<Record<string, string[]>> = ref({});

const id = ref<number | null>(null);
const asset = ref<string>('');
const label = ref<string>('');
const amount = ref<string>('');
const tags: Ref<string[]> = ref([]);
const location: Ref<TradeLocation> = ref(TRADE_LOCATION_EXTERNAL);
const balanceType: Ref<BalanceType> = ref(BalanceType.ASSET);
const form = ref<any>(null);
const priceForm: Ref<InstanceType<typeof ManualBalancesPriceForm> | null> =
  ref(null);

const reset = () => {
  get(form)?.reset();
  set(balanceType, get(context));
  set(errors, {});
};

const clear = () => {
  emit('clear');
  reset();
};

const setBalance = (balance: ManualBalance) => {
  set(id, balance.id);
  set(asset, balance.asset);
  set(label, balance.label);
  set(amount, balance.amount.toFixed());
  set(tags, balance.tags ?? []);
  set(location, balance.location);
  set(balanceType, balance.balanceType);
};

watch(
  edit,
  balance => {
    if (!balance) {
      reset();
    } else {
      setBalance(balance);
    }
  },
  { immediate: true }
);

const { editManualBalance, addManualBalance, manualLabels } =
  useManualBalancesStore();
const { refreshPrices } = useBalances();
const { setMessage } = useMessageStore();

const { valid, submitting, setValidation, setSubmitFunc } =
  useManualBalancesForm();

const rules = {
  amount: {
    required: helpers.withMessage(
      t('manual_balances_form.validation.amount'),
      required
    )
  },
  label: {
    required: helpers.withMessage(
      t('manual_balances_form.validation.label_empty'),
      required
    )
  },
  asset: {
    required: helpers.withMessage(
      t('manual_balances_form.validation.asset'),
      required
    )
  },
  location: {
    required
  }
};

const v$ = setValidation(
  rules,
  {
    amount,
    asset,
    label,
    location
  },
  { $autoDirty: true, $externalResults: errors }
);

const save = async () => {
  const balance: Omit<ManualBalance, 'id' | 'asset'> = {
    amount: bigNumberify(get(amount)),
    label: get(label),
    tags: get(tags),
    location: get(location),
    balanceType: get(balanceType)
  };

  const usedAsset: string = get(asset);

  const idVal = get(id);
  const isEdit = get(edit) && idVal;

  const form = get(priceForm);
  await form?.savePrice(usedAsset);

  const status = await (isEdit
    ? editManualBalance({ ...balance, id: idVal, asset: usedAsset })
    : addManualBalance({ ...balance, asset: usedAsset }));

  startPromise(refreshPrices(true));

  if (status.success) {
    clear();
    return true;
  }

  if (status.message) {
    if (typeof status.message !== 'string') {
      set(errors, status.message);
      await get(v$).$validate();
    } else {
      const obj = { message: status.message };
      setMessage({
        description: isEdit
          ? t('actions.manual_balances.edit.error.description', obj)
          : t('actions.manual_balances.add.error.description', obj)
      });
    }
  }
  return false;
};

setSubmitFunc(save);

watch(label, label => {
  if (get(edit)) {
    return;
  }

  const validationErrors = get(errors)['label'];
  if (get(manualLabels).includes(label)) {
    if (validationErrors && validationErrors.length > 0) {
      return;
    }
    set(errors, {
      ...get(errors),
      label: [
        t('manual_balances_form.validation.label_exists', {
          label
        }).toString()
      ]
    });
  } else {
    const { label, ...data } = get(errors);
    set(errors, data);
  }

  get(v$).label.$validate();
});

const { setOpenDialog, setPostSubmitFunc } = useCustomAssetForm();

const postSubmit = (assetId: string) => {
  set(asset, assetId);
};

setPostSubmitFunc(postSubmit);

const customAssetTypes = ref<string[]>([]);

const { getCustomAssetTypes } = useAssetManagementApi();

const openCustomAssetForm = async () => {
  if (get(customAssetTypes).length === 0) {
    set(customAssetTypes, await getCustomAssetTypes());
  }

  setOpenDialog(true);
};

onMounted(async () => {
  const editPayload = get(edit);
  if (editPayload) {
    set(asset, editPayload.asset);
  }
});

const css = useCssModule();
</script>

<template>
  <v-form
    ref="form"
    :value="valid"
    :class="css.form"
    data-cy="manual-balance-form"
  >
    <v-text-field
      v-model="label"
      class="manual-balances-form__label"
      outlined
      :label="t('manual_balances_form.fields.label')"
      :error-messages="toMessages(v$.label)"
      :disabled="submitting"
      @blur="v$.label.$touch()"
    />

    <balance-type-input
      v-model="balanceType"
      :disabled="submitting"
      :label="t('manual_balances_form.fields.balance_type')"
      outlined
    />

    <v-row>
      <v-col>
        <asset-select
          v-model="asset"
          :label="t('common.asset')"
          class="manual-balances-form__asset"
          outlined
          :error-messages="toMessages(v$.asset)"
          :disabled="submitting"
          @blur="v$.asset.$touch()"
        />
      </v-col>
      <v-col cols="auto">
        <v-tooltip top>
          <template #activator="{ on }">
            <v-btn
              text
              color="primary"
              class="mt-1 py-6"
              :disabled="submitting"
              v-on="on"
              @click="openCustomAssetForm()"
            >
              <div class="d-flex">
                <v-icon large>mdi-pencil-circle-outline</v-icon>
                <v-icon small class="mt-n4">mdi-plus</v-icon>
              </div>
            </v-btn>
          </template>
          <span>
            {{ t('manual_balances_form.fields.create_a_custom_asset') }}
          </span>
        </v-tooltip>
      </v-col>
    </v-row>

    <manual-balances-price-form
      ref="priceForm"
      :pending="submitting"
      :asset="asset"
    />

    <amount-input
      v-model="amount"
      :label="t('common.amount')"
      :error-messages="toMessages(v$.amount)"
      class="manual-balances-form__amount"
      outlined
      autocomplete="off"
      :disabled="submitting"
      @blur="v$.amount.$touch()"
    />

    <tag-input
      v-model="tags"
      :label="t('manual_balances_form.fields.tags')"
      :disabled="submitting"
      outlined
      class="manual-balances-form__tags"
    />

    <location-selector
      v-model="location"
      class="manual-balances-form__location"
      outlined
      :error-messages="toMessages(v$.location)"
      :disabled="submitting"
      :label="t('common.location')"
      attach=".manual-balances-form__location"
      @blur="v$.location.$touch()"
    />
    <custom-asset-form-dialog
      :title="t('asset_management.add_title')"
      :types="customAssetTypes"
    />
  </v-form>
</template>

<style module lang="scss">
.form {
  padding-top: 12px;
}
</style>
