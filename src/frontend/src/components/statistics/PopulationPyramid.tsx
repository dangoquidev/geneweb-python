import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';

interface PyramidData {
  birth_year: number;
  age: number;
  male: number;
  female: number;
  unknown: number;
  total: number;
}

interface PopulationPyramidData {
  pyramid: PyramidData[];
  total_living: number;
  current_year: number;
}

interface PopulationPyramidProps {
  data: PopulationPyramidData;
  resultsRef: React.RefObject<HTMLDivElement | null>;
}

/**
 * PopulationPyramid renders a horizontal age pyramid from aggregated backend data.
 * Expects pre-aggregated buckets with male/female counts and the computed current year.
 */
export const PopulationPyramid: React.FC<PopulationPyramidProps> = ({ 
  data, 
  resultsRef 
}) => {
  const maxCount = Math.max(...data.pyramid.map(p => Math.max(p.male, p.female)));
  const barWidth = 100; // Maximum width for bars

  const getBarWidth = (count: number) => {
    if (maxCount === 0) return 0;
    return (count / maxCount) * barWidth;
  };

  return (
    <div ref={resultsRef} className="flex justify-center mb-6">
      <div className="w-full max-w-4xl">
        <Card>
          <CardHeader className="border-b border-border">
            <CardTitle className="text-center">
              📊 Pyramide des âges ({data.current_year})
            </CardTitle>
            <div className="text-center text-sm text-muted-foreground">
              Répartition par année de naissance
            </div>
          </CardHeader>
          <CardContent className="p-6">
            <div className="space-y-1 font-mono text-sm">
              {data.pyramid.map((period, index) => (
                <div key={period.birth_year} className="flex items-center justify-between min-h-[24px]">
                  {/* Birth Year */}
                  <div className="w-12 text-right text-xs text-muted-foreground">
                    {period.birth_year}
                  </div>
                  
                  {/* Male bar (left side) */}
                  <div className="flex-1 flex justify-end items-center pr-2">
                    <div className="flex items-center">
                      {period.male > 0 && (
                        <span className="text-xs mr-1 text-blue-600 font-medium">
                          {period.male}
                        </span>
                      )}
                      <div 
                        className="bg-blue-500 h-4 rounded-l"
                        style={{ width: `${getBarWidth(period.male)}px` }}
                      />
                    </div>
                  </div>
                  
                  {/* Center - Age */}
                  <div className="w-16 text-center text-xs font-medium border-x border-border py-1">
                    {period.age}
                  </div>
                  
                  {/* Female bar (right side) */}
                  <div className="flex-1 flex justify-start items-center pl-2">
                    <div className="flex items-center">
                      <div 
                        className="bg-pink-500 h-4 rounded-r"
                        style={{ width: `${getBarWidth(period.female)}px` }}
                      />
                      {period.female > 0 && (
                        <span className="text-xs ml-1 text-pink-600 font-medium">
                          {period.female}
                        </span>
                      )}
                    </div>
                  </div>
                  
                  {/* Birth Year (right) */}
                  <div className="w-12 text-left text-xs text-muted-foreground">
                    {period.birth_year}
                  </div>
                </div>
              ))}
              
              {/* Legend row */}
              <div className="flex items-center justify-between mt-4 pt-2 border-t border-border">
                <div className="w-12"></div>
                <div className="flex-1 text-center text-xs text-blue-600 font-medium">
                  M
                </div>
                <div className="w-16 text-center text-xs font-bold">
                  ÂGE
                </div>
                <div className="flex-1 text-center text-xs text-pink-600 font-medium">
                  F
                </div>
                <div className="w-12"></div>
              </div>
            </div>
            
            {/* Summary */}
            <div className="mt-6 p-4 bg-muted rounded-lg text-center">
              <div className="text-sm font-medium">
                Nombre d'individus vivants : <span className="font-bold text-primary">{data.total_living}</span>
              </div>
            </div>
            
            {/* Legend */}
            <div className="mt-4 flex justify-center gap-6 text-xs">
              <div className="flex items-center gap-2">
                <div className="w-4 h-4 bg-blue-500 rounded"></div>
                <span>Hommes</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-4 h-4 bg-pink-500 rounded"></div>
                <span>Femmes</span>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};
