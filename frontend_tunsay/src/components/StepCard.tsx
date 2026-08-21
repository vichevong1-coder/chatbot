import React, { useState } from 'react';
import { StepItem, Language } from '../types';
import { TunsayAvatar } from './TunsayAvatar';
import { Lightbulb, RefreshCw, Mic, CheckCircle, AlertCircle, ArrowRight, HelpCircle } from 'lucide-react';

interface StepCardProps {
  step: StepItem;
  language?: Language;
  onAnswerSubmit: (answer: string) => boolean | Promise<boolean>;
  onOpenHints: () => void;
  onOpenExplainDifferently: () => void;
  onVoiceInputRequested?: () => void;
}

export const StepCard: React.FC<StepCardProps> = ({
  step,
  language = 'km',
  onAnswerSubmit,
  onOpenHints,
  onOpenExplainDifferently,
  onVoiceInputRequested
}) => {
  const isKhmer = language === 'km';
  const [selectedOption, setSelectedOption] = useState<string | null>(null);
  const [feedback, setFeedback] = useState<'none' | 'correct' | 'incorrect'>('none');
  const [typedAnswer, setTypedAnswer] = useState('');

  const socraticPrompt = isKhmer ? step.socraticPromptKhmer : step.socraticPromptEng;

  const handleOptionClick = async (optionText: string) => {
    setSelectedOption(optionText);
    const isCorrect = await onAnswerSubmit(optionText);
    setFeedback(isCorrect ? 'correct' : 'incorrect');
  };

  const handleFormSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!typedAnswer.trim()) return;
    const isCorrect = await onAnswerSubmit(typedAnswer.trim());
    setFeedback(isCorrect ? 'correct' : 'incorrect');
  };

  return (
    <div className="w-full bg-white rounded-3xl border-3 border-[#2A1E4D] shadow-[4px_4px_0px_#2A1E4D] p-5 sm:p-6 space-y-5 animate-fadeIn">
      {/* Top Banner: Step Indicator & Tunsay Mascot */}
      <div className="flex items-center justify-between flex-wrap gap-2 pb-3 border-b-2 border-[#2A1E4D]/20">
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 bg-[#FFCB3D] rounded-2xl border-2 border-[#2A1E4D] shadow-[2px_2px_0px_#2A1E4D] flex items-center justify-center">
            <TunsayAvatar size="sm" state={feedback === 'incorrect' ? 'thinking' : feedback === 'correct' ? 'celebrating' : 'explaining'} showBadge={false} />
          </div>
          <div>
            <span className="px-3 py-0.5 bg-[#FF6FA3] text-white text-xs font-black rounded-full border-2 border-[#2A1E4D] shadow-[1.5px_1.5px_0px_#2A1E4D]">
              {isKhmer 
                ? `ជំហានទី ${step.stepNumber} នៃ ${step.totalSteps}` 
                : `Step ${step.stepNumber} of ${step.totalSteps}`}
            </span>
            <h4 className="text-base sm:text-lg font-black text-[#2A1E4D] font-heading mt-1">
              {isKhmer ? step.questionKhmer : step.questionEng}
            </h4>
          </div>
        </div>
      </div>

      {/* Tunsay Socratic Guiding Prompt.
          No step in the corpus carries socraticPrompt* (see types.ts), so this
          panel rendered as an empty blue box on every problem. Guarded rather
          than deleted: the slot is a real product idea waiting on content. */}
      {socraticPrompt && (
        <div className="p-4 bg-[#EAF2FF] rounded-2xl border-3 border-[#2A1E4D] shadow-[3px_3px_0px_#2A1E4D] space-y-2">
          <p className="text-xs font-black text-[#6C4FF6] uppercase tracking-wider">
            {isKhmer ? 'សំណួរណែនាំពីទន្សាយ៖' : "Tunsay's Guiding Prompt:"}
          </p>
          <p className="text-sm sm:text-base font-black text-[#2A1E4D] leading-relaxed">
            {socraticPrompt}
          </p>
        </div>
      )}

      {/* Answer Options or Input Area */}
      {step.options ? (
        <div className="space-y-3">
          <p className="text-xs font-black text-[#2A1E4D] uppercase">
            {isKhmer ? 'ជ្រើសរើសចម្លើយរបស់អ្នក៖' : 'Choose your answer:'}
          </p>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            {step.options.map((opt, idx) => {
              const isSelected = selectedOption === opt;
              return (
                <button
                  key={idx}
                  type="button"
                  onClick={() => handleOptionClick(opt)}
                  className={`p-4 rounded-2xl border-3 font-black text-sm sm:text-base transition-all text-left flex items-center justify-between cursor-pointer ${
                    isSelected && feedback === 'correct'
                      ? 'bg-[#6FCF6F] border-[#2A1E4D] text-[#2A1E4D] shadow-[3px_3px_0px_#2A1E4D]'
                      : isSelected && feedback === 'incorrect'
                      ? 'bg-[#FF6FA3] border-[#2A1E4D] text-white shadow-[3px_3px_0px_#2A1E4D]'
                      : 'bg-white border-[#2A1E4D] text-[#2A1E4D] hover:bg-[#FFCB3D] shadow-[3px_3px_0px_#2A1E4D] hover:-translate-y-0.5 active:translate-y-0.5 active:shadow-[1px_1px_0px_#2A1E4D]'
                  }`}
                >
                  <span>{opt}</span>
                  {isSelected && feedback === 'correct' && (
                    <CheckCircle className="w-5 h-5 text-[#2A1E4D] stroke-[3]" />
                  )}
                  {isSelected && feedback === 'incorrect' && (
                    <AlertCircle className="w-5 h-5 text-white stroke-[3]" />
                  )}
                </button>
              );
            })}
          </div>
        </div>
      ) : (
        <form onSubmit={handleFormSubmit} className="space-y-3">
          <div className="flex items-center gap-2">
            <input
              type="text"
              value={typedAnswer}
              onChange={(e) => setTypedAnswer(e.target.value)}
              placeholder={isKhmer ? 'វាយចម្លើយរបស់អ្នកនៅទីនេះ...' : 'Type your answer here...'}
              className="flex-1 p-3.5 bg-[#EAF2FF] rounded-2xl border-3 border-[#2A1E4D] shadow-[3px_3px_0px_#2A1E4D] font-black text-base text-[#2A1E4D] focus:outline-none"
            />
            {onVoiceInputRequested && (
              <button
                type="button"
                onClick={onVoiceInputRequested}
                className="p-3.5 bg-[#3EC6E0] rounded-2xl border-3 border-[#2A1E4D] shadow-[3px_3px_0px_#2A1E4D] text-[#2A1E4D] hover:-translate-y-0.5 transition-transform cursor-pointer"
                title={isKhmer ? 'ឆ្លើយតាមសំឡេង' : 'Answer with voice'}
              >
                <Mic className="w-5 h-5 stroke-[2.5]" />
              </button>
            )}
            <button
              type="submit"
              className="px-5 py-3.5 bg-[#6C4FF6] text-white font-black rounded-2xl border-3 border-[#2A1E4D] shadow-[3px_3px_0px_#2A1E4D] hover:-translate-y-0.5 transition-transform cursor-pointer"
            >
              <ArrowRight className="w-5 h-5 stroke-[3]" />
            </button>
          </div>
        </form>
      )}

      {/* Feedback Banner */}
      {feedback === 'correct' && (
        <div className="p-3.5 bg-[#6FCF6F] text-[#2A1E4D] rounded-2xl border-3 border-[#2A1E4D] shadow-[3px_3px_0px_#2A1E4D] flex items-center gap-2 font-black text-sm animate-fadeIn">
          <CheckCircle className="w-5 h-5 stroke-[3]" />
          <span>{isKhmer ? 'ត្រឹមត្រូវហើយ! ពូកែណាស់!' : 'Correct! Awesome job!'}</span>
        </div>
      )}

      {feedback === 'incorrect' && (
        <div className="p-3.5 bg-[#FF6FA3] text-white rounded-2xl border-3 border-[#2A1E4D] shadow-[3px_3px_0px_#2A1E4D] flex items-center justify-between gap-2 font-black text-sm animate-fadeIn">
          <div className="flex items-center gap-2">
            <AlertCircle className="w-5 h-5 stroke-[3]" />
            <span>{isKhmer ? 'ព្យាយាមម្តងទៀត! មើលតម្រុយខាងក្រោម' : 'Try again! Check the hint below'}</span>
          </div>
          <button
            type="button"
            onClick={onOpenHints}
            className="px-3 py-1 bg-[#FFCB3D] text-[#2A1E4D] rounded-xl border-2 border-[#2A1E4D] shadow-[1px_1px_0px_#2A1E4D] text-xs font-black cursor-pointer"
          >
            {isKhmer ? 'តម្រុយ' : 'Hint'}
          </button>
        </div>
      )}

      {/* Scaffolding Action Buttons (Hint & Explain Differently) */}
      <div className="flex flex-wrap items-center justify-between gap-3 pt-2 border-t-2 border-[#2A1E4D]/20">
        <button
          type="button"
          onClick={onOpenHints}
          className="px-4 py-2.5 bg-[#FFCB3D] text-[#2A1E4D] hover:bg-[#FFCB3D]/80 rounded-2xl font-black text-xs sm:text-sm border-3 border-[#2A1E4D] shadow-[3px_3px_0px_#2A1E4D] hover:-translate-y-0.5 active:translate-y-0.5 active:shadow-[1px_1px_0px_#2A1E4D] flex items-center gap-2 transition-all cursor-pointer"
        >
          <Lightbulb className="w-4 h-4 fill-[#2A1E4D] stroke-[2.5]" />
          <span>{isKhmer ? 'តម្រុយ' : 'Hint'}</span>
        </button>

        <button
          type="button"
          onClick={onOpenExplainDifferently}
          className="px-4 py-2.5 bg-[#3EC6E0] text-[#2A1E4D] hover:bg-[#3EC6E0]/80 rounded-2xl font-black text-xs sm:text-sm border-3 border-[#2A1E4D] shadow-[3px_3px_0px_#2A1E4D] hover:-translate-y-0.5 active:translate-y-0.5 active:shadow-[1px_1px_0px_#2A1E4D] flex items-center gap-2 transition-all cursor-pointer"
        >
          <RefreshCw className="w-4 h-4 stroke-[2.5]" />
          <span>{isKhmer ? 'ពន្យល់តាមរបៀបផ្សេង' : 'Explain Differently'}</span>
        </button>
      </div>
    </div>
  );
};
