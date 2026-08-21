import React from 'react';
import { UserProfile, Language } from '../types';
import { TunsayAvatar } from './TunsayAvatar';
import { Home, BookOpen, User, Star } from 'lucide-react';

interface HeaderProps {
  profile: UserProfile;
  activeTab: 'home' | 'chat' | 'profile';
  onSelectTab: (tab: 'home' | 'chat' | 'profile') => void;
  onSelectLanguage: (lang: Language) => void;
}

export const Header: React.FC<HeaderProps> = ({
  profile,
  activeTab,
  onSelectTab,
  onSelectLanguage
}) => {
  const isKhmer = profile.language === 'km';

  return (
    <header className={`sticky top-0 z-50 w-full bg-white/95 backdrop-blur-md transition-all ${activeTab === 'chat' ? 'pb-0' : 'pb-2'}`}>
      <div className="w-full bg-[#6C4FF6] relative overflow-hidden">
        <div className={`mx-auto py-2 sm:py-3 flex items-center justify-between gap-2 sm:gap-4 relative z-10 ${
          activeTab === 'chat' ? 'w-full px-3 sm:px-8 lg:px-14' : 'max-w-7xl px-3 sm:px-6 lg:px-8'
        }`}>
          {/* Brand & Tunsay Logo */}
          <div 
            onClick={() => onSelectTab('home')}
            className="flex items-center gap-2 sm:gap-3 cursor-pointer group shrink-0"
          >
            <div className="w-9 h-9 sm:w-12 sm:h-12 bg-[#FFCB3D] rounded-xl sm:rounded-2xl flex items-center justify-center border-2 sm:border-3 border-[#2A1E4D] shadow-[2px_2px_0px_#2A1E4D] sm:shadow-[3px_3px_0px_#2A1E4D] group-hover:-translate-y-0.5 group-hover:scale-105 transition-all">
              <TunsayAvatar size="sm" state="idle" showBadge={false} />
            </div>
            <div>
              <div className="flex items-center gap-1.5">
                <h1 className="text-base sm:text-2xl lg:text-3xl font-black text-white font-heading tracking-wide leading-none drop-shadow-[2px_2px_0px_#2A1E4D]">
                  Tunsay
                </h1>
              </div>
              <p className="text-[10px] sm:text-xs font-black text-[#FFCB3D] mt-0.5 hidden sm:block tracking-wide">
                {isKhmer ? 'គ្រូបង្រៀន AI' : 'AI Homework Tutor'}
              </p>
            </div>
          </div>

          {/* Nav Segmented Control inside Purple Header ONLY for Chat Page - Positioned on Far Top Right */}
          {activeTab === 'chat' && (
            <div className="flex items-center gap-0.5 sm:gap-1.5 bg-[#2A1E4D]/35 p-0.5 sm:p-1 rounded-lg sm:rounded-2xl border-1.5 sm:border-2 border-[#2A1E4D] shadow-[1.5px_1.5px_0px_#2A1E4D] sm:shadow-[2px_2px_0px_#2A1E4D] shrink-0 ml-auto">
              <button
                type="button"
                onClick={() => onSelectTab('home')}
                // Always inactive: this toolbar only renders while activeTab === 'chat'.
                className="px-2 sm:px-3 py-1 sm:py-1.5 rounded-md sm:rounded-xl text-[11px] sm:text-sm font-black transition-all cursor-pointer flex items-center gap-1 border sm:border-2 border-[#2A1E4D] bg-white/95 text-[#2A1E4D] hover:bg-white shadow-[1px_1px_0px_#2A1E4D]"
              >
                <Home className="w-3.5 h-3.5 sm:w-4 sm:h-4 stroke-[2.5]" />
                <span className="hidden min-[380px]:inline">{isKhmer ? 'ទំព័រដើម' : 'Home'}</span>
              </button>

              <button
                type="button"
                onClick={() => onSelectTab('chat')}
                className={`px-2 sm:px-3 py-1 sm:py-1.5 rounded-md sm:rounded-xl text-[11px] sm:text-sm font-black transition-all cursor-pointer flex items-center gap-1 border sm:border-2 border-[#2A1E4D] ${
                  activeTab === 'chat'
                    ? 'bg-[#FFCB3D] text-[#2A1E4D] shadow-[1px_1px_0px_#2A1E4D]'
                    : 'bg-white/95 text-[#2A1E4D] hover:bg-white shadow-[1px_1px_0px_#2A1E4D]'
                }`}
              >
                <BookOpen className="w-3.5 h-3.5 sm:w-4 sm:h-4 stroke-[2.5]" />
                <span className="hidden min-[380px]:inline">{isKhmer ? 'លំហាត់' : 'Homework'}</span>
              </button>

              <button
                type="button"
                onClick={() => onSelectTab('profile')}
                // Always inactive: this toolbar only renders while activeTab === 'chat'.
                className="px-2 sm:px-3 py-1 sm:py-1.5 rounded-md sm:rounded-xl text-[11px] sm:text-sm font-black transition-all cursor-pointer flex items-center gap-1 border sm:border-2 border-[#2A1E4D] bg-white/95 text-[#2A1E4D] hover:bg-white shadow-[1px_1px_0px_#2A1E4D]"
              >
                <Star className="w-3.5 h-3.5 sm:w-4 sm:h-4 stroke-[2.5]" />
                <span className="hidden min-[380px]:inline">{isKhmer ? 'គណនី' : 'Profile'}</span>
              </button>
            </div>
          )}

          {/* Removed language switcher from nav per user request */}
        </div>

        {/* Scalloped Wavy Bottom Edge SVG Pattern */}
        <div className="absolute top-full -mt-[10px] left-0 right-0 h-[30px] overflow-hidden leading-none pointer-events-none z-20">
          <svg
            className="w-full h-[30px] text-[#6C4FF6] fill-current block"
            preserveAspectRatio="none"
          >
            <defs>
              <pattern
                id="header-scallop"
                x="0"
                y="0"
                width="52"
                height="30"
                patternUnits="userSpaceOnUse"
              >
                <path d="M 0,0 L 52,0 L 52,10 C 39,28 13,28 0,10 Z" />
              </pattern>
            </defs>
            <rect x="0" y="0" width="100%" height="30" fill="url(#header-scallop)" />
          </svg>
        </div>
      </div>

      {/* Chunky Pill Nav Buttons below header (Only for Home & Profile pages) */}
      {activeTab !== 'chat' && (
        <nav className="max-w-7xl mx-auto px-3 sm:px-6 lg:px-8 pt-2.5 sm:pt-3.5 pb-2 sm:pb-3 flex items-center justify-start sm:justify-start gap-2 sm:gap-4 overflow-x-auto no-scrollbar">
          <button
            type="button"
            onClick={() => onSelectTab('home')}
            className={`px-3.5 sm:px-6 py-2 sm:py-2.5 rounded-xl sm:rounded-3xl text-xs sm:text-base font-black transition-all cursor-pointer flex items-center gap-1.5 sm:gap-2 shrink-0 border-2.5 sm:border-3 border-[#2A1E4D] ${
              activeTab === 'home'
                ? 'bg-[#FFCB3D] text-[#2A1E4D] shadow-[2.5px_2.5px_0px_#2A1E4D] sm:shadow-[3px_3px_0px_#2A1E4D] -translate-y-0.5'
                : 'bg-white text-[#2A1E4D] shadow-[2px_2px_0px_#2A1E4D] sm:shadow-[2.5px_2.5px_0px_#2A1E4D] hover:bg-[#FFCB3D]/20 hover:-translate-y-0.5'
            }`}
          >
            <Home className="w-4 h-4 sm:w-5 sm:h-5 stroke-[2.5]" />
            <span>{isKhmer ? 'ទំព័រដើម' : 'Home'}</span>
          </button>

          <button
            type="button"
            onClick={() => onSelectTab('chat')}
            // Always inactive: this button only renders while activeTab !== 'chat'.
            className="px-3.5 sm:px-6 py-2 sm:py-2.5 rounded-xl sm:rounded-3xl text-xs sm:text-base font-black transition-all cursor-pointer flex items-center gap-1.5 sm:gap-2 shrink-0 border-2.5 sm:border-3 border-[#2A1E4D] bg-white text-[#2A1E4D] shadow-[2px_2px_0px_#2A1E4D] sm:shadow-[2.5px_2.5px_0px_#2A1E4D] hover:bg-[#FFCB3D]/20 hover:-translate-y-0.5"
          >
            <BookOpen className="w-4 h-4 sm:w-5 sm:h-5 stroke-[2.5]" />
            <span>{isKhmer ? 'លំហាត់' : 'Homework'}</span>
          </button>

          <button
            type="button"
            onClick={() => onSelectTab('profile')}
            className={`px-3.5 sm:px-6 py-2 sm:py-2.5 rounded-xl sm:rounded-3xl text-xs sm:text-base font-black transition-all cursor-pointer flex items-center gap-1.5 sm:gap-2 shrink-0 border-2.5 sm:border-3 border-[#2A1E4D] ${
              activeTab === 'profile'
                ? 'bg-[#FFCB3D] text-[#2A1E4D] shadow-[2.5px_2.5px_0px_#2A1E4D] sm:shadow-[3px_3px_0px_#2A1E4D] -translate-y-0.5'
                : 'bg-white text-[#2A1E4D] shadow-[2px_2px_0px_#2A1E4D] sm:shadow-[2.5px_2.5px_0px_#2A1E4D] hover:bg-[#FFCB3D]/20 hover:-translate-y-0.5'
            }`}
          >
            <Star className="w-4 h-4 sm:w-5 sm:h-5 stroke-[2.5]" />
            <span>{isKhmer ? 'គណនី' : 'Profile'}</span>
          </button>
        </nav>
      )}
    </header>
  );
};
