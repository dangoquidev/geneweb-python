export type DatabaseInfo = {
  base_name: string;
  persons: number;
  families: number;
  path: string;
  version: string;
};

export type SearchResult = {
  id: string;
  first_name: string;
  surname: string;
  occupation: string;
  sex: string;
  birth_date: string;
  death_date: string;
};

export type ViewType = 'search' | 'statistics';

export type StatisticOption = {
  id: string;
  label: string;
};

export type SearchFormData = {
  globalSearch: string;
  firstName: string;
  surname: string;
  title: string;
  field: string;
};

export type SearchOptions = {
  oneFirstName: boolean;
  sameOrder: boolean;
  partial: boolean;
};

// Couples / families statistics
export type MarriageSpouse = {
  id: string;
  first_name: string;
  surname: string;
};

export type MarriageEntry = {
  family_id: string;
  marriage_date: string;
  marriage_place: string;
  husband: MarriageSpouse | null;
  wife: MarriageSpouse | null;
  year: number;
};

export type OldestCoupleSpouse = MarriageSpouse & {
  age: number;
  birth_date: string;
};

export type OldestCoupleEntry = {
  family_id: string;
  husband: OldestCoupleSpouse;
  wife: OldestCoupleSpouse;
  combined_age: number;
  marriage_date: string;
};

export type StatisticResult = SearchResult | MarriageEntry | OldestCoupleEntry;
