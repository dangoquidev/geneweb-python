import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import type { SearchResult, ViewType, MarriageEntry, OldestCoupleEntry, StatisticResult } from '../../types/database';
import { STATISTIC_OPTIONS } from '../../constants/statistics';

interface ResultsDisplayProps {
  results: StatisticResult[];
  viewType: ViewType;
  selectedStatistic?: string | null;
  resultsRef: React.RefObject<HTMLDivElement | null>;
}

/**
 * Generic results renderer for both search and statistics views.
 * - Person results: shows identity + birth/death/occupation
 * - Couple results: for latest-marriages and oldest-couples
 */
export const ResultsDisplay: React.FC<ResultsDisplayProps> = ({ 
  results, 
  viewType, 
  selectedStatistic,
  resultsRef 
}) => {
  const getTitle = () => {
    if (viewType === 'search') {
      return `📋 Résultats de recherche (${results.length})`;
    }
    
    const selectedOption = STATISTIC_OPTIONS.find(opt => opt.id === selectedStatistic);
    return `📊 ${selectedOption?.label || 'Statistiques'} (${results.length})`;
  };

  const showLimitMessage = results.length >= 50;

  const isCoupleStat = selectedStatistic === 'latest-marriages' || selectedStatistic === 'oldest-couples';

  const renderPerson = (person: SearchResult) => (
    <Card key={person.id} className="border-l-4 border-l-primary hover:shadow-md transition-shadow">
      <CardContent className="p-4">
        <div className="flex items-start justify-between">
          <div className="flex items-start gap-3 flex-1">
            <Badge variant={person.sex === 'M' ? 'default' : 'destructive'} className="mt-0.5">
              {person.sex === 'M' ? '♂️' : '♀️'}
            </Badge>
            <div className="flex-1">
              <h5 className="font-semibold text-lg mb-1">
                {person.first_name} {person.surname}
              </h5>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-2 text-sm text-muted-foreground">
                {person.birth_date && (
                  <div className="flex items-center gap-1">
                    <span>🎂</span>
                    <span>Né{person.sex === 'F' ? 'e' : ''} le {person.birth_date}</span>
                  </div>
                )}
                {person.death_date && (
                  <div className="flex items-center gap-1">
                    <span>✝️</span>
                    <span>Décédé{person.sex === 'F' ? 'e' : ''} le {person.death_date}</span>
                  </div>
                )}
                {person.occupation && (
                  <div className="flex items-center gap-1 md:col-span-2">
                    <span>💼</span>
                    <span>{person.occupation}</span>
                  </div>
                )}
              </div>
            </div>
          </div>
          {/* <div className="text-right">
            <div className="text-xs text-muted-foreground mb-2">ID: {person.id}</div>
            <Button size="sm" variant="outline" disabled>
              👁️ Voir la fiche
            </Button>
          </div> */}
        </div>
      </CardContent>
    </Card>
  );

  const renderCouple = (entry: MarriageEntry | OldestCoupleEntry, index: number) => {
    const isOldest = 'combined_age' in entry;
    const husband = (entry as any).husband;
    const wife = (entry as any).wife;
    const marriageDate = (entry as any).marriage_date;
    const marriagePlace = (entry as any).marriage_place;
    return (
      <Card key={(entry as any).family_id || index} className="border-l-4 border-l-primary hover:shadow-md transition-shadow">
        <CardContent className="p-4">
          <div className="flex items-start justify-between">
            <div className="flex items-start gap-3 flex-1">
              <Badge variant={'default'} className="mt-0.5">👫</Badge>
              <div className="flex-1">
                <h5 className="font-semibold text-lg mb-1">
                  {(husband ? `${husband.first_name} ${husband.surname}` : 'Inconnu')} & { (wife ? `${wife.first_name} ${wife.surname}` : 'Inconnue')}
                </h5>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-2 text-sm text-muted-foreground">
                  {marriageDate && (
                    <div className="flex items-center gap-1">
                      <span>💒</span>
                      <span>Mariage: {marriageDate}{marriagePlace ? `, ${marriagePlace}` : ''}</span>
                    </div>
                  )}
                  {isOldest && (
                    <div className="flex items-center gap-1">
                      <span>🎂</span>
                      <span>Âges: {(entry as OldestCoupleEntry).husband.age} + {(entry as OldestCoupleEntry).wife.age} = {(entry as OldestCoupleEntry).combined_age}</span>
                    </div>
                  )}
                </div>
              </div>
            </div>
            {/* <div className="text-right">
              <div className="text-xs text-muted-foreground mb-2">Famille: {(entry as any).family_id}</div>
              <Button size="sm" variant="outline" disabled>
                👁️ Voir la famille
              </Button>
            </div> */}
          </div>
        </CardContent>
      </Card>
    );
  };

  return (
    <div ref={resultsRef} className="flex justify-center mb-6">
      <div className="w-full max-w-5xl">
        <Card>
          <CardHeader className="border-b border-border">
            <CardTitle className="text-center">
              {getTitle()}
            </CardTitle>
            <div className="text-center text-sm text-muted-foreground">
              {showLimitMessage && "Seuls les 50 premiers résultats sont affichés"}
            </div>
          </CardHeader>
          <CardContent className="p-4">
            <div className="space-y-3">
              {results.map((item, idx) =>
                isCoupleStat
                  ? renderCouple(item as MarriageEntry | OldestCoupleEntry, idx)
                  : renderPerson(item as SearchResult)
              )}
            </div>
            
            {showLimitMessage && (
              <div className="mt-4 p-3 bg-blue-50 dark:bg-blue-950/20 rounded-lg text-center text-sm">
                <div className="text-blue-700 dark:text-blue-300">
                  ℹ️ Seuls les 50 premiers résultats sont affichés. 
                  {viewType === 'search' ? 'Affinez votre recherche pour des résultats plus précis.' : ''}
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
};
