<script setup lang="ts">
import useVuelidate from '@vuelidate/core';
import { helpers, required, sameAs } from '@vuelidate/validators';
import { type Ref } from 'vue';
import { type CreateAccountPayload } from '@/types/login';

const props = defineProps({
  loading: { required: true, type: Boolean },
  error: { required: false, type: String, default: '' }
});

const emit = defineEmits<{
  (e: 'confirm', payload: CreateAccountPayload): void;
  (e: 'cancel'): void;
  (e: 'error:clear'): void;
}>();
const { error } = toRefs(props);

const store = useMainStore();
const { newUser } = toRefs(store);
const username: Ref<string> = ref('');
const password: Ref<string> = ref('');
const passwordConfirm: Ref<string> = ref('');

const premiumEnabled: Ref<boolean> = ref(false);
const userPrompted: Ref<boolean> = ref(false);

const submitUsageAnalytics: Ref<boolean> = ref(true);
const apiKey: Ref<string> = ref('');
const apiSecret: Ref<string> = ref('');
const syncDatabase: Ref<boolean> = ref(false);

const premiumFormValid: Ref<boolean> = ref(false);
const credentialsFormValid: Ref<boolean> = ref(false);
const step: Ref<number> = ref(1);

const form: Ref = ref(null);

const { t } = useI18n();

const rules = {
  username: {
    required: helpers.withMessage(
      t('create_account.select_credentials.validation.non_empty_username'),
      required
    ),
    isValidUsername: helpers.withMessage(
      t('create_account.select_credentials.validation.valid_username'),
      (v: string): boolean => !!(v && /^[\w.-]+$/.test(v))
    )
  },
  password: {
    required: helpers.withMessage(
      t('create_account.select_credentials.validation.non_empty_password'),
      required
    )
  },
  passwordConfirm: {
    required: helpers.withMessage(
      t(
        'create_account.select_credentials.validation.non_empty_password_confirmation'
      ),
      required
    ),
    isMatch: helpers.withMessage(
      t(
        'create_account.select_credentials.validation.password_confirmation_mismatch'
      ),
      sameAs(password)
    )
  }
};

const v$ = useVuelidate(
  rules,
  {
    username,
    password,
    passwordConfirm
  },
  {
    $autoDirty: true
  }
);

watch(v$, ({ $invalid }) => {
  set(credentialsFormValid, !$invalid);
});

const confirm = () => {
  const payload: CreateAccountPayload = {
    credentials: {
      username: get(username),
      password: get(password)
    },
    initialSettings: {
      submitUsageAnalytics: get(submitUsageAnalytics)
    }
  };

  if (get(premiumEnabled)) {
    payload.premiumSetup = {
      apiKey: get(apiKey),
      apiSecret: get(apiSecret),
      syncDatabase: get(syncDatabase)
    };
  }

  emit('confirm', payload);
};

const cancel = () => emit('cancel');

const errorClear = () => emit('error:clear');

const back = () => {
  set(step, Math.max(get(step) - 1, 1));
  if (get(error)) {
    errorClear();
  }
};
</script>

<template>
  <v-slide-y-transition>
    <div class="create-account">
      <div class="text-h6 text--primary create-account__header">
        {{ t('create_account.title') }}
      </div>
      <v-stepper v-model="step">
        <v-stepper-header>
          <v-stepper-step step="1" :complete="step > 1">
            <span v-if="step === 1">
              {{ t('create_account.premium.title') }}
            </span>
          </v-stepper-step>
          <v-divider />
          <v-stepper-step step="2" :complete="step > 2">
            <span v-if="step === 2">
              {{ t('create_account.select_credentials.title') }}
            </span>
          </v-stepper-step>
          <v-divider />
          <v-stepper-step step="3">
            <span v-if="step === 3">
              {{ t('create_account.usage_analytics.title') }}
            </span>
          </v-stepper-step>
        </v-stepper-header>
        <v-stepper-items>
          <v-stepper-content step="1">
            <v-card-text>
              <v-form :value="premiumFormValid">
                <v-alert text color="primary">
                  <i18n
                    tag="div"
                    path="create_account.premium.premium_question"
                  >
                    <template #premiumLink>
                      <b>
                        <external-link url="https://rotki.com/products">
                          {{ t('create_account.premium.premium_link_text') }}
                        </external-link>
                      </b>
                    </template>
                  </i18n>
                  <div class="d-flex mt-4 justify-center">
                    <v-btn
                      depressed
                      rounded
                      small
                      :outlined="premiumEnabled"
                      color="primary"
                      @click="
                        premiumEnabled = false;
                        syncDatabase = false;
                      "
                    >
                      <v-icon small class="mr-2">mdi-close</v-icon>
                      <span>
                        {{ t('common.actions.no') }}
                      </span>
                    </v-btn>
                    <v-btn
                      depressed
                      rounded
                      small
                      :outlined="!premiumEnabled"
                      color="primary"
                      class="ml-2"
                      @click="premiumEnabled = true"
                    >
                      <v-icon small class="mr-2"> mdi-check</v-icon>
                      <span>
                        {{ t('create_account.premium.button_premium_approve') }}
                      </span>
                    </v-btn>
                  </div>
                </v-alert>

                <premium-credentials
                  :enabled="premiumEnabled"
                  :api-secret="apiSecret"
                  :api-key="apiKey"
                  :loading="loading"
                  :sync-database="syncDatabase"
                  @update:api-key="apiKey = $event"
                  @update:api-secret="apiSecret = $event"
                  @update:sync-database="syncDatabase = $event"
                  @update:valid="premiumFormValid = $event"
                />
              </v-form>
            </v-card-text>
            <v-card-actions>
              <v-spacer />
              <v-btn
                class="create-account__button__cancel"
                depressed
                outlined
                color="primary"
                :disabled="loading || newUser"
                @click="cancel()"
              >
                {{ t('common.actions.cancel') }}
              </v-btn>
              <v-btn
                class="create-account__premium__button__continue"
                depressed
                color="primary"
                :disabled="premiumEnabled && !premiumFormValid"
                :loading="loading"
                data-cy="create-account__premium__button__continue"
                @click="step = 2"
              >
                {{ t('common.actions.continue') }}
              </v-btn>
            </v-card-actions>
          </v-stepper-content>
          <v-stepper-content step="2">
            <v-card-text>
              <v-form ref="form" :value="credentialsFormValid">
                <v-text-field
                  v-model="username"
                  outlined
                  autofocus
                  single-line
                  class="create-account__fields__username"
                  :label="t('create_account.select_credentials.label_username')"
                  prepend-inner-icon="mdi-account"
                  :error-messages="v$.username.$errors.map(e => e.$message)"
                  :disabled="loading"
                  required
                />
                <v-alert
                  v-if="syncDatabase"
                  text
                  class="mt-2 create-account__password-sync-requirement"
                  outlined
                  color="deep-orange"
                  icon="mdi-information"
                >
                  {{
                    t(
                      'create_account.select_credentials.password_sync_requirement'
                    )
                  }}
                </v-alert>
                <revealable-input
                  v-model="password"
                  outlined
                  class="create-account__fields__password"
                  :label="t('create_account.select_credentials.label_password')"
                  prepend-icon="mdi-lock"
                  :error-messages="v$.password.$errors.map(e => e.$message)"
                  :disabled="loading"
                  required
                />
                <revealable-input
                  v-model="passwordConfirm"
                  outlined
                  class="create-account__fields__password-repeat"
                  prepend-icon="mdi-repeat"
                  :error-messages="
                    v$.passwordConfirm.$errors.map(e => e.$message)
                  "
                  :disabled="loading"
                  :label="
                    t('create_account.select_credentials.label_password_repeat')
                  "
                  required
                />
                <v-checkbox
                  v-model="userPrompted"
                  class="create-account__boxes__user-prompted"
                  :label="
                    t(
                      'create_account.select_credentials.label_password_backup_reminder'
                    )
                  "
                />
              </v-form>
            </v-card-text>
            <v-card-actions>
              <v-spacer />
              <v-btn
                color="primary"
                class="create-account__credentials__button__back"
                depressed
                :disabled="loading"
                outlined
                @click="back()"
              >
                {{ t('common.actions.back') }}
              </v-btn>
              <v-btn
                class="create-account__credentials__button__continue"
                depressed
                color="primary"
                :disabled="!credentialsFormValid || loading || !userPrompted"
                :loading="loading"
                @click="step = 3"
              >
                {{ t('common.actions.continue') }}
              </v-btn>
            </v-card-actions>
          </v-stepper-content>
          <v-stepper-content step="3">
            <v-card-text>
              <v-alert
                outlined
                prominent
                color="primary"
                class="mx-auto text-justify text-body-2 create-account__analytics__content"
              >
                {{ t('create_account.usage_analytics.description') }}
              </v-alert>
              <v-alert v-if="error" type="error" outlined>
                {{ error }}
              </v-alert>
              <v-row no-gutters>
                <v-col>
                  <v-checkbox
                    v-model="submitUsageAnalytics"
                    :disabled="loading"
                    :label="t('create_account.usage_analytics.label_confirm')"
                  />
                </v-col>
              </v-row>
            </v-card-text>
            <v-card-actions>
              <v-spacer />
              <v-btn
                color="primary"
                class="create-account__analytics__button__back"
                depressed
                :disabled="loading"
                outlined
                @click="back()"
              >
                {{ t('common.actions.back') }}
              </v-btn>
              <v-btn
                color="primary"
                depressed
                :disabled="loading"
                :loading="loading"
                class="create-account__analytics__button__confirm"
                @click="confirm()"
              >
                {{ t('common.actions.create') }}
              </v-btn>
            </v-card-actions>
          </v-stepper-content>
        </v-stepper-items>
      </v-stepper>
    </div>
  </v-slide-y-transition>
</template>

<style scoped lang="scss">
.create-account {
  &__header {
    padding: 12px;
  }

  &__analytics {
    &__content {
      background-color: #f8f8f8 !important;
    }
  }

  &__password-sync-requirement {
    font-weight: bold;
    font-size: 0.8rem;
    line-height: 1rem;
  }

  :deep(.v-stepper) {
    box-shadow: none !important;

    .v-stepper {
      &__header {
        box-shadow: none !important;
      }

      &__content {
        padding: 12px !important;
      }
    }
  }
}
</style>
