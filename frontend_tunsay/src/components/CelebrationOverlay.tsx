import React from 'react';
import { Trophy, ArrowRight, RotateCcw, Star, Sparkles, Leaf } from 'lucide-react';
import { TunsayAvatar } from './TunsayAvatar';
import { Language } from '../types';

interface CelebrationOverlayProps {
  isOpen: boolean;
  language?: Language;
  onRestart: () => void;
  onContinue: () => void;
}

export const CelebrationOverlay: React.FC<CelebrationOverlayProps> = ({
  isOpen,
  language = 'km',
  onRestart,
  onContinue
}) => {
  const isKhmer = language === 'km';

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-[#2A1E4D]/60 backdrop-blur-xs p-4 animate-fadeIn">
      {/* Sparkles Particle Effect */}
      <div className="absolute inset-0 pointer-events-none overflow-hidden">
        {[...Array(12)].map((_, i) => (
          <div
            key={i}
            className="absolute text-xl animate-bounce"
            style={{
              top: `${Math.random() * 80}%`,
              left: `${Math.random() * 90}%`,
              animationDelay: `${i * 0.2}s`,
              animationDuration: `${1.5 + Math.random()}s`
            }}
          >
            {i % 3 === 0 ? (
              <Sparkles className="w-6 h-6 text-[#FFCB3D] fill-[#FFCB3D]" />
            ) : i % 3 === 1 ? (
              <Leaf className="w-6 h-6 text-[#6FCF6F]" />
            ) : (
              <Star className="w-6 h-6 text-[#FF6FA3] fill-[#FF6FA3]" />
            )}
          </div>
        ))}
      </div>

      <div className="w-full max-w-md bg-[#FFCB3D] rounded-3xl border-3 border-[#2A1E4D] shadow-[6px_6px_0px_#2A1E4D] p-6 sm:p-8 relative overflow-hidden flex flex-col items-center text-center space-y-5 animate-scaleUp z-10 text-[#2A1E4D]">
        <div className="p-3 bg-white rounded-2xl border-3 border-[#2A1E4D] shadow-[3px_3px_0px_#2A1E4D]">
          <Trophy className="w-8 h-8 text-[#2A1E4D]" />
        </div>

        <TunsayAvatar size="xl" state="celebrating" showBadge={false} />

        <div className="space-y-2">
          <h2 className="text-2xl sm:text-3xl font-black text-[#2A1E4D] font-heading drop-shadow-[1px_1px_0px_white]">
            {isKhmer ? 'អ្នកធ្វើបានហើយ!' : 'You solved it!'}
          </h2>
          <p className="text-sm sm:text-base font-black text-[#2A1E4D] bg-white p-4 rounded-2xl border-3 border-[#2A1E4D] shadow-[3px_3px_0px_#2A1E4D] leading-relaxed">
            {isKhmer 
              ? 'អ្នកបានប្រើខួរក្បាលគិតដោយខ្លួនឯង! ពូកែណាស់' 
              : 'You did the thinking yourself! Great job!'}
          </p>
        </div>

        <div className="flex gap-3 w-full pt-2">
          <button
            type="button"
            onClick={onRestart}
            className="flex-1 py-3.5 px-4 rounded-2xl border-3 border-[#2A1E4D] bg-white text-[#2A1E4D] font-black text-xs sm:text-sm flex items-center justify-center gap-1.5 shadow-[3px_3px_0px_#2A1E4D] hover:-translate-y-0.5 transition-all cursor-pointer"
          >
            <RotateCcw className="w-4 h-4 stroke-[2.5]" /> {isKhmer ? 'ធ្វើម្តងទៀត' : 'Try Again'}
          </button>
          <button
            type="button"
            onClick={onContinue}
            className="flex-1 py-3.5 px-4 rounded-2xl bg-[#6FCF6F] text-[#2A1E4D] font-black text-xs sm:text-sm border-3 border-[#2A1E4D] shadow-[3px_3px_0px_#2A1E4D] flex items-center justify-center gap-1.5 hover:-translate-y-0.5 transition-all cursor-pointer"
          >
            <span>{isKhmer ? 'បន្តទៀត' : 'Next'}</span>
            <ArrowRight className="w-4 h-4 stroke-[3]" />
          </button>
        </div>
      </div>
    </div>
  );
};
