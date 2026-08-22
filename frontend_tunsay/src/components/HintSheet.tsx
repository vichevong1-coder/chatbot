import React, { useState, useEffect } from 'react';
import { StepItem, Language } from '../types';
import { Lightbulb, Sparkles, HelpCircle, X, ChevronRight, Star, Loader2 } from 'lucide-react';
import { TunsayAvatar } from './TunsayAvatar';

interface HintSheetProps {
  step: StepItem;
  isOpen: boolean;
  problemId?: string;
  language?: Language;
  onClose: () => void;
  onRequestAIHint?: (hintLevel: number) => Promise<{ hintKhmer: string; hintEng: string }>;
  onDeductStars?: (hintLevel: number) => Promise<{ starsRemaining: number }>;
}

export const HintSheet: React.FC<HintSheetProps> = ({
  step,
  isOpen,
  problemId,
  language = 'km',
  onClose,
  onRequestAIHint,
  onDeductStars,
}) => {
  const [hintLevel, setHintLevel] = useState<1 | 2 | 3>(1);
  const [aiHints, setAiHints] = useState<Record<number, { hintKhmer: string; hintEng: string }>>({});
  const [aiLoading, setAiLoading] = useState<Record<number, boolean>>({});
  const [usedHints, setUsedHints] = useState<Set<number>>(new Set());
  const [starToast, setStarToast] = useState<string | null>(null);

  const isKhmer = language === 'km';

  // Check if static hint exists for given level
  const hasStaticHint = (lvl: 1 | 2 | 3): boolean => {
    if (lvl === 1) return Boolean(step.hint1?.khmer || step.hint1?.eng);
    if (lvl === 2) return Boolean(step.hint2?.khmer || step.hint2?.eng);
    if (lvl === 3) return Boolean(step.hint3?.exampleKhmer || step.hint3?.exampleEng || step.hint3?.titleKhmer || step.hint3?.titleEng);
    return false;
  };

  // Reset when step changes
  useEffect(() => {
    setHintLevel(1);
    setAiHints({});
    setAiLoading({});
    setUsedHints(new Set());
    setStarToast(null);
  }, [step.id]);

  // Handle star deduction & AI hint fetch when level changes
  useEffect(() => {
    if (!isOpen) return;

    // Star deduction on first view
    if (!usedHints.has(hintLevel) && onDeductStars) {
      setUsedHints((prev) => new Set(prev).add(hintLevel));
      onDeductStars(hintLevel).then((res) => {
        if (res && res.starsRemaining >= 0) {
          const msg = isKhmer ? `⭐ -${hintLevel} ពិន្ទុ` : `⭐ -${hintLevel} stars`;
          setStarToast(msg);
          setTimeout(() => setStarToast(null), 2500);
        }
      });
    }

    // AI hint fetch if static hint is missing
    if (!hasStaticHint(hintLevel) && !aiHints[hintLevel] && onRequestAIHint && !aiLoading[hintLevel]) {
      setAiLoading((prev) => ({ ...prev, [hintLevel]: true }));
      onRequestAIHint(hintLevel)
        .then((res) => {
          if (res) {
            setAiHints((prev) => ({ ...prev, [hintLevel]: res }));
          }
        })
        .finally(() => {
          setAiLoading((prev) => ({ ...prev, [hintLevel]: false }));
        });
    }
  }, [hintLevel, isOpen, step.id]);

  if (!isOpen) return null;

  const currentAiHint = aiHints[hintLevel];
  const isLoadingAi = aiLoading[hintLevel];

  return (
    <div className="fixed inset-0 z-50 flex items-end sm:items-center justify-center bg-[#2A1E4D]/60 backdrop-blur-xs p-0 sm:p-4 animate-fadeIn text-[#2A1E4D]">
      <div 
        className="w-full max-w-lg bg-white rounded-t-3xl sm:rounded-3xl border-3 border-[#2A1E4D] shadow-[6px_6px_0px_#2A1E4D] overflow-hidden flex flex-col max-h-[85vh] animate-slideUp relative"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Star Deduction Toast */}
        {starToast && (
          <div className="absolute top-16 right-4 z-50 px-3 py-1.5 bg-[#FF6FA3] text-white text-xs font-black rounded-full border-2 border-[#2A1E4D] shadow-[2px_2px_0px_#2A1E4D] flex items-center gap-1.5 animate-bounce">
            <Star className="w-3.5 h-3.5 fill-white" />
            <span>{starToast}</span>
          </div>
        )}

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
        <div className="border-b-3 border-[#2A1E4D] bg-[#EAF2FF] p-2 space-y-1.5">
          <div className="flex gap-2">
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

          {/* Hint Progress Indicator */}
          <div className="text-center">
            <span className="text-[11px] font-bold text-[#6C4FF6]">
              {hintLevel < 3 
                ? (isKhmer ? `តម្រុយទី ${hintLevel} នៃ ៣ — អ្នកអាចមើលបន្ថែមបាន!` : `Hint ${hintLevel} of 3 — you can ask for more help!`)
                : (isKhmer ? '✨ នេះជាតម្រុយលម្អិតបំផុត!' : '✨ This is the most detailed hint!')}
            </span>
          </div>
        </div>

        {/* Content Body */}
        <div className="p-5 overflow-y-auto space-y-4">
          {isLoadingAi ? (
            <div className="bg-[#EAF2FF] p-6 rounded-2xl border-3 border-[#2A1E4D] shadow-[3px_3px_0px_#2A1E4D] flex flex-col items-center justify-center gap-2 animate-pulse">
              <Loader2 className="w-6 h-6 text-[#6C4FF6] animate-spin" />
              <p className="text-xs font-black text-[#2A1E4D]">
                {isKhmer ? 'ទន្សាយកំពុងបង្កើតតម្រុយ AI...' : 'Tunsay is generating an AI hint...'}
              </p>
            </div>
          ) : hasStaticHint(hintLevel) ? (
            <>
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
            </>
          ) : currentAiHint ? (
            <div className="bg-[#EAF2FF] p-4 rounded-2xl border-3 border-[#2A1E4D] shadow-[3px_3px_0px_#2A1E4D] space-y-2 animate-fadeIn">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2 text-[#2A1E4D] font-black text-sm">
                  <Sparkles className="w-4 h-4 text-[#FF6FA3]" />
                  {isKhmer ? `តម្រុយ AI (កម្រិត ${hintLevel})៖` : `AI Hint (Level ${hintLevel}):`}
                </div>
                <span className="px-2 py-0.5 bg-[#FFCB3D] text-[#2A1E4D] text-[10px] font-black rounded-full border border-[#2A1E4D]">
                  ✨ AI Generated
                </span>
              </div>
              <p className="text-sm sm:text-base text-[#2A1E4D] font-black leading-relaxed">
                {isKhmer ? (currentAiHint.hintKhmer || currentAiHint.hintEng) : (currentAiHint.hintEng || currentAiHint.hintKhmer)}
              </p>
            </div>
          ) : (
            <div className="bg-[#EAF2FF] p-4 rounded-2xl border-3 border-[#2A1E4D] shadow-[3px_3px_0px_#2A1E4D] space-y-2 animate-fadeIn">
              <p className="text-sm text-[#2A1E4D] font-bold">
                {isKhmer 
                  ? 'សូមអានសំណួរម្តងទៀតដោយប្រុងប្រយ័ត្នដើម្បីរកពាក្យគន្លឹះ។ 🐰' 
                  : 'Please read the question carefully to find the keywords. 🐰'}
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
