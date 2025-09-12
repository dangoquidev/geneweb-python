import { useState, useRef } from 'react';
import type { StatisticResult, MarriageEntry, OldestCoupleEntry } from '../types/database';

export const useStatistics = (baseName: string | undefined) => {
  const [statisticsResults, setStatisticsResults] = useState<StatisticResult[]>([]);
  const [populationPyramidData, setPopulationPyramidData] = useState<any>(null);
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
      
      // Handle population pyramid differently
      if (statisticType === 'population-pyramid') {
        setPopulationPyramidData(data.data || data.results);
        setStatisticsResults([]);
      } else {
        const results = (data.results || []) as (MarriageEntry | OldestCoupleEntry | any)[];
        setStatisticsResults(results);
        setPopulationPyramidData(null);
      }
      
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
    setPopulationPyramidData(null);
    setSelectedStatistic(null);
    setError(null);
  };

  return {
    statisticsResults,
    populationPyramidData,
    loadingStatistics,
    selectedStatistic,
    error,
    statisticsResultsRef,
    fetchStatistics,
    clearStatistics
  };
};
