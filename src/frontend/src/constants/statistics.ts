import type { StatisticOption } from '../types/database';

export const STATISTIC_OPTIONS: StatisticOption[] = [
  { 
    id: 'latest-births', 
    label: '🎂 20 dernières naissances'
  },
  { 
    id: 'latest-deaths', 
    label: '✝️ 20 derniers décès'
  },
  { 
    id: 'latest-marriages', 
    label: '💒 20 derniers mariages'
  },
  { 
    id: 'oldest-couples', 
    label: '👫 20 couples les plus âgés'
  },
  { 
    id: 'oldest-people', 
    label: '👴 20 personnes les plus âgées'
  },
  { 
    id: 'longest-lived', 
    label: '⏳ 20 qui ont vécu le plus longtemps'
  },
  { 
    id: 'population-pyramid', 
    label: '📊 Pyramide des âges'
  }
];
