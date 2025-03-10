<script setup lang="ts">
import { useListeners } from 'vue';
import { type DataTableHeader } from '@/types/vuetify';
import { type TablePagination } from '@/types/pagination';

const { t } = useI18n();

const props = withDefaults(
  defineProps<{
    sortDesc?: boolean;
    /**
     * Disables the triple (asc/desc/neutral) state sorting.
     *
     * Default: true
     *
     * This option has been disabled by default since it was confusing to users.
     * It should be turned off if multiSort is set to true since multiSort
     * relies on the neutral state to change the multi-sort order.
     */
    mustSort?: boolean;
    /**
     * Enables the ability to sort by multiple columns.
     *
     * Default: false
     *
     * Does not work well with mustSort.
     */
    multiSort?: boolean;
    items: any[];
    headers: DataTableHeader[];
    expanded?: any[];
    itemClass?: string | Function;
    hideDefaultFooter?: boolean;
    container?: HTMLDivElement | null;
    loading?: boolean;
    loadingText?: string;
    options?: TablePagination<any> | null;
    disableFloatingHeader?: boolean;
  }>(),
  {
    sortDesc: true,
    mustSort: true,
    multiSort: false,
    expanded: () => [],
    itemClass: '',
    hideDefaultFooter: false,
    container: null,
    loading: false,
    loadingText: '',
    options: () => null,
    disableFloatingHeader: false
  }
);

const rootAttrs = useAttrs();
const rootListeners = useListeners();
const frontendSettingsStore = useFrontendSettingsStore();
const { itemsPerPage: itemsPerPageFromFrontendSetting } = storeToRefs(
  frontendSettingsStore
);
const { container, options, disableFloatingHeader } = toRefs(props);

if (props.multiSort && props.mustSort) {
  logger.warn(
    'Both multi-sort and must-sort were enabled, ' +
      'check <data-table/> for more information why this might be a problem'
  );
}

const tableRef = ref<any>(null);
const cloneTableRef = ref<any>(null);
const currentPage = ref<number>(1);
const { footerProps } = useFooterProps();

const itemsPerPageUsed = computed(
  () => get(options)?.itemsPerPage ?? get(itemsPerPageFromFrontendSetting)
);

const onItemsPerPageChange = async (newValue: number) => {
  if (get(itemsPerPageUsed) === newValue) {
    return;
  }

  await frontendSettingsStore.updateSetting({
    itemsPerPage: newValue
  });
};

const scrollToTop = () => {
  const { top } = useElementBounding(tableRef);
  const { top: containerTop } = useElementBounding(container);

  const tableContainer = get(container);
  const wrapper = tableContainer ?? document.body;
  const table = get(tableRef);

  if (!table || !wrapper) {
    return;
  }

  const tableTop = get(top);
  setTimeout(() => {
    let newScrollTop: number;
    if (get(container)) {
      newScrollTop =
        tableTop + wrapper.scrollTop - get(containerTop) - table.$el.scrollTop;
    } else {
      newScrollTop = tableTop + wrapper.scrollTop - 64;
    }
    if (wrapper.scrollTop > newScrollTop) {
      wrapper.scrollTop = newScrollTop;
    }
  }, 10);
};

const pageSelectorData = (props: {
  pageStart: number;
  pageStop: number;
  itemsLength: number;
}) => {
  const itemsLength = props.itemsLength;
  const perPage = get(itemsPerPageUsed);
  const totalPage = Math.ceil(itemsLength / perPage);

  return new Array(totalPage).fill(0).map((item, index) => ({
    value: index + 1,
    text: `${index * perPage + 1} - ${Math.min(
      (index + 1) * perPage,
      itemsLength
    )}`
  }));
};

onMounted(() => {
  const optionsVal = get(options);
  if (!optionsVal) {
    return;
  }

  if (optionsVal.page) {
    set(currentPage, optionsVal.page);
  }
  if (optionsVal.itemsPerPage) {
    onItemsPerPageChange(optionsVal.itemsPerPage);
  }
});

onMounted(() => {
  if (!get(container) && !get(disableFloatingHeader)) {
    watchEffect(onCleanup => {
      const tableInstance = get(tableRef);
      const cloneEl = get(cloneTableRef);
      const tableEl = tableInstance.$el.querySelector('table');

      const newSticky = new stickyTableHeader(tableEl, cloneEl, {
        mobileBreakpoint: tableInstance.mobileBreakpoint
      });

      onCleanup(() => {
        newSticky.destroy();
      });
    });
  }
});

const { dark } = useTheme();
</script>

<template>
  <div>
    <v-data-table
      ref="tableRef"
      v-bind="rootAttrs"
      :must-sort="mustSort"
      :multi-sort="multiSort"
      :sort-desc="sortDesc"
      :items="items"
      :item-class="itemClass"
      :headers="headers"
      :expanded="expanded"
      :footer-props="footerProps"
      :page.sync="currentPage"
      :items-per-page="itemsPerPageUsed"
      :hide-default-footer="hideDefaultFooter"
      :loading="loading"
      :loading-text="loadingText"
      :options="options"
      v-on="rootListeners"
      @update:items-per-page="onItemsPerPageChange($event)"
      @update:page="scrollToTop()"
    >
      <!-- Pass on all scoped slots -->
      <template
        v-for="slot in Object.keys($scopedSlots)"
        :slot="slot"
        slot-scope="scope"
      >
        <slot
          :name="slot"
          v-bind="
            // @ts-ignore
            scope
          "
        />
      </template>

      <!-- Pass on all named slots -->
      <slot v-for="slot in Object.keys($slots)" :slot="slot" :name="slot" />

      <template #footer.page-text="footerPageTextProps">
        <div class="d-flex align-center items-page-select">
          <span>{{ t('data_table.items_no') }}</span>
          <v-select
            v-if="footerPageTextProps.itemsLength > 0"
            v-model="currentPage"
            auto
            hide-details
            :disabled="footerPageTextProps.itemsLength <= itemsPerPageUsed"
            :items="pageSelectorData(footerPageTextProps)"
            item-value="value"
            item-text="text"
          />
          <span v-else class="mr-1">{{ footerPageTextProps.itemsLength }}</span>
          <span>
            {{ t('common.of') }} {{ footerPageTextProps.itemsLength }}
          </span>
        </div>
      </template>

      <template
        v-if="!hideDefaultFooter"
        #top="{ pagination, options: opt, updateOptions }"
      >
        <v-data-footer
          v-bind="footerProps"
          :pagination="pagination"
          :options="opt"
          @update:options="updateOptions($event)"
        >
          <template #page-text="footerPageTextProps">
            <div class="d-flex align-center items-page-select">
              <span>{{ t('data_table.items_no') }}</span>
              <v-select
                v-if="footerPageTextProps.itemsLength > 0"
                v-model="currentPage"
                auto
                hide-details
                :disabled="footerPageTextProps.itemsLength <= itemsPerPageUsed"
                :items="pageSelectorData(footerPageTextProps)"
                item-value="value"
                item-text="text"
              />
              <span v-else class="mr-1">
                {{ footerPageTextProps.itemsLength }}
              </span>
              <span>
                {{ t('common.of') }} {{ footerPageTextProps.itemsLength }}
              </span>
            </div>
          </template>
        </v-data-footer>
        <v-divider />
      </template>
    </v-data-table>
    <div
      class="clone v-data-table"
      :class="dark ? 'theme--dark' : 'theme--light'"
    >
      <div class="v-data-table__wrapper clone__wrapper">
        <table ref="cloneTableRef" class="clone__table" />
        <div>
          <v-progress-linear v-if="loading" indeterminate />
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped lang="scss">
/* stylelint-disable selector-class-pattern,selector-nested-pattern,no-descending-specificity */

:deep(.v-data-table) {
  .v-data-table__expanded {
    &__content {
      background-color: var(--v-rotki-light-grey-base) !important;
      box-shadow: none !important;
    }
  }

  .v-data-table--mobile {
    .v-data-table {
      &__wrapper {
        tbody {
          .v-data-table__expanded__content,
          .table-expand-container {
            height: auto !important;
            display: block;
          }
        }
      }
    }
  }
}

.clone {
  z-index: 2;
  position: relative;

  &__wrapper {
    position: fixed;
    overflow: hidden;
  }

  &__table {
    border-spacing: 0;
    position: relative;

    :deep(.v-data-table-header) {
      background: var(--v-rotki-light-grey-base) !important;

      th {
        .v-icon {
          color: inherit !important;
        }
      }
    }

    &:empty {
      + div {
        display: none;
      }
    }
  }
}

.theme {
  &--dark {
    :deep(.v-data-table) {
      .v-data-table__expanded {
        &__content {
          background-color: var(--v-dark-lighten1) !important;
        }
      }
    }
  }
}

.items-page-select {
  display: flex;

  :deep(.v-input) {
    margin: 13px 0.5rem;
    font-size: 0.75rem;
    width: 100px;
    max-width: 100%;
    flex: 0 1 0;
    padding: 0;
    position: initial;

    .v-select__selections {
      .v-select__selection {
        overflow: visible;
        padding-right: 0.5rem;
      }
    }
  }
}

/* stylelint-enable selector-class-pattern,selector-nested-pattern,no-descending-specificity */
</style>
