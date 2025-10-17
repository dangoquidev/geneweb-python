import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { SearchForm } from '../search/SearchForm';
import { StatisticsOptions } from '../statistics/StatisticsOptions';
import type { ViewType, SearchFormData, SearchOptions } from '../../types/database';
import { useTranslation } from 'react-i18next';

interface ContentContainerProps {
  currentView: ViewType;
  onSearch: (formData: SearchFormData, options: SearchOptions) => void;
  onClearSearch: () => void;
  searching: boolean;
  onSelectStatistic: (statisticId: string) => void;
  selectedStatistic: string | null;
  loadingStatistics: boolean;
}

export const ContentContainer: React.FC<ContentContainerProps> = ({
  currentView,
  onSearch,
  onClearSearch,
  searching,
  onSelectStatistic,
  selectedStatistic,
  loadingStatistics
}) => {
  const { t } = useTranslation('common');

  return (
    <div className="flex justify-center mb-6">
      <div className="w-full max-w-5xl">
        <Card>
          <CardHeader className="border-b border-border">
            <CardTitle className="text-center">
              {currentView === 'search'
                ? `🔍 ${t('database.search')}`
                : `📊 ${t('admin.detailed_stats')}`
              }
            </CardTitle>
          </CardHeader>
          <CardContent className="p-6">
            {currentView === 'search' ? (
              <SearchForm
                onSearch={onSearch}
                onClear={onClearSearch}
                searching={searching}
              />
            ) : (
              <StatisticsOptions
                onSelectStatistic={onSelectStatistic}
                selectedStatistic={selectedStatistic}
                loading={loadingStatistics}
              />
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
};
