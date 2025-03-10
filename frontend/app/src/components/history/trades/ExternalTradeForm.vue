﻿<script setup lang="ts">
import { helpers, required, requiredIf } from '@vuelidate/validators';
import dayjs from 'dayjs';
import { type Writeable } from '@/types';
import {
  type NewTrade,
  type Trade,
  type TradeType
} from '@/types/history/trade';
import { TaskType } from '@/types/task-type';
import { toMessages } from '@/utils/validation';

const props = withDefaults(
  defineProps<{
    editableItem?: Trade | null;
  }>(),
  {
    editableItem: null
  }
);

const { t } = useI18n();
const { editableItem } = toRefs(props);

const { isTaskRunning } = useTaskStore();
const { getHistoricPrice } = useBalancePricesStore();

const id = ref<string>('');
const base = ref<string>('');
const quote = ref<string>('');
const datetime = ref<string>('');
const amount = ref<string>('');
const rate = ref<string>('');
const quoteAmount = ref<string>('');
const fee = ref<string>('');
const feeCurrency = ref<string>('');
const link = ref<string>('');
const notes = ref<string>('');
const type = ref<TradeType>('buy');

const errorMessages = ref<Record<string, string[]>>({});

const quoteAmountInputFocused = ref<boolean>(false);
const feeInput = ref<any>(null);
const feeCurrencyInput = ref<any>(null);

const { assetSymbol } = useAssetInfoRetrieval();
const baseSymbol = assetSymbol(base);
const quoteSymbol = assetSymbol(quote);

const rules = {
  baseAsset: {
    required: helpers.withMessage(
      t('external_trade_form.validation.non_empty_base').toString(),
      required
    )
  },
  quoteAsset: {
    required: helpers.withMessage(
      t('external_trade_form.validation.non_empty_quote').toString(),
      required
    )
  },
  amount: {
    required: helpers.withMessage(
      t('external_trade_form.validation.non_empty_amount').toString(),
      required
    )
  },
  rate: {
    required: helpers.withMessage(
      t('external_trade_form.validation.non_empty_rate').toString(),
      required
    )
  },
  quoteAmount: {
    required: helpers.withMessage(
      t('external_trade_form.validation.non_empty_quote_amount').toString(),
      required
    )
  },
  fee: {
    required: helpers.withMessage(
      t('external_trade_form.validation.non_empty_fee').toString(),
      requiredIf(refIsTruthy(feeCurrency))
    )
  },
  feeCurrency: {
    required: helpers.withMessage(
      t('external_trade_form.validation.non_empty_fee_currency').toString(),
      requiredIf(refIsTruthy(fee))
    )
  }
};

const { valid, setValidation, setSubmitFunc } = useTradesForm();

const v$ = setValidation(
  rules,
  {
    baseAsset: base,
    quoteAsset: quote,
    amount,
    rate,
    quoteAmount,
    fee,
    feeCurrency
  },
  {
    $autoDirty: true,
    $externalResults: errorMessages
  }
);

const triggerFeeValidator = () => {
  get(feeInput)?.textInput?.validate(true);
  get(feeCurrencyInput)?.autoCompleteInput?.validate(true);
};

const quoteHint = computed<string>(() =>
  get(type) === 'buy'
    ? t('external_trade_form.buy_quote').toString()
    : t('external_trade_form.sell_quote').toString()
);

const shouldRenderSummary = computed<boolean>(
  () => !!(get(type) && get(base) && get(quote) && get(amount) && get(rate))
);

const fetching = isTaskRunning(TaskType.FETCH_HISTORIC_PRICE);

const numericAmount = bigNumberifyFromRef(amount);
const numericQuoteAmount = bigNumberifyFromRef(quoteAmount);
const numericFee = bigNumberifyFromRef(fee);
const numericRate = bigNumberifyFromRef(rate);

const reset = () => {
  set(id, '');
  set(datetime, convertFromTimestamp(dayjs().unix(), true));
  set(amount, '');
  set(rate, '');
  set(fee, '');
  set(feeCurrency, '');
  set(link, '');
  set(notes, '');
  set(type, 'buy');
  set(errorMessages, {});
};

const setEditMode = () => {
  const trade = get(editableItem);
  if (!trade) {
    reset();
    return;
  }

  set(base, trade.baseAsset);
  set(quote, trade.quoteAsset);
  set(datetime, convertFromTimestamp(trade.timestamp, true));
  set(amount, trade.amount.toFixed());
  set(rate, trade.rate.toFixed());
  set(fee, trade.fee?.toFixed() ?? '');
  set(feeCurrency, trade.feeCurrency ?? '');
  set(link, trade.link ?? '');
  set(notes, trade.notes ?? '');
  set(type, trade.tradeType);
  set(id, trade.tradeId);
};

const { setMessage } = useMessageStore();

const { addExternalTrade, editExternalTrade } = useTrades();

const save = async (): Promise<boolean> => {
  const amount = get(numericAmount);
  const fee = get(numericFee);
  const rate = get(numericRate);

  const tradePayload: Writeable<NewTrade> = {
    amount: amount.isNaN() ? Zero : amount,
    fee: fee.isNaN() || fee.isZero() ? undefined : fee,
    feeCurrency: get(feeCurrency) || undefined,
    link: get(link) || undefined,
    notes: get(notes) || undefined,
    baseAsset: get(base),
    quoteAsset: get(quote),
    rate: rate.isNaN() ? Zero : rate,
    location: 'external',
    timestamp: convertToTimestamp(get(datetime)),
    tradeType: get(type)
  };

  const identifier = get(id);
  const result = !identifier
    ? await addExternalTrade(tradePayload)
    : await editExternalTrade({ ...tradePayload, tradeId: identifier });

  if (result.success) {
    reset();
    return true;
  }

  if (result.message) {
    if (typeof result.message === 'string') {
      setMessage({
        description: result.message
      });
    } else {
      set(errorMessages, result.message);
      await get(v$).$validate();
    }
  }

  return false;
};

setSubmitFunc(save);

const updateRate = (forceUpdate = false) => {
  if (
    get(amount) &&
    get(rate) &&
    (!get(quoteAmountInputFocused) || forceUpdate)
  ) {
    set(
      quoteAmount,
      get(numericAmount).multipliedBy(get(numericRate)).toFixed()
    );
  }
};

const fetchPrice = async () => {
  if (
    (get(rate) && get(editableItem)) ||
    !get(datetime) ||
    !get(base) ||
    !get(quote)
  ) {
    return;
  }

  const timestamp = convertToTimestamp(get(datetime));
  const fromAsset = get(base);
  const toAsset = get(quote);

  const rateFromHistoricPrice = await getHistoricPrice({
    timestamp,
    fromAsset,
    toAsset
  });

  if (rateFromHistoricPrice.gt(0)) {
    set(rate, rateFromHistoricPrice.toFixed());
    updateRate(true);
  } else if (!get(rate)) {
    set(errorMessages, {
      rate: [t('external_trade_form.rate_not_found').toString()]
    });
    await get(v$).rate.$validate();
    useTimeoutFn(() => {
      set(errorMessages, {});
    }, 4000);
  }
};

const onQuoteAmountChange = () => {
  if (get(amount) && get(quoteAmount) && get(quoteAmountInputFocused)) {
    set(rate, get(numericQuoteAmount).div(get(numericAmount)).toFixed());
  }
};

watch([datetime, quote, base], async () => {
  await fetchPrice();
});

watch(rate, () => {
  updateRate();
});

watch(amount, () => {
  updateRate();
  onQuoteAmountChange();
});

watch(quoteAmount, () => {
  onQuoteAmountChange();
});

watch(editableItem, setEditMode);
onMounted(setEditMode);
</script>

<template>
  <v-form :value="valid" data-cy="trade-form" class="external-trade-form pt-1">
    <date-time-picker
      v-model="datetime"
      required
      outlined
      seconds
      limit-now
      data-cy="date"
      :label="t('external_trade_form.date.label')"
      persistent-hint
      :hint="t('external_trade_form.date.hint')"
      :error-messages="errorMessages['timestamp']"
    />

    <v-row class="pt-1">
      <v-col cols="12" md="4">
        <div data-cy="type">
          <v-radio-group
            v-model="type"
            class="mt-2 mt-md-3"
            hide-details
            :column="false"
            required
            :label="t('external_trade_form.trade_type.label')"
          >
            <v-radio
              class="ml-4"
              :label="t('external_trade_form.trade_type.buy')"
              value="buy"
            />
            <v-radio
              class="ml-4"
              :label="t('external_trade_form.trade_type.sell')"
              value="sell"
            />
          </v-radio-group>
        </div>
      </v-col>
      <v-col cols="12" md="8" class="d-flex flex-column">
        <v-row>
          <v-col cols="12" md="5" class="d-flex flex-row align-center">
            <asset-select
              v-model="base"
              outlined
              required
              data-cy="base-asset"
              :error-messages="toMessages(v$.baseAsset)"
              :hint="t('external_trade_form.base_asset.hint')"
              :label="t('external_trade_form.base_asset.label')"
              @blur="v$.baseAsset.$touch()"
            />
          </v-col>
          <v-col class="d-flex flex-row align-center">
            <div class="text--secondary external-trade-form__action-hint">
              {{ quoteHint }}
            </div>
          </v-col>
          <v-col cols="12" md="5" class="d-flex flex-row align-center">
            <asset-select
              v-model="quote"
              required
              outlined
              data-cy="quote-asset"
              :error-messages="toMessages(v$.quoteAsset)"
              :hint="t('external_trade_form.quote_asset.hint')"
              :label="t('external_trade_form.quote_asset.label')"
              @blur="v$.quoteAsset.$touch()"
            />
          </v-col>
        </v-row>
      </v-col>
    </v-row>

    <div class="mt-2">
      <amount-input
        v-model="amount"
        required
        outlined
        :error-messages="toMessages(v$.amount)"
        data-cy="amount"
        :label="t('common.amount')"
        persistent-hint
        :hint="t('external_trade_form.amount.hint')"
        @blur="v$.amount.$touch()"
      />
      <two-fields-amount-input
        class="mb-5"
        :primary-value.sync="rate"
        :secondary-value.sync="quoteAmount"
        :loading="fetching"
        :disabled="fetching"
        data-cy="trade-rate"
        :label="{
          primary: t('external_trade_form.rate.label'),
          secondary: t('external_trade_form.quote_amount.label')
        }"
        :error-messages="{
          primary: toMessages(v$.rate),
          secondary: toMessages(v$.quoteAmount)
        }"
        @update:reversed="quoteAmountInputFocused = $event"
      />
      <div
        v-if="shouldRenderSummary"
        class="text-caption green--text mt-n4 mb-n1"
      >
        <v-icon small class="mr-2 green--text"> mdi-comment-quote </v-icon>
        <i18n v-if="type === 'buy'" path="external_trade_form.summary.buy">
          <template #label>
            <strong>
              {{ t('external_trade_form.summary.label') }}
            </strong>
          </template>
          <template #amount>
            <strong>
              <amount-display :value="numericAmount" :tooltip="false" />
            </strong>
          </template>
          <template #base>
            <strong>{{ baseSymbol }}</strong>
          </template>
          <template #quote>
            <strong>{{ quoteSymbol }}</strong>
          </template>
          <template #rate>
            <strong>
              <amount-display :value="numericRate" :tooltip="false" />
            </strong>
          </template>
        </i18n>
        <i18n
          v-if="type === 'sell'"
          tag="span"
          path="external_trade_form.summary.sell"
        >
          <template #label>
            <strong>
              {{ t('external_trade_form.summary.label') }}
            </strong>
          </template>
          <template #amount>
            <strong>
              <amount-display :value="numericAmount" :tooltip="false" />
            </strong>
          </template>
          <template #base>
            <strong>{{ baseSymbol }}</strong>
          </template>
          <template #quote>
            <strong>{{ quoteSymbol }}</strong>
          </template>
          <template #rate>
            <strong>
              <amount-display :value="numericRate" :tooltip="false" />
            </strong>
          </template>
        </i18n>
      </div>
    </div>

    <v-divider class="mb-6 mt-8" />

    <v-row class="mb-2">
      <v-col cols="12" md="6">
        <amount-input
          ref="feeInput"
          v-model="fee"
          class="external-trade-form__fee"
          persistent-hint
          outlined
          data-cy="fee"
          :required="!!feeCurrency"
          :label="t('external_trade_form.fee.label')"
          :hint="t('external_trade_form.fee.hint')"
          :error-messages="toMessages(v$.fee)"
          @input="triggerFeeValidator()"
        />
      </v-col>
      <v-col cols="12" md="6">
        <asset-select
          ref="feeCurrencyInput"
          v-model="feeCurrency"
          data-cy="fee-currency"
          outlined
          persistent-hint
          :label="t('external_trade_form.fee_currency.label')"
          :hint="t('external_trade_form.fee_currency.hint')"
          :required="!!fee"
          :error-messages="toMessages(v$.feeCurrency)"
          @input="triggerFeeValidator()"
        />
      </v-col>
    </v-row>

    <v-text-field
      v-model="link"
      data-cy="link"
      outlined
      prepend-inner-icon="mdi-link"
      :label="t('external_trade_form.link.label')"
      persistent-hint
      :hint="t('external_trade_form.link.hint')"
      :error-messages="errorMessages['link']"
    />

    <v-textarea
      v-model="notes"
      prepend-inner-icon="mdi-text-box-outline"
      outlined
      data-cy="notes"
      class="mt-4"
      :label="t('external_trade_form.notes.label')"
      persistent-hint
      :hint="t('external_trade_form.notes.hint')"
      :error-messages="errorMessages['notes']"
    />
  </v-form>
</template>

<style scoped lang="scss">
.external-trade-form {
  &__action-hint {
    width: 60px;
    margin-top: -2rem;
  }
}
</style>
