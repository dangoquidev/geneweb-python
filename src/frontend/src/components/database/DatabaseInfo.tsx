import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import type { DatabaseInfo as DatabaseInfoType } from '../../types/database';

interface DatabaseInfoProps {
  dbInfo: DatabaseInfoType;
  baseName: string;
}

export const DatabaseInfo: React.FC<DatabaseInfoProps> = ({ dbInfo, baseName }) => {
  return (
    <>
      {/* En-tête */}
      <div className="flex justify-center mb-6">
        <div className="w-full max-w-6xl text-center">
          <h1 className="text-3xl font-semibold mb-1 flex items-center justify-center gap-2">
            🌳 Base {baseName}
          </h1>
          <p className="text-muted-foreground">Base de données généalogique</p>
        </div>
      </div>

      {/* Statistiques */}
      <div className="flex justify-center mb-6">
        <div className="w-full max-w-3xl">
          <Card>
            <CardHeader className="border-b border-border">
              <CardTitle className="text-center">📊 Informations sur la base</CardTitle>
            </CardHeader>
            <CardContent className="p-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-center">
                <div>
                  <div className="text-2xl mb-2">👥</div>
                  <h4 className="text-xl font-bold">{dbInfo.persons.toLocaleString()}</h4>
                  <small className="text-muted-foreground">
                    {dbInfo.persons === 1 ? 'Personne' : 'Personnes'}
                  </small>
                </div>
                <div>
                  <div className="text-2xl mb-2">❤️</div>
                  <h4 className="text-xl font-bold">{dbInfo.families.toLocaleString()}</h4>
                  <small className="text-muted-foreground">
                    {dbInfo.families === 1 ? 'Famille' : 'Familles'}
                  </small>
                </div>
              </div>
              <div className="mt-4 text-sm space-y-1">
                <div><strong>Chemin:</strong> <code className="text-xs">{dbInfo.path}</code></div>
                <div><strong>Version:</strong> {dbInfo.version}</div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </>
  );
};
