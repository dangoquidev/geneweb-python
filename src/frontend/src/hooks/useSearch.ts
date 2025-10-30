import { useState, useRef } from 'react';
import type { SearchResult, SearchFormData, SearchOptions } from '../types/database';

/**
 * Hook to perform free-text person search within a specific base.
 * Builds a query from multiple form fields and returns matching people.
 */
export const useSearch = (baseName: string | undefined) => {
  const [searchResults, setSearchResults] = useState<SearchResult[]>([]);
  const [searching, setSearching] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const searchResultsRef = useRef<HTMLDivElement>(null);

  const performSearch = async (formData: SearchFormData, options: SearchOptions) => {
    if (!baseName) return;

    // Build search query from all fields
    const searchTerms = [];
    if (formData.globalSearch.trim()) searchTerms.push(formData.globalSearch.trim());
    if (formData.firstName.trim()) searchTerms.push(formData.firstName.trim());
    if (formData.surname.trim()) searchTerms.push(formData.surname.trim());
    if (formData.title.trim()) searchTerms.push(formData.title.trim());
    if (formData.field.trim()) searchTerms.push(formData.field.trim());

    if (searchTerms.length === 0) return;

    const query = searchTerms.join(' ');

    setSearching(true);
    setError(null);

    try {
      const response = await fetch(`/api/databases/${encodeURIComponent(baseName)}/search?q=${encodeURIComponent(query)}`);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      // The new route returns an array directly, not {results: [...]}
      const results = Array.isArray(data) ? data : (data.results || []);
      setSearchResults(results);

      // Scroll to results after a short delay
      if (results && results.length > 0) {
        setTimeout(() => {
          searchResultsRef.current?.scrollIntoView({
            behavior: 'smooth',
            block: 'start'
          });
        }, 100);
      }
    } catch (err) {
      console.error('Error searching:', err);
      setError(err instanceof Error ? err.message : 'Search failed');
    } finally {
      setSearching(false);
    }
  };

  const clearSearch = () => {
    setSearchResults([]);
    setError(null);
  };

  return {
    searchResults,
    searching,
    error,
    searchResultsRef,
    performSearch,
    clearSearch
  };
};
