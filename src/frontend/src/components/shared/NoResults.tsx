import React from 'react';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import type { ViewType } from '../../types/database';
import { useTranslation } from 'react-i18next'

interface NoResultsProps {
  viewType: ViewType;
  onNewSearch: () => void;
  onNewStatistic: () => void;
}

export const NoResults: React.FC<NoResultsProps> = ({
  viewType,
  onNewSearch,
  onNewStatistic
}) => {
  const { t } = useTranslation('common')
  const isSearch = viewType === 'search';

  return (
    <div className="flex justify-center mb-6" role="status" aria-live="polite">
      <div className="w-full max-w-3xl">
        <Card role="region" aria-labelledby="noresults-heading">
          <CardContent className="p-8 text-center">
            <div className="text-4xl mb-4">{isSearch ? '🔍' : '📊'}</div>
            <h3 id="noresults-heading" className="text-lg font-medium mb-2">
              {t('database.no_results')}
            </h3>
            <p className="text-muted-foreground mb-4"></p>
            {isSearch && (
              <div className="text-sm text-muted-foreground space-y-1">
                <div>• {t('database.refine_search')}</div>
              </div>
            )}
            <Button
              className="mt-4"
              onClick={isSearch ? onNewSearch : onNewStatistic}
              aria-label={isSearch ? t('admin.new_search') : t('admin.choose_other_stat')}
            >
              {isSearch ? '🔁' : '📊'}
            </Button>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};
