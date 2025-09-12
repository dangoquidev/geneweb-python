import { useState, useEffect } from 'react';
import type { DatabaseInfo } from '../types/database';

/**
 * Hook to fetch basic database metadata: persons, families, path, version.
 * Fetches on base change and exposes loading/error states.
 */
export const useDatabaseInfo = (baseName: string | undefined) => {
  const [dbInfo, setDbInfo] = useState<DatabaseInfo | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!baseName) return;
    
    const fetchDatabaseInfo = async () => {
      try {
        const response = await fetch(`/api/${baseName}/info`);
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();
        setDbInfo(data);
        setError(null);
      } catch (err) {
        console.error('Error fetching database info:', err);
        setError(err instanceof Error ? err.message : 'Failed to fetch database info');
      } finally {
        setLoading(false);
      }
    };

    fetchDatabaseInfo();
  }, [baseName]);

  return { dbInfo, loading, error };
};
