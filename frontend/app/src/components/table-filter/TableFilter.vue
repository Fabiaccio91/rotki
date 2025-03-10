<script setup lang="ts">
import { type AssetInfo } from '@rotki/common/lib/data';
import { type ComputedRef } from 'vue';
import {
  type MatchedKeyword,
  type SavedFilterLocation,
  type SearchMatcher,
  type Suggestion
} from '@/types/filtering';

const props = withDefaults(
  defineProps<{
    matches: MatchedKeyword<any>;
    matchers: SearchMatcher<any, any>[];
    location?: SavedFilterLocation | null;
    disabled?: boolean;
  }>(),
  {
    location: null,
    disabled: false
  }
);

const emit = defineEmits<{
  (e: 'update:matches', matches: MatchedKeyword<any>): void;
}>();

const { matchers, matches } = toRefs(props);

const input = ref();
const selection = ref<Suggestion[]>([]);
const search = ref('');
const selectedSuggestion = ref(0);
const suggestedFilter = ref<Suggestion>({
  index: 0,
  total: 0,
  asset: false,
  key: '',
  value: ''
});
const validKeys = computed(() => get(matchers).map(({ key }) => key));

const selectedMatcher = computed(() => {
  const searchKey = splitSearch(get(search));
  const key = get(validKeys).find(value => value === searchKey.key);
  return matcherForKey(key) ?? null;
});

const usedKeys = computed(() => get(selection).map(entry => entry.key));

const removeSelection = (suggestion: Suggestion) => {
  updateMatches(get(selection).filter(sel => sel !== suggestion));
};

const matcherForKey = (searchKey: string | undefined) =>
  get(matchers).find(({ key }) => key === searchKey);

const matcherForKeyValue = (searchKey: string | undefined) =>
  get(matchers).find(({ keyValue }) => keyValue === searchKey);

const setSearchToMatcherKey = (matcher: SearchMatcher<any>) => {
  const allowExclusion = 'string' in matcher && matcher.allowExclusion;
  const filter = `${matcher.key}${allowExclusion ? '' : '='}`;
  set(search, filter);
  get(input).focus();
};

function updateMatches(pairs: Suggestion[]) {
  const matched: Partial<MatchedKeyword<any>> = {};
  const validPairs: Suggestion[] = [];

  for (const entry of pairs) {
    const key = entry.key;
    const matcher = matcherForKey(key);
    if (!matcher) {
      continue;
    }

    const valueKey = (matcher.keyValue || matcher.key) as string;
    let transformedKeyword = '';
    if ('string' in matcher) {
      if (typeof entry.value !== 'string') {
        continue;
      }
      if (matcher.validate(entry.value)) {
        transformedKeyword = matcher.serializer?.(entry.value) || entry.value;

        if (entry.exclude) {
          transformedKeyword = `!${transformedKeyword}`;
        }
      } else {
        continue;
      }
    } else if (matcher.asset) {
      transformedKeyword =
        typeof entry.value !== 'string' ? entry.value.identifier : entry.value;
    }

    if (!transformedKeyword) {
      continue;
    }

    validPairs.push(entry);

    if (matcher.multiple) {
      if (!matched[valueKey]) {
        matched[valueKey] = [];
      }
      (matched[valueKey] as string[]).push(transformedKeyword);
    } else {
      matched[valueKey] = transformedKeyword;
    }
  }

  set(selection, validPairs);
  emit('update:matches', matched);
}

const applyFilter = (filter: Suggestion) => {
  let newSelection = [...get(selection)];
  const key = filter.key;
  const index = newSelection.findIndex(value => value.key === key);
  const matcher = matcherForKey(key);
  assert(matcher);

  if (
    index >= 0 &&
    (!matcher.multiple || newSelection[index].exclude !== filter.exclude)
  ) {
    newSelection = newSelection.filter(item => item.key !== key);
  }

  newSelection.push(filter);

  updateMatches(newSelection);
  set(search, '');
};

const filteredMatchers: ComputedRef<SearchMatcher<any>[]> = computed(() =>
  get(matchers).filter(
    ({ key, multiple }) =>
      (!get(usedKeys).includes(key) || multiple) &&
      key.startsWith(get(search) || '')
  )
);

const applySuggestion = async () => {
  const selectedIndex = get(selectedSuggestion);
  if (!get(selectedMatcher)) {
    const filteredMatchersVal = get(filteredMatchers);
    if (filteredMatchersVal.length >= selectedIndex) {
      setSearchToMatcherKey(filteredMatchersVal[selectedIndex]);
    }
    return;
  }

  const filter = get(suggestedFilter);
  if (filter.value) {
    nextTick(() => applyFilter(filter));
  } else {
    const { key, value: keyword, exclude } = splitSearch(get(search));

    const matcher = matcherForKey(key);
    let asset = false;
    if (matcher) {
      let suggestedItems: (AssetInfo | string)[] = [];
      if ('string' in matcher) {
        suggestedItems = matcher.suggestions();
      } else if ('asset' in matcher) {
        suggestedItems = await matcher.suggestions(keyword);
        asset = true;
      } else {
        logger.debug('Matcher missing asset=true or string=true', matcher);
      }

      if (
        suggestedItems.length === 0 &&
        'validate' in matcher &&
        matcher.validate(keyword)
      ) {
        nextTick(() =>
          applyFilter({
            key,
            asset,
            value: keyword,
            index: 0,
            total: 1,
            exclude
          })
        );
      }
    }
    if (!key) {
      get(input).blur();
    }
  }
  set(selectedSuggestion, 0);
  set(search, '');
};

onMounted(() => {
  get(input).onTabDown = function (e: KeyboardEvent) {
    e.preventDefault();
    e.stopPropagation();
    moveSuggestion(false);
  };
  get(input).onEnterDown = function (e: KeyboardEvent) {
    e.preventDefault();
    e.stopPropagation();
  };
});

watch(search, () => {
  set(selectedSuggestion, 0);
});

const moveSuggestion = (up: boolean) => {
  const total = get(selectedMatcher)
    ? get(suggestedFilter).total
    : get(filteredMatchers).length;

  let position = get(selectedSuggestion);
  const move = up ? -1 : 1;

  position += move;

  if (position >= total) {
    set(selectedSuggestion, 0);
  } else if (position < 0) {
    set(selectedSuggestion, total - 1);
  } else {
    set(selectedSuggestion, position);
  }
};

// TODO: This is too specific for custom asset, move it!
const getDisplayValue = (suggestion: Suggestion) => {
  const value = suggestion.value;
  if (typeof value === 'string') {
    return value;
  }

  return value.isCustomAsset ? value.name : value.symbol;
};

const getSuggestionText = (suggestion: Suggestion) => {
  const operator = suggestion.exclude ? '!=' : '=';
  return `${suggestion.key}${operator}${getDisplayValue(suggestion)}`;
};

const selectItem = (suggestion: Suggestion) => {
  nextTick(() => {
    set(search, getSuggestionText(suggestion));
  });
};

const restoreSelection = (matches: MatchedKeyword<any>): void => {
  const oldSelection = get(selection);
  const newSelection: Suggestion[] = [];
  Object.entries(matches).forEach(([key, value]) => {
    const foundMatchers = matcherForKeyValue(key);

    if (!(foundMatchers && value)) {
      return;
    }

    const values = typeof value === 'string' ? [value] : value;
    const asset = 'asset' in foundMatchers;

    values.forEach(value => {
      let deserializedValue = null;
      if (asset) {
        const prevAssetSelection = oldSelection.find(
          ({ key }) => key === foundMatchers.key
        );
        if (prevAssetSelection) {
          deserializedValue = prevAssetSelection.value;
        }
      }

      let exclude = false;
      if (!deserializedValue) {
        let normalizedValue = value;
        if (!asset && value.startsWith('!')) {
          normalizedValue = value.substring(1);
          exclude = true;
        }
        deserializedValue =
          foundMatchers.deserializer?.(normalizedValue) || normalizedValue;
      }

      newSelection.push({
        key: foundMatchers.key,
        value: deserializedValue,
        asset,
        total: 1,
        index: 0,
        exclude
      });
    });
  });

  set(selection, newSelection);
};

onMounted(() => {
  restoreSelection(get(matches));
});

watch(matches, matches => {
  restoreSelection(matches);
});

const css = useCssModule();
const slots = useSlots();
const { t } = useI18n();
</script>

<template>
  <v-tooltip
    :disabled="!disabled || !slots.tooltip"
    open-delay="400"
    close-delay="2500"
    top
  >
    <template #activator="{ on }">
      <div v-on="on">
        <v-card flat class="d-flex" data-cy="table-filter" :disabled="disabled">
          <v-combobox
            ref="input"
            :class="css.filter"
            :value="selection"
            outlined
            dense
            chips
            small-chips
            deletable-chips
            :label="t('table_filter.label')"
            solo
            flat
            multiple
            clearable
            hide-details
            :menu-props="{ maxHeight: '390px' }"
            prepend-inner-icon="mdi-filter-variant"
            :search-input.sync="search"
            @input="updateMatches($event)"
            @keydown.enter="applySuggestion()"
            @keydown.up.prevent
            @keydown.up="moveSuggestion(true)"
            @keydown.down.prevent
            @keydown.down="moveSuggestion(false)"
          >
            <template #selection="{ item, selected }">
              <v-chip
                label
                small
                class="font-weight-medium px-2"
                :input-value="selected"
                close
                @click:close="removeSelection(item)"
                @click="
                  removeSelection(item);
                  selectItem(item);
                "
              >
                <suggested-item chip :suggestion="item" />
              </v-chip>
            </template>
            <template #no-data>
              <filter-dropdown
                :matchers="filteredMatchers"
                :used="usedKeys"
                :keyword="search"
                :selected-matcher="selectedMatcher"
                :selection="selection"
                :selected-suggestion="selectedSuggestion"
                :location="location"
                @apply:filter="applyFilter($event)"
                @suggest="suggestedFilter = $event"
                @click="setSearchToMatcherKey($event)"
              />
            </template>
          </v-combobox>

          <div v-if="location" class="ml-2 mt-1">
            <saved-filter-management
              :selection="selection"
              :location="location"
              :matchers="matchers"
              @update:matches="updateMatches($event)"
            />
          </div>
        </v-card>
      </div>
    </template>
    <span :class="css.tooltip">
      <slot name="tooltip" />
    </span>
  </v-tooltip>
</template>

<style module lang="css">
.filter {
  border-radius: 4px !important;
}

.tooltip {
  pointer-events: initial !important;
}
</style>
