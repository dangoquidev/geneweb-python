import React from 'react';
import { Card, CardContent } from '@/components/ui/card';
import { STATISTIC_OPTIONS } from '../../constants/statistics';

interface StatisticsOptionsProps {
  onSelectStatistic: (statisticId: string) => void;
  selectedStatistic: string | null;
  loading: boolean;
}

/**
 * Grid of available statistics to fetch for the selected base.
 * Uses STATISTIC_OPTIONS for id/label/description and reports the selection upstream.
 */
export const StatisticsOptions: React.FC<StatisticsOptionsProps> = ({
  onSelectStatistic,
  selectedStatistic,
  loading
}) => {
  return (
    <div className="space-y-4" role="region" aria-labelledby="stats-heading">
      <div className="text-center text-sm text-muted-foreground mb-6">
        <span id="stats-heading">Sélectionnez une statistique pour afficher les données correspondantes</span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4" role="list">
        {STATISTIC_OPTIONS.map((option) => (
          <Card
            key={option.id}
            className={`cursor-pointer transition-all hover:shadow-md ${
              selectedStatistic === option.id ? 'ring-2 ring-primary' : ''
            } ${loading ? 'opacity-50 pointer-events-none' : ''}`}
            onClick={() => !loading && onSelectStatistic(option.id)}
            role="button"
            aria-pressed={selectedStatistic === option.id}
            tabIndex={0}
            onKeyDown={(e) => {
              if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                if (!loading) onSelectStatistic(option.id);
              }
            }}
          >
            <CardContent className="p-4" role="listitem">
              <div className="text-center">
                <h4 className="font-medium mb-2">{option.label}</h4>
                <p className="text-sm text-muted-foreground">{option.description}</p>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {loading && (
        <div className="text-center py-4" role="status" aria-live="polite">
          <div className="text-2xl mb-2">⏳</div>
          <div className="text-sm text-muted-foreground">Chargement des statistiques...</div>
        </div>
      )}
    </div>
  );
};
