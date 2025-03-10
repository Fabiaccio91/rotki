<script setup lang="ts">
import { useAppRoutes } from '@/router/routes';
import { NoteLocation } from '@/types/notes';

const { t } = useI18n();

defineProps({
  visible: { required: true, type: Boolean }
});

const emit = defineEmits(['visible:update', 'about']);
const tab = ref<number>(0);
const visibleUpdate = (_visible: boolean) => {
  emit('visible:update', _visible);
};

const route = useRoute();

const location = computed<string>(() => {
  const meta = get(route).meta;

  if (meta && meta.noteLocation) {
    return meta.noteLocation;
  }

  let noteLocation = '';
  get(route).matched.forEach(matched => {
    if (matched.meta.noteLocation) {
      noteLocation = matched.meta.noteLocation;
    }
  });

  return noteLocation;
});

const { appRoutes } = useAppRoutes();

const getNoteLocationKey = (key: string): string | null => {
  const index = Object.values<string>(NoteLocation).indexOf(key);
  if (index > -1) {
    return Object.keys(NoteLocation)[index];
  }

  return null;
};

const locationName = computed<string>(() => {
  const locationVal = get(location);
  if (!locationVal) {
    return '';
  }

  const noteLocationKey = getNoteLocationKey(locationVal);
  if (!noteLocationKey) {
    return '';
  }

  const Routes = get(appRoutes);
  const keyIn = (key: string): key is keyof typeof Routes => key in Routes;

  if (keyIn(noteLocationKey)) {
    return Routes[noteLocationKey].text;
  }

  return '';
});

watch(locationName, locationName => {
  if (locationName === '') {
    set(tab, 0);
  }
});

const { smAndDown } = useDisplay();
</script>

<template>
  <v-navigation-drawer
    width="400px"
    class="user-notes-sidebar"
    :class="smAndDown ? 'user-notes-sidebar--mobile' : null"
    absolute
    clipped
    :value="visible"
    right
    temporary
    hide-overlay
    @input="visibleUpdate($event)"
  >
    <v-sheet elevation="2">
      <v-row no-gutters justify="space-between" align="center">
        <v-col>
          <v-tabs
            v-model="tab"
            class="tabs"
            fixed-tabs
            height="42"
            mobile-breakpoint="0"
          >
            <v-tab>
              {{ t('notes_menu.tabs.general') }}
            </v-tab>
            <v-tooltip bottom>
              <template #activator="{ on }">
                <v-tab v-if="locationName" class="ml-2" v-on="on">
                  {{
                    t('notes_menu.tabs.in_this_page', { page: locationName })
                  }}
                </v-tab>
              </template>
              <div>
                {{
                  t('notes_menu.tabs.in_this_page_tooltip', {
                    page: locationName
                  })
                }}
              </div>
            </v-tooltip>
          </v-tabs>
        </v-col>
        <v-col cols="auto" class="pr-2">
          <v-btn icon @click="visibleUpdate(false)">
            <v-icon>mdi-close</v-icon>
          </v-btn>
        </v-col>
      </v-row>
    </v-sheet>

    <user-notes-list
      :key="location + tab"
      :location="tab === 0 ? '' : location"
    />
  </v-navigation-drawer>
</template>

<style lang="scss" scoped>
.user-notes-sidebar {
  top: 64px !important;
  box-shadow: 0 2px 12px rgba(74, 91, 120, 0.1);
  padding-top: 0 !important;
  border-top: var(--v-rotki-light-grey-darken1) solid thin;

  &--mobile {
    top: 56px !important;
  }

  &.v-navigation-drawer {
    &--is-mobile {
      padding-top: 0 !important;
    }
  }
}

.tabs {
  :deep(.v-slide-group) {
    .v-slide-group {
      &__prev,
      &__next {
        display: none;
      }

      &__wrapper {
        .v-tab {
          font-size: 0.75rem;
          padding: 0 1rem;
          margin-left: 0;
          flex: none;
          width: auto;
        }
      }
    }
  }
}
</style>
