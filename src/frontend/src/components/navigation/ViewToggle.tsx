import React from 'react';
import { Link } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import type { ViewType } from '../../types/database';

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
  return (
    <div className="flex justify-center mb-6">
      <div className="w-full max-w-5xl">
        <Card>
          <CardHeader className="border-b border-border">
            <CardTitle className="text-center">🛠️ Outils de navigation</CardTitle>
          </CardHeader>
          <CardContent className="p-6">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3 mb-4">
              <Button 
                variant={currentView === 'search' ? 'default' : 'outline'} 
                onClick={onShowSearch}
              >
                🔍 Nouvelle recherche
              </Button>
              <Button 
                variant={currentView === 'statistics' ? 'default' : 'outline'} 
                onClick={onShowStatistics}
              >
                📊 Statistiques détaillées
              </Button>
              <Button variant="outline" asChild>
                <Link to="/">🏠 Retour aux bases</Link>
              </Button>
            </div>
            <hr className="my-4 border-border" />
            <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
              <Button variant="outline" size="sm" disabled>📅 Calendrier</Button>
              <Button variant="outline" size="sm" disabled>🎂 Anniversaires</Button>
              <Button variant="outline" size="sm" disabled>🗺️ Lieux</Button>
              <Button variant="outline" size="sm" disabled>⚙️ Configuration</Button>
            </div>
            <div className="text-center text-sm text-muted-foreground mt-3">
              Certaines fonctionnalités sont en cours de développement
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};
