import { useTranslation } from 'react-i18next'

export default function LanguageSwitcher() {
  const { i18n, t } = useTranslation('common')

  const changeLanguage = (lng: 'en' | 'fr') => {
    void i18n.changeLanguage(lng)
  }

  return (
    <div className="flex items-center gap-2" aria-label={t('app.language')}>
      <button
        type="button"
        onClick={() => changeLanguage('fr')}
        className={`text-sm px-2 py-1 rounded-md focus:ring-2 focus:ring-ring focus:ring-offset-2 ${i18n.language.startsWith('fr') ? 'font-semibold underline' : ''}`}
        aria-pressed={i18n.language.startsWith('fr')}
      >
        {t('app.french')}
      </button>
      <span aria-hidden>·</span>
      <button
        type="button"
        onClick={() => changeLanguage('en')}
        className={`text-sm px-2 py-1 rounded-md focus:ring-2 focus:ring-ring focus:ring-offset-2 ${i18n.language.startsWith('en') ? 'font-semibold underline' : ''}`}
        aria-pressed={i18n.language.startsWith('en')}
      >
        {t('app.english')}
      </button>
    </div>
  )
}
