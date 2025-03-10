import { z } from 'zod';
import {
  type MatchedKeyword,
  type SearchMatcher,
  assetDeserializer,
  assetSuggestions,
  dateDeserializer,
  dateSerializer,
  dateValidator
} from '@/types/filtering';
import { MovementCategory } from '@/types/history/asset-movements';

enum AssetMovementFilterKeys {
  LOCATION = 'location',
  ACTION = 'action',
  ASSET = 'asset',
  START = 'start',
  END = 'end'
}

enum AssetMovementFilterValueKeys {
  LOCATION = 'location',
  ACTION = 'action',
  ASSET = 'asset',
  START = 'fromTimestamp',
  END = 'toTimestamp'
}

export type Matcher = SearchMatcher<
  AssetMovementFilterKeys,
  AssetMovementFilterValueKeys
>;
export type Filters = MatchedKeyword<AssetMovementFilterValueKeys>;

export const useAssetMovementFilters = () => {
  const filters: Ref<Filters> = ref({});

  const locationsStore = useHistoryStore();
  const { associatedLocations } = storeToRefs(locationsStore);
  const { dateInputFormat } = storeToRefs(useFrontendSettingsStore());
  const { assetSearch } = useAssetInfoApi();
  const { assetInfo } = useAssetInfoRetrieval();
  const { t } = useI18n();

  const matchers: ComputedRef<Matcher[]> = computed(
    () =>
      [
        {
          key: AssetMovementFilterKeys.ASSET,
          keyValue: AssetMovementFilterValueKeys.ASSET,
          description: t('deposit_withdrawals.filter.asset'),
          asset: true,
          suggestions: assetSuggestions(assetSearch),
          deserializer: assetDeserializer(assetInfo)
        },
        {
          key: AssetMovementFilterKeys.ACTION,
          keyValue: AssetMovementFilterValueKeys.ACTION,
          description: t('deposit_withdrawals.filter.action'),
          string: true,
          suggestions: () => MovementCategory.options,
          validate: type =>
            (MovementCategory.options as string[]).includes(type)
        },
        {
          key: AssetMovementFilterKeys.START,
          keyValue: AssetMovementFilterValueKeys.START,
          description: t('deposit_withdrawals.filter.start_date'),
          string: true,
          hint: t('deposit_withdrawals.filter.date_hint', {
            format: getDateInputISOFormat(get(dateInputFormat))
          }),
          suggestions: () => [],
          validate: dateValidator(dateInputFormat),
          serializer: dateSerializer(dateInputFormat),
          deserializer: dateDeserializer(dateInputFormat)
        },
        {
          key: AssetMovementFilterKeys.END,
          keyValue: AssetMovementFilterValueKeys.END,
          description: t('deposit_withdrawals.filter.end_date'),
          hint: t('deposit_withdrawals.filter.date_hint', {
            format: getDateInputISOFormat(get(dateInputFormat))
          }),
          string: true,
          suggestions: () => [],
          validate: dateValidator(dateInputFormat),
          serializer: dateSerializer(dateInputFormat),
          deserializer: dateDeserializer(dateInputFormat)
        },
        {
          key: AssetMovementFilterKeys.LOCATION,
          keyValue: AssetMovementFilterValueKeys.LOCATION,
          description: t('deposit_withdrawals.filter.location'),
          string: true,
          suggestions: () => get(associatedLocations),
          validate: location =>
            get(associatedLocations).includes(location as any)
        }
      ] satisfies Matcher[]
  );

  const updateFilter = (newFilters: Filters) => {
    set(filters, newFilters);
  };

  const OptionalString = z.string().optional();
  const RouteFilterSchema = z.object({
    [AssetMovementFilterValueKeys.LOCATION]: OptionalString,
    [AssetMovementFilterValueKeys.ACTION]: OptionalString,
    [AssetMovementFilterValueKeys.ASSET]: OptionalString,
    [AssetMovementFilterValueKeys.START]: OptionalString,
    [AssetMovementFilterValueKeys.END]: OptionalString
  });

  return {
    filters,
    matchers,
    updateFilter,
    RouteFilterSchema
  };
};
