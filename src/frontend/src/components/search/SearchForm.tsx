import React, { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Checkbox } from '@/components/ui/checkbox';
import type { SearchFormData, SearchOptions } from '../../types/database';
import { useTranslation } from 'react-i18next';

interface SearchFormProps {
  onSearch: (formData: SearchFormData, options: SearchOptions) => void;
  onClear: () => void;
  searching: boolean;
}

export const SearchForm: React.FC<SearchFormProps> = ({ onSearch, onClear, searching }) => {
  const { t } = useTranslation('common');

  // Search form fields
  const [formData, setFormData] = useState<SearchFormData>({
    globalSearch: '',
    firstName: '',
    surname: '',
    title: '',
    field: ''
  });

  // Search options
  const [options, setOptions] = useState<SearchOptions>({
    oneFirstName: false,
    sameOrder: false,
    partial: true
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSearch(formData, options);
  };

  const handleClear = () => {
    setFormData({
      globalSearch: '',
      firstName: '',
      surname: '',
      title: '',
      field: ''
    });
    setOptions({
      oneFirstName: false,
      sameOrder: false,
      partial: true
    });
    onClear();
  };

  const updateFormData = (field: keyof SearchFormData, value: string) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  const updateOptions = (field: keyof SearchOptions, value: boolean) => {
    setOptions(prev => ({ ...prev, [field]: value }));
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4" aria-labelledby="search-form-title">
      {/* Global search field */}
      <div>
        <h3 id="search-form-title" className="sr-only">{t('search.form_title')}</h3>
        <label className="block text-sm font-medium mb-2" htmlFor="global-search">
          {t('search.global_search')}
        </label>
        <Input
          type="search"
          placeholder={t('search.search_all_fields')}
          value={formData.globalSearch}
          onChange={(e) => updateFormData('globalSearch', e.target.value)}
          autoFocus
          id="global-search"
        />
      </div>

      {/* Name fields */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium mb-2" htmlFor="first-name">{t('search.first_name')}</label>
          <Input
            type="text"
            placeholder={t('search.first_names_placeholder')}
            value={formData.firstName}
            onChange={(e) => updateFormData('firstName', e.target.value)}
            disabled={true}
            id="first-name"
            aria-disabled="true"
          />
        </div>
        <div>
          <label className="block text-sm font-medium mb-2" htmlFor="surname">{t('search.surname')}</label>
          <Input
            type="text"
            placeholder={t('search.surname_placeholder')}
            value={formData.surname}
            onChange={(e) => updateFormData('surname', e.target.value)}
            disabled={true}
            id="surname"
            aria-disabled="true"
          />
        </div>
      </div>

      {/* Title and field */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium mb-2" htmlFor="title">{t('search.title')}</label>
          <Input
            type="text"
            placeholder={t('search.title_placeholder')}
            value={formData.title}
            onChange={(e) => updateFormData('title', e.target.value)}
            disabled={true}
            id="title"
            aria-disabled="true"
          />
        </div>
        <div>
          <label className="block text-sm font-medium mb-2" htmlFor="field">{t('search.field')}</label>
          <Input
            type="text"
            placeholder={t('search.field_placeholder')}
            value={formData.field}
            onChange={(e) => updateFormData('field', e.target.value)}
            disabled={true}
            id="field"
            aria-disabled="true"
          />
        </div>
      </div>

      {/* Search options */}
      <div className="border-t pt-4">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="space-y-3">
            <h4 className="text-sm font-medium">{t('search.search_options')}</h4>
            <div className="space-y-2" role="group" aria-labelledby="search-options-heading">
              <h4 id="search-options-heading" className="sr-only">{t('search.search_options')}</h4>
              <label className="flex items-center space-x-2 cursor-pointer">
                <Checkbox
                  checked={options.oneFirstName}
                  onCheckedChange={(checked) => updateOptions('oneFirstName', checked === true)}
                  disabled={true}
                />
                <span className="text-sm">{t('search.one_first_name')}</span>
              </label>
              <label className="flex items-center space-x-2 cursor-pointer">
                <Checkbox
                  checked={options.sameOrder}
                  onCheckedChange={(checked) => updateOptions('sameOrder', checked === true)}
                  disabled={true}
                />
                <span className="text-sm">{t('search.same_order')}</span>
              </label>
              <label className="flex items-center space-x-2 cursor-pointer">
                <Checkbox
                  checked={options.partial}
                  onCheckedChange={(checked) => updateOptions('partial', checked === true)}
                  disabled={true}
                />
                <span className="text-sm">{t('search.partial_search')}</span>
              </label>
            </div>
          </div>
          <div className="flex flex-col justify-end space-y-2">
            <Button type="submit" disabled={searching} className="w-full" aria-busy={searching} aria-live="polite">
              {searching ? t('search.searching') : `🔍 ${t('search.search_button')}`}
            </Button>
            <Button type="button" variant="outline" onClick={handleClear} className="w-full">
              🗑️ {t('search.clear')}
            </Button>
          </div>
        </div>
      </div>

      <div className="text-center text-xs text-muted-foreground">
        {t('search.fill_fields_hint')}
      </div>
    </form>
  );
};
