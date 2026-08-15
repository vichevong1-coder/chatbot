import React from 'react';
import { Language } from '../types';

interface LanguageSwitcherProps {
  language: Language;
  onSelectLanguage: (lang: Language) => void;
  compact?: boolean;
}

export const LanguageSwitcher: React.FC<LanguageSwitcherProps> = ({
  language,
  onSelectLanguage,
}) => {
  return (
    <div className="inline-flex items-center bg-[#FFCB3D] border-3 border-[#2A1E4D] rounded-2xl p-1 shadow-[3px_3px_0px_#2A1E4D] text-xs">
      <button
        type="button"
        onClick={() => onSelectLanguage('km')}
        className={`px-2.5 py-1 rounded-xl font-black transition-all cursor-pointer ${
          language === 'km'
            ? 'bg-[#6C4FF6] text-white border-2 border-[#2A1E4D] shadow-[1.5px_1.5px_0px_#2A1E4D] -translate-y-0.5'
            : 'text-[#2A1E4D] hover:bg-black/10'
        }`}
        title="ភាសាខ្មែរ (Khmer)"
      >
        KM
      </button>

      <button
        type="button"
        onClick={() => onSelectLanguage('en')}
        className={`px-2.5 py-1 rounded-xl font-black transition-all cursor-pointer ${
          language === 'en'
            ? 'bg-[#6C4FF6] text-white border-2 border-[#2A1E4D] shadow-[1.5px_1.5px_0px_#2A1E4D] -translate-y-0.5'
            : 'text-[#2A1E4D] hover:bg-black/10'
        }`}
        title="English"
      >
        EN
      </button>
    </div>
  );
};
