import { Link } from "react-router-dom";
import BaseLayout from "./BaseLayout";
import { Button } from "@/components/ui/button";
import { useParams } from "react-router-dom";
import { useEffect } from "react";
import { useLiveRegion } from "@/components/shared/LiveRegion";
import { useTranslation } from 'react-i18next'

// Import custom hooks
import { useDatabaseInfo, useSearch, useStatistics, useViewManager } from '../hooks';

// Import components
import {
  DatabaseInfo,
  ViewToggle,
  ContentContainer,
  ResultsDisplay,
  NoResults,
  PopulationPyramid
} from '../components';

export default function DatabasePage() {
  const { baseName } = useParams<{ baseName: string }>();
  const { announce } = useLiveRegion();
  const { t } = useTranslation('common')

  // Custom hooks
  const { dbInfo, loading, error } = useDatabaseInfo(baseName);
  const { currentView, showSearchView, showStatisticsView } = useViewManager();

  const {
    searchResults,
    searching,
    error: searchError,
    searchResultsRef,
    performSearch,
    clearSearch
  } = useSearch(baseName);

  const {
    statisticsResults,
    populationPyramidData,
    loadingStatistics,
    selectedStatistic,
    error: statisticsError,
    statisticsResultsRef,
    fetchStatistics,
    clearStatistics
  } = useStatistics(baseName);

  // Handler functions
  const handleShowSearchView = () => {
    showSearchView();
    clearStatistics();
  };

  const handleShowStatisticsView = () => {
    showStatisticsView();
    clearSearch();
  };

  const currentError = error || searchError || statisticsError;

  if (loading) {
    return (
      <BaseLayout title={`GenEWeb - ${t('database.loading')}`}>
        <div className="flex justify-center items-center min-h-[400px]" role="status" aria-live="polite">
          <div className="text-center">
            <div className="text-4xl mb-4">⏳</div>
            <h2 className="text-xl">{t('database.loading')}</h2>
          </div>
        </div>
      </BaseLayout>
    );
  }

  if (currentError || !dbInfo) {
    return (
      <BaseLayout title={`GenEWeb - ${t('app.error')}`}>
        <div className="flex justify-center items-center min-h-[400px]" role="alert">
          <div className="text-center">
            <div className="text-4xl mb-4">❌</div>
            <h2 className="text-xl mb-2">{t('app.error')}</h2>
            <p className="text-muted-foreground mb-4">{currentError || ''}</p>
            <Button asChild>
              <Link to="/">{t('home.welcome')}</Link>
            </Button>
          </div>
        </div>
      </BaseLayout>
    );
  }

  // Get current results and refs based on view
  const currentResults = currentView === 'search' ? searchResults : statisticsResults;
  const currentResultsRef = currentView === 'search' ? searchResultsRef : statisticsResultsRef;
  const hasResults = currentResults.length > 0;
  const hasPopulationPyramid = populationPyramidData && selectedStatistic === 'population-pyramid';

  // Check if we should show "no results" message
  const shouldShowNoResults = currentView === 'search'
    ? (searchResults.length === 0 && !searching)
    : (statisticsResults.length === 0 && !populationPyramidData && !loadingStatistics && selectedStatistic);

  return (
    <BaseLayout
      title={`${baseName} - GenEWeb`}
      showNavbar
      navbarItems={
        <div className="flex items-center gap-4">
          <span className="text-sm opacity-90">{baseName}</span>
          <Link className="text-sm opacity-90 hover:opacity-100" to="/">{t('home.welcome')}</Link>
        </div>
      }
    >
      {/* Announce page/context */}
      <PageAnnouncer baseName={baseName!} onAnnounce={announce} />
      <DatabaseInfo dbInfo={dbInfo} baseName={baseName!} />

      <ViewToggle
        currentView={currentView}
        onShowSearch={handleShowSearchView}
        onShowStatistics={handleShowStatisticsView}
      />

      <ContentContainer
        currentView={currentView}
        onSearch={performSearch}
        onClearSearch={clearSearch}
        searching={searching}
        onSelectStatistic={fetchStatistics}
        selectedStatistic={selectedStatistic}
        loadingStatistics={loadingStatistics}
      />

      {hasResults && (
        <ResultsDisplay
          results={currentResults}
          viewType={currentView}
          selectedStatistic={selectedStatistic}
          resultsRef={currentResultsRef}
        />
      )}

      {hasPopulationPyramid && (
        <PopulationPyramid
          data={populationPyramidData}
          resultsRef={statisticsResultsRef}
        />
      )}

      {shouldShowNoResults && (
        <NoResults
          viewType={currentView}
          onNewSearch={clearSearch}
          onNewStatistic={() => {
            clearStatistics();
            showStatisticsView();
          }}
        />
      )}
    </BaseLayout>
  );
}

function PageAnnouncer({ baseName, onAnnounce }: { baseName: string; onAnnounce: (m: string) => void }) {
  useEffect(() => {
    onAnnounce(`Base ${baseName}`);
  }, [baseName, onAnnounce]);
  return null;
}
