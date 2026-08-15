import React, { useState } from 'react';
import { StepItem, Language } from '../types';
import { Lightbulb, Sparkles, HelpCircle, X, ChevronRight } from 'lucide-react';
import { TunsayAvatar } from './TunsayAvatar';

interface HintSheetProps {
  step: StepItem;
  isOpen: boolean;
  language?: Language;
  onClose: () => void;
}

export const HintSheet: React.FC<HintSheetProps> = ({
  step,
  isOpen,
  language = 'km',
  onClose
}) => {
  const [hintLevel, setHintLevel] = useState<1 | 2 | 3>(1);
  const isKhmer = language === 'km';

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-end sm:items-center justify-center bg-[#2A1E4D]/60 backdrop-blur-xs p-0 sm:p-4 animate-fadeIn text-[#2A1E4D]">
      <div 
        className="w-full max-w-lg bg-white rounded-t-3xl sm:rounded-3xl border-3 border-[#2A1E4D] shadow-[6px_6px_0px_#2A1E4D] overflow-hidden flex flex-col max-h-[85vh] animate-slideUp"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Sheet Header */}
        <div className="p-4 bg-[#6C4FF6] border-b-3 border-[#2A1E4D] flex items-center justify-between text-white">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 bg-[#FFCB3D] rounded-2xl border-2 border-[#2A1E4D] shadow-[2px_2px_0px_#2A1E4D] flex items-center justify-center">
              <TunsayAvatar size="sm" state="thinking" showBadge={false} />
            </div>
            <div>
              <h3 className="text-base sm:text-lg font-black text-white font-heading flex items-center gap-1.5 drop-shadow-[1px_1px_0px_#2A1E4D]">
                <Lightbulb className="w-5 h-5 text-[#FFCB3D] fill-[#FFCB3D]" />
                {isKhmer ? 'តម្រុយពី ទន្សាយ' : "Tunsay's Hints"}
              </h3>
              <p className="text-xs text-[#FFCB3D] font-bold">
                {isKhmer 
                  ? `ជំហានទី ${step.stepNumber} នៃ ${step.totalSteps}` 
                  : `Step ${step.stepNumber} of ${step.totalSteps}`}
              </p>
            </div>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="p-2 rounded-2xl bg-[#FF6FA3] border-2 border-[#2A1E4D] text-white hover:bg-[#FFCB3D] hover:text-[#2A1E4D] transition-colors cursor-pointer"
            title="Close hints"
          >
            <X className="w-5 h-5 stroke-[3]" />
          </button>
        </div>

        {/* Hint Level Selector Tabs */}
        <div className="flex border-b-3 border-[#2A1E4D] bg-[#EAF2FF] p-2 gap-2">
          <button
            type="button"
            onClick={() => setHintLevel(1)}
            className={`flex-1 py-2 px-3 rounded-2xl text-xs sm:text-sm font-black flex items-center justify-center gap-1.5 transition-all cursor-pointer border-2 border-[#2A1E4D] ${
              hintLevel === 1 
                ? 'bg-[#FFCB3D] text-[#2A1E4D] shadow-[2px_2px_0px_#2A1E4D] -translate-y-0.5' 
                : 'bg-white text-[#2A1E4D]/80 hover:bg-[#FFCB3D]/50'
            }`}
          >
            <Lightbulb className="w-3.5 h-3.5 stroke-[2.5]" />
            {isKhmer ? 'តម្រុយ ១' : 'Hint 1'}
          </button>

          <button
            type="button"
            onClick={() => setHintLevel(2)}
            className={`flex-1 py-2 px-3 rounded-2xl text-xs sm:text-sm font-black flex items-center justify-center gap-1.5 transition-all cursor-pointer border-2 border-[#2A1E4D] ${
              hintLevel === 2 
                ? 'bg-[#3EC6E0] text-[#2A1E4D] shadow-[2px_2px_0px_#2A1E4D] -translate-y-0.5' 
                : 'bg-white text-[#2A1E4D]/80 hover:bg-[#3EC6E0]/50'
            }`}
          >
            <HelpCircle className="w-3.5 h-3.5 stroke-[2.5]" />
            {isKhmer ? 'តម្រុយ ២' : 'Hint 2'}
          </button>

          <button
            type="button"
            onClick={() => setHintLevel(3)}
            className={`flex-1 py-2 px-3 rounded-2xl text-xs sm:text-sm font-black flex items-center justify-center gap-1.5 transition-all cursor-pointer border-2 border-[#2A1E4D] ${
              hintLevel === 3 
                ? 'bg-[#FF6FA3] text-white shadow-[2px_2px_0px_#2A1E4D] -translate-y-0.5' 
                : 'bg-white text-[#2A1E4D]/80 hover:bg-[#FF6FA3]/50'
            }`}
          >
            <Sparkles className="w-3.5 h-3.5 stroke-[2.5]" />
            {isKhmer ? 'ឧទាហរណ៍' : 'Example'}
          </button>
        </div>

        {/* Content Body */}
        <div className="p-5 overflow-y-auto space-y-4">
          {hintLevel === 1 && (
            <div className="bg-[#EAF2FF] p-4 rounded-2xl border-3 border-[#2A1E4D] shadow-[3px_3px_0px_#2A1E4D] space-y-2 animate-fadeIn">
              <div className="flex items-center gap-2 text-[#2A1E4D] font-black text-sm">
                <Sparkles className="w-4 h-4 text-[#FF6FA3]" />
                {isKhmer ? 'តម្រុយតូច៖' : 'Small hint:'}
              </div>
              <p className="text-sm sm:text-base text-[#2A1E4D] font-black leading-relaxed">
                {isKhmer ? step.hint1.khmer : step.hint1.eng}
              </p>
            </div>
          )}

          {hintLevel === 2 && (
            <div className="bg-[#EAF2FF] p-4 rounded-2xl border-3 border-[#2A1E4D] shadow-[3px_3px_0px_#2A1E4D] space-y-2 animate-fadeIn">
              <div className="flex items-center gap-2 text-[#2A1E4D] font-black text-sm">
                <HelpCircle className="w-4 h-4 text-[#3EC6E0]" />
                {isKhmer ? 'តម្រុយធំជាង៖' : 'Bigger hint:'}
              </div>
              <p className="text-sm sm:text-base text-[#2A1E4D] font-black leading-relaxed">
                {isKhmer ? step.hint2.khmer : step.hint2.eng}
              </p>
            </div>
          )}

          {hintLevel === 3 && (
            <div className="bg-[#FFCB3D] p-4 rounded-2xl border-3 border-[#2A1E4D] shadow-[3px_3px_0px_#2A1E4D] space-y-3 animate-fadeIn">
              <div className="flex items-center gap-2 text-[#2A1E4D] font-black text-sm">
                <Sparkles className="w-4 h-4 text-[#6C4FF6]" />
                {isKhmer ? step.hint3.titleKhmer : step.hint3.titleEng}
              </div>
              <p className="text-sm sm:text-base text-[#2A1E4D] font-black leading-relaxed bg-white p-3 rounded-xl border-2 border-[#2A1E4D]">
                {isKhmer ? step.hint3.exampleKhmer : step.hint3.exampleEng}
              </p>
            </div>
          )}

          {/* Sayo Encouragement Note */}
          <div className="flex items-center gap-3 p-3.5 bg-[#6FCF6F] rounded-2xl border-3 border-[#2A1E4D] shadow-[2px_2px_0px_#2A1E4D]">
            <Sparkles className="w-5 h-5 text-[#2A1E4D]" />
            <p className="text-xs sm:text-sm text-[#2A1E4D] font-black">
              {isKhmer 
                ? "អ្នកអាចធ្វើវាបាន! ព្យាយាមម្តងទៀតជាមួយចម្លើយរបស់អ្នក។" 
                : "You can do it! Give it a try now with your answer."}
            </p>
          </div>
        </div>

        {/* Bottom Actions */}
        <div className="p-4 bg-white border-t-3 border-[#2A1E4D] flex items-center justify-between">
          {hintLevel < 3 ? (
            <button
              type="button"
              onClick={() => setHintLevel((prev) => (prev + 1) as 1 | 2 | 3)}
              className="text-xs sm:text-sm font-black text-[#6C4FF6] hover:underline flex items-center gap-1 cursor-pointer"
            >
              {isKhmer ? 'មើលតម្រុយបន្ទាប់' : 'See next hint'} <ChevronRight className="w-4 h-4 stroke-[3]" />
            </button>
          ) : (
            <span className="text-xs font-black text-[#2A1E4D]">
              {isKhmer ? 'ត្រៀមខ្លួនសាកល្បងចម្លើយ!' : 'Ready to try your answer!'}
            </span>
          )}

          <button
            type="button"
            onClick={onClose}
            className="px-5 py-2.5 bg-[#6FCF6F] hover:bg-[#FFCB3D] text-[#2A1E4D] font-black text-xs sm:text-sm rounded-2xl border-3 border-[#2A1E4D] shadow-[3px_3px_0px_#2A1E4D] transition-all cursor-pointer"
          >
            {isKhmer ? 'យល់ហើយ!' : 'Got it!'}
          </button>
        </div>
      </div>
    </div>
  );
};
