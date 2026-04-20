import React from 'react';
import { useTranslation } from 'react-i18next';
import { Globe } from 'lucide-react';

const languages = [
    { code: 'en', label: 'English', flag: '🇺🇸' },
    { code: 'hi', label: 'हिन्दी', flag: '🇮🇳' },
    { code: 'mr', label: 'मराठी', flag: '🇮🇳' },
    { code: 'es', label: 'Español', flag: '🇪🇸' },
    { code: 'fr', label: 'Français', flag: '🇫🇷' },
    { code: 'de', label: 'Deutsch', flag: '🇩🇪' }
];

const LanguageSelector = () => {
    const { i18n } = useTranslation();

    const changeLanguage = (lng) => {
        i18n.changeLanguage(lng);
        // Optionally persist to local storage
        localStorage.setItem('i18nextLng', lng);
    };

    return (
        <div className="relative group">
            <button className="flex items-center gap-2 p-2 rounded-lg hover:bg-white/10 transition-colors text-slate-300 hover:text-white">
                <Globe size={20} />
                <span className="text-sm font-medium">{languages.find(l => i18n.language.startsWith(l.code))?.label || 'Language'}</span>
            </button>

            <div className="absolute right-0 top-full mt-2 w-48 bg-slate-800 border border-slate-700 rounded-lg shadow-xl overflow-hidden hidden group-hover:block z-50">
                {languages.map((lang) => (
                    <button
                        key={lang.code}
                        onClick={() => changeLanguage(lang.code)}
                        className={`w-full text-left px-4 py-3 text-sm flex items-center gap-3 hover:bg-slate-700 transition-colors ${i18n.language === lang.code ? 'bg-slate-700 text-teal-400' : 'text-slate-300'
                            }`}
                    >
                        <span className="text-lg">{lang.flag}</span>
                        <span>{lang.label}</span>
                    </button>
                ))}
            </div>
        </div >
    );
};

export default LanguageSelector;
