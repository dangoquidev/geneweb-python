import { useState } from 'react';
import type { ViewType } from '../types/database';

export const useViewManager = () => {
  const [currentView, setCurrentView] = useState<ViewType>('search');

  const showSearchView = () => {
    setCurrentView('search');
  };

  const showStatisticsView = () => {
    setCurrentView('statistics');
  };

  return {
    currentView,
    showSearchView,
    showStatisticsView
  };
};
