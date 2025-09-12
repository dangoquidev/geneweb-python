import React from 'react';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import type { ViewType } from '../../types/database';

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
  const isSearch = viewType === 'search';

  return (
    <div className="flex justify-center mb-6">
      <div className="w-full max-w-3xl">
        <Card>
          <CardContent className="p-8 text-center">
            <div className="text-4xl mb-4">{isSearch ? '🔍' : '📊'}</div>
            <h3 className="text-lg font-medium mb-2">
              {isSearch ? 'Aucun résultat trouvé' : 'Aucune donnée disponible'}
            </h3>
            <p className="text-muted-foreground mb-4">
              {isSearch 
                ? 'Votre recherche n\'a donné aucun résultat. Essayez de :'
                : 'Cette statistique n\'a retourné aucune donnée pour cette base.'
              }
            </p>
            {isSearch && (
              <div className="text-sm text-muted-foreground space-y-1">
                <div>• Vérifier l'orthographe</div>
                <div>• Utiliser moins de mots-clés</div>
                <div>• Essayer des variantes du nom</div>
                <div>• Activer la recherche partielle</div>
              </div>
            )}
            <Button 
              className="mt-4" 
              onClick={isSearch ? onNewSearch : onNewStatistic}
            >
              {isSearch ? '🗑️ Nouvelle recherche' : '📊 Choisir une autre statistique'}
            </Button>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};
