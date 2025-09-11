import { useState, useRef } from 'react';
import type { SearchResult } from '../types/database';

export const useStatistics = (baseName: string | undefined) => {
  const [statisticsResults, setStatisticsResults] = useState<SearchResult[]>([]);
  const [loadingStatistics, setLoadingStatistics] = useState(false);
  const [selectedStatistic, setSelectedStatistic] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const statisticsResultsRef = useRef<HTMLDivElement>(null);

  const fetchStatistics = async (statisticType: string) => {
    if (!baseName) return;

    setSelectedStatistic(statisticType);
    setLoadingStatistics(true);
    setError(null);
    
    try {
      const response = await fetch(`/api/${baseName}/statistics/${statisticType}`);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      setStatisticsResults(data.results || []);
      
      // Scroll to results after a short delay
      setTimeout(() => {
        statisticsResultsRef.current?.scrollIntoView({ 
          behavior: 'smooth',
          block: 'start'
        });
      }, 100);
    } catch (err) {
      console.error('Error fetching statistics:', err);
      setError(err instanceof Error ? err.message : 'Statistics failed');
    } finally {
      setLoadingStatistics(false);
    }
  };

  const clearStatistics = () => {
    setStatisticsResults([]);
    setSelectedStatistic(null);
    setError(null);
  };

  return {
    statisticsResults,
    loadingStatistics,
    selectedStatistic,
    error,
    statisticsResultsRef,
    fetchStatistics,
    clearStatistics
  };
};
