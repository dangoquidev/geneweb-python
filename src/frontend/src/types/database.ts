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
  description: string;
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
