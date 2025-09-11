import React, { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Checkbox } from '@/components/ui/checkbox';
import type { SearchFormData, SearchOptions } from '../../types/database';

interface SearchFormProps {
  onSearch: (formData: SearchFormData, options: SearchOptions) => void;
  onClear: () => void;
  searching: boolean;
}

export const SearchForm: React.FC<SearchFormProps> = ({ onSearch, onClear, searching }) => {
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
    <form onSubmit={handleSubmit} className="space-y-4">
      {/* Global search field */}
      <div>
        <label className="block text-sm font-medium mb-2">
          Recherche globale (individu, nom, nom public, alias, clé)
        </label>
        <Input
          type="search"
          placeholder="Recherche dans tous les champs..."
          value={formData.globalSearch}
          onChange={(e) => updateFormData('globalSearch', e.target.value)}
          autoFocus
        />
      </div>

      {/* Name fields */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium mb-2">Prénom</label>
          <Input
            type="text"
            placeholder="Prénom(s)"
            value={formData.firstName}
            onChange={(e) => updateFormData('firstName', e.target.value)}
          />
        </div>
        <div>
          <label className="block text-sm font-medium mb-2">Nom de famille</label>
          <Input
            type="text"
            placeholder="Nom de famille"
            value={formData.surname}
            onChange={(e) => updateFormData('surname', e.target.value)}
          />
        </div>
      </div>

      {/* Title and field */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium mb-2">Titre</label>
          <Input
            type="text"
            placeholder="Titre (M., Mme, Dr...)"
            value={formData.title}
            onChange={(e) => updateFormData('title', e.target.value)}
          />
        </div>
        <div>
          <label className="block text-sm font-medium mb-2">Domaine</label>
          <Input
            type="text"
            placeholder="Profession, domaine..."
            value={formData.field}
            onChange={(e) => updateFormData('field', e.target.value)}
          />
        </div>
      </div>

      {/* Search options */}
      <div className="border-t pt-4">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="space-y-3">
            <h4 className="text-sm font-medium">Options de recherche</h4>
            <div className="space-y-2">
              <label className="flex items-center space-x-2 cursor-pointer">
                <Checkbox
                  checked={options.oneFirstName}
                  onCheckedChange={(checked) => updateOptions('oneFirstName', checked === true)}
                />
                <span className="text-sm">Un seul prénom</span>
              </label>
              <label className="flex items-center space-x-2 cursor-pointer">
                <Checkbox
                  checked={options.sameOrder}
                  onCheckedChange={(checked) => updateOptions('sameOrder', checked === true)}
                />
                <span className="text-sm">Même ordre</span>
              </label>
              <label className="flex items-center space-x-2 cursor-pointer">
                <Checkbox
                  checked={options.partial}
                  onCheckedChange={(checked) => updateOptions('partial', checked === true)}
                />
                <span className="text-sm">Recherche partielle</span>
              </label>
            </div>
          </div>
          <div className="flex flex-col justify-end space-y-2">
            <Button type="submit" disabled={searching} className="w-full">
              {searching ? "Recherche en cours..." : "🔍 Rechercher"}
            </Button>
            <Button type="button" variant="outline" onClick={handleClear} className="w-full">
              🗑️ Effacer
            </Button>
          </div>
        </div>
      </div>

      <div className="text-center text-xs text-muted-foreground">
        Remplissez un ou plusieurs champs pour effectuer une recherche
      </div>
    </form>
  );
};
