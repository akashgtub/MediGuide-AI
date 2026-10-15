import { createContext, useState, useContext, useEffect, useCallback } from 'react';
import { SUPPORTED_LANGUAGES, translations } from '../i18n/translations';
import { useAuth, apiFetch } from './AuthContext';

const LanguageContext = createContext(null);

export const LanguageProvider = ({ children }) => {
  const { user } = useAuth();

  // Initialize language from user preference or localStorage or default 'en'
  const [language, setLanguageState] = useState(() => {
    const saved = localStorage.getItem('mediguide_language');
    if (saved && SUPPORTED_LANGUAGES.some((l) => l.code === saved)) {
      return saved;
    }
    return 'en';
  });

  // Restore saved language preference whenever user logs in or profile changes
  useEffect(() => {
    if (user?.preferred_language && SUPPORTED_LANGUAGES.some((l) => l.code === user.preferred_language)) {
      setLanguageState(user.preferred_language);
      localStorage.setItem('mediguide_language', user.preferred_language);
    }
  }, [user]);

  // Update language, persist to localStorage, and sync to backend SQLite for authenticated patient
  const setLanguage = useCallback(
    async (newLang) => {
      if (!SUPPORTED_LANGUAGES.some((l) => l.code === newLang)) {
        return;
      }
      setLanguageState(newLang);
      localStorage.setItem('mediguide_language', newLang);

      // Persist to backend database for logged-in user
      if (user) {
        try {
          await apiFetch('/api/auth/language', {
            method: 'PATCH',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ preferred_language: newLang }),
          });
        } catch (err) {
          // Local preference still preserved in localStorage
          console.warn('Could not persist language preference to backend:', err);
        }
      }
    },
    [user]
  );

  // Translation lookup function with nested dot-notation and fallback to English
  const t = useCallback(
    (keyPath, fallback = '') => {
      if (!keyPath) return fallback;

      const keys = keyPath.split('.');
      let current = translations[language];

      for (const k of keys) {
        if (current && typeof current === 'object' && k in current) {
          current = current[k];
        } else {
          current = null;
          break;
        }
      }

      if (current !== null && current !== undefined && typeof current === 'string') {
        return current;
      }

      // Fallback to English dictionary
      let enCurrent = translations.en;
      for (const k of keys) {
        if (enCurrent && typeof enCurrent === 'object' && k in enCurrent) {
          enCurrent = enCurrent[k];
        } else {
          enCurrent = null;
          break;
        }
      }

      if (enCurrent !== null && enCurrent !== undefined && typeof enCurrent === 'string') {
        return enCurrent;
      }

      return fallback || keyPath;
    },
    [language]
  );

  const currentLanguageInfo = SUPPORTED_LANGUAGES.find((l) => l.code === language) || SUPPORTED_LANGUAGES[0];

  return (
    <LanguageContext.Provider
      value={{
        language,
        setLanguage,
        t,
        supportedLanguages: SUPPORTED_LANGUAGES,
        currentLanguageInfo,
      }}
    >
      {children}
    </LanguageContext.Provider>
  );
};

export const useLanguage = () => {
  const context = useContext(LanguageContext);
  if (!context) {
    throw new Error('useLanguage must be used within a LanguageProvider');
  }
  return context;
};
