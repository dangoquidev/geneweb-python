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

            {/* Tools section */}
            <div className="mb-4">
              <h3 className="text-sm font-medium text-center mb-3">{t('tools.title')}</h3>
              <div className="flex flex-wrap justify-center gap-2">
                <Button variant="outline" size="sm" onClick={() => alert('Add notes')}>{t('tools.add_notes')}</Button>
                <Button variant="outline" size="sm" onClick={() => alert('Anniversaries')}>{t('tools.anniversaries')}</Button>
                <Button variant="outline" size="sm" onClick={() => alert('Places/surname')}>{t('tools.places_surname')}</Button>
                <Button variant="outline" size="sm" onClick={() => alert('Calendars')}>{t('tools.calendars')}</Button>
                <Button variant="outline" size="sm" onClick={() => alert('Configuration')}>{t('tools.configuration')}</Button>
                <Button variant="outline" size="sm" onClick={() => alert('Add note')}>{t('tools.add_note')}</Button>
                <Button variant="outline" size="sm" onClick={() => alert('Add family')}>{t('tools.add_family')}</Button>
              </div>
            </div>

            <hr className="my-4 border-border" />

            {/* Books section */}
            <div>
              <h3 className="text-sm font-medium text-center mb-3">{t('books.title')}</h3>
              <div className="grid grid-cols-3 md:grid-cols-5 gap-2">
                <Button variant="outline" size="sm" onClick={() => alert('First names')}>{t('books.first_names')}</Button>
                <Button variant="outline" size="sm" onClick={() => alert('Surnames')}>{t('books.surnames')}</Button>
                <Button variant="outline" size="sm" onClick={() => alert('Public names')}>{t('books.public_names')}</Button>
                <Button variant="outline" size="sm" onClick={() => alert('Qualifiers')}>{t('books.qualifiers')}</Button>
                <Button variant="outline" size="sm" onClick={() => alert('Aliases')}>{t('books.aliases')}</Button>
                <Button variant="outline" size="sm" onClick={() => alert('Occupations')}>{t('books.occupations')}</Button>
                <Button variant="outline" size="sm" onClick={() => alert('Places')}>{t('books.places')}</Button>
                <Button variant="outline" size="sm" onClick={() => alert('Sources')}>{t('books.sources')}</Button>
                <Button variant="outline" size="sm" onClick={() => alert('Titles')}>{t('books.titles')}</Button>
                <Button variant="outline" size="sm" onClick={() => alert('Domains')}>{t('books.domains')}</Button>
              </div>
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
