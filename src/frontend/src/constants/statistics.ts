import type { StatisticOption } from '../types/database';

export const STATISTIC_OPTIONS: StatisticOption[] = [
  { 
    id: 'latest-births', 
    label: '🎂 20 dernières naissances', 
    description: 'Les 20 personnes nées le plus récemment' 
  },
  { 
    id: 'latest-deaths', 
    label: '✝️ 20 derniers décès', 
    description: 'Les 20 personnes décédées le plus récemment' 
  },
  { 
    id: 'latest-marriages', 
    label: '💒 20 derniers mariages', 
    description: 'Les 20 mariages les plus récents' 
  },
  { 
    id: 'oldest-couples', 
    label: '👫 20 couples les plus âgés', 
    description: 'Les 20 couples les plus âgés encore en vie et mariés' 
  },
  { 
    id: 'oldest-people', 
    label: '👴 20 personnes les plus âgées', 
    description: 'Les 20 personnes les plus âgées encore en vie' 
  },
  { 
    id: 'longest-lived', 
    label: '⏳ 20 qui ont vécu le plus longtemps', 
    description: 'Les 20 personnes ayant vécu le plus longtemps' 
  },
  { 
    id: 'population-pyramid', 
    label: '📊 Pyramide des âges', 
    description: 'Répartition de la population par âge et sexe' 
  }
];
