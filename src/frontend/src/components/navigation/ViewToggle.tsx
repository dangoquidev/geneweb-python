import React from 'react';
import { Link } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import type { ViewType } from '../../types/database';
import { useTranslation } from 'react-i18next'

interface ViewToggleProps {
  currentView: ViewType;
  onShowSearch: () => void;
  onShowStatistics: () => void;
}

export const ViewToggle: React.FC<ViewToggleProps> = ({
  currentView,
  onShowSearch,
  onShowStatistics
}) => {
  const { t } = useTranslation('common')
  return (
    <div className="flex justify-center mb-6">
      <div className="w-full max-w-5xl">
        <Card role="region" aria-labelledby="nav-tools-heading">
          <CardHeader className="border-b border-border">
            <CardTitle className="text-center" id="nav-tools-heading">🛠️ {t('admin.nav_tools')}</CardTitle>
          </CardHeader>
          <CardContent className="p-6">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3 mb-4">
              <Button
                variant={currentView === 'search' ? 'default' : 'outline'}
                onClick={onShowSearch}
                aria-pressed={currentView === 'search'}
              >
                🔍 {t('database.search')}
              </Button>
              <Button
                variant={currentView === 'statistics' ? 'default' : 'outline'}
                onClick={onShowStatistics}
                aria-pressed={currentView === 'statistics'}
              >
                📊 {t('admin.detailed_stats')}
              </Button>
              <Button variant="outline" asChild>
                <Link to="/">🏠 {t('admin.back_to_bases')}</Link>
              </Button>
            </div>
            <hr className="my-4 border-border" />
            <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
              <Button variant="outline" size="sm" disabled aria-disabled="true">📅 Calendrier</Button>
              <Button variant="outline" size="sm" disabled aria-disabled="true">🎂 Anniversaires</Button>
              <Button variant="outline" size="sm" disabled aria-disabled="true">🗺️ Lieux</Button>
              <Button variant="outline" size="sm" disabled aria-disabled="true">⚙️ Configuration</Button>
            </div>
            <div className="text-center text-sm text-muted-foreground mt-3">
              {t('admin.in_progress')}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};
