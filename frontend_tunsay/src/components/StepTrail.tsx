import React from 'react';
import { Language } from '../types';
import { Footprints, Check } from 'lucide-react';

interface StepTrailProps {
  currentStep: number;
  totalSteps: number;
  language?: Language;
  onSelectStep?: (stepIndex: number) => void;
}

export const StepTrail: React.FC<StepTrailProps> = ({
  currentStep,
  totalSteps,
  language = 'km',
  onSelectStep
}) => {
  const isKhmer = language === 'km';

  return (
    <div className="w-full flex justify-center items-center my-3">
      <div className="flex flex-wrap items-center justify-center gap-3 px-6 py-2.5 bg-white rounded-full border-3 border-[#2A1E4D] shadow-[4px_4px_0px_#2A1E4D]">
        <div className="flex items-center gap-1.5 text-xs font-black text-[#2A1E4D]">
          <Footprints className="w-4 h-4 text-[#6C4FF6]" />
          <span>
            {isKhmer 
              ? `ជំហានទី ${currentStep} នៃ ${totalSteps}` 
              : `Step ${currentStep} of ${totalSteps}`}
          </span>
        </div>

        <div className="flex items-center gap-2 ml-2">
          {Array.from({ length: totalSteps }).map((_, idx) => {
            const stepNum = idx + 1;
            const isCompleted = stepNum < currentStep;
            const isCurrent = stepNum === currentStep;

            return (
              <React.Fragment key={idx}>
                {idx > 0 && (
                  <div 
                    className={`w-5 sm:w-7 h-[3px] rounded-full transition-colors ${
                      stepNum <= currentStep ? 'bg-[#2A1E4D]' : 'bg-[#2A1E4D]/30'
                    }`}
                  />
                )}
                <button
                  type="button"
                  onClick={() => onSelectStep && onSelectStep(idx)}
                  className={`flex items-center justify-center transition-all ${
                    onSelectStep ? 'cursor-pointer hover:scale-110' : 'cursor-default'
                  }`}
                  title={isKhmer ? `ទៅកាន់ជំហានទី ${stepNum}` : `Go to step ${stepNum}`}
                >
                  {isCompleted ? (
                    <div className="w-6 h-6 rounded-full bg-[#6FCF6F] border-2 border-[#2A1E4D] text-[#2A1E4D] flex items-center justify-center shadow-[1px_1px_0px_#2A1E4D]">
                      <Check className="w-3.5 h-3.5 stroke-[3]" />
                    </div>
                  ) : isCurrent ? (
                    <div className="w-7 h-7 rounded-full bg-[#6C4FF6] border-2 border-[#2A1E4D] text-white flex items-center justify-center text-xs font-black shadow-[2px_2px_0px_#2A1E4D]">
                      {stepNum}
                    </div>
                  ) : (
                    <div className="w-5 h-5 rounded-full border-2 border-[#2A1E4D] bg-[#EAF2FF]" />
                  )}
                </button>
              </React.Fragment>
            );
          })}
        </div>
      </div>
    </div>
  );
};
