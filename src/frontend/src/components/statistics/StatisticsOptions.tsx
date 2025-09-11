import React from 'react';
import { Card, CardContent } from '@/components/ui/card';
import { STATISTIC_OPTIONS } from '../../constants/statistics';

interface StatisticsOptionsProps {
  onSelectStatistic: (statisticId: string) => void;
  selectedStatistic: string | null;
  loading: boolean;
}

export const StatisticsOptions: React.FC<StatisticsOptionsProps> = ({ 
  onSelectStatistic, 
  selectedStatistic, 
  loading 
}) => {
  return (
    <div className="space-y-4">
      <div className="text-center text-sm text-muted-foreground mb-6">
        Sélectionnez une statistique pour afficher les données correspondantes
      </div>
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {STATISTIC_OPTIONS.map((option) => (
          <Card 
            key={option.id} 
            className={`cursor-pointer transition-all hover:shadow-md ${
              selectedStatistic === option.id ? 'ring-2 ring-primary' : ''
            } ${loading ? 'opacity-50 pointer-events-none' : ''}`}
            onClick={() => !loading && onSelectStatistic(option.id)}
          >
            <CardContent className="p-4">
              <div className="text-center">
                <h4 className="font-medium mb-2">{option.label}</h4>
                <p className="text-sm text-muted-foreground">{option.description}</p>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
      
      {loading && (
        <div className="text-center py-4">
          <div className="text-2xl mb-2">⏳</div>
          <div className="text-sm text-muted-foreground">Chargement des statistiques...</div>
        </div>
      )}
    </div>
  );
};
