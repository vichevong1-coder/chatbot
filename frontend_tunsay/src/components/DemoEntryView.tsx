import React, { useMemo, useState } from 'react';
import { Grade, Language } from '../types';
import { MOCK_PROBLEMS } from '../data/mockProblems';
import { TunsayAvatar } from './TunsayAvatar';
import { ArrowRight, BookOpen, Loader2, AlertCircle } from 'lucide-react';

interface DemoEntryViewProps {
  language: Language;
  onSelectLanguage: (language: Language) => void;
  /** Resolves when the demo account for this grade has a token, or rejects-as-false. */
  onStart: (grade: Grade) => Promise<boolean>;
}

/**
 * DEMO MODE ENTRY — replaces landing + login while VITE_DEMO_MODE is on.
 *
 * No account, no PIN, no school code: pick a grade and go. Behind the scenes
 * App.tsx still mints a real JWT (the gateway rejects every /chat, /problems
 * and /answers call without one), so this is a shortcut through the UI, not a
 * hole in the backend.
 *
 * LandingView and LoginView are untouched and come back the moment the flag is
 * off — nothing here is commented-out code waiting to be restored.
 */
export const DemoEntryView: React.FC<DemoEntryViewProps> = ({
  language,
  onSelectLanguage,
  onStart,
}) => {
  const isKhmer = language === 'km';
  const [grade, setGrade] = useState<Grade>(4);
  const [isStarting, setIsStarting] = useState(false);
  const [failed, setFailed] = useState(false);

  // Which grades actually have problems, read from the corpus rather than
  // hardcoded — so this stays honest as content is authored. Picking an empty
  // grade mid-demo is a bad surprise; the badge warns first.
  const problemsByGrade = useMemo(() => {
    const counts = new Map<number, number>();
    for (const p of MOCK_PROBLEMS) counts.set(p.grade, (counts.get(p.grade) ?? 0) + 1);
    return counts;
  }, []);

  const selectedCount = problemsByGrade.get(grade) ?? 0;

  const handleStart = async () => {
    setIsStarting(true);
    setFailed(false);
    const ok = await onStart(grade);
    if (!ok) {
      setFailed(true);
      setIsStarting(false);
    }
    // On success App.tsx swaps the page out, so no need to reset state.
  };

  return (
    <div className="min-h-screen w-full bg-[#EAF2FF] flex flex-col items-center justify-center p-4 sm:p-6 font-sans text-[#2A1E4D]">
      <div className="w-full max-w-lg bg-white rounded-3xl border-3 border-[#2A1E4D] shadow-[6px_6px_0px_#2A1E4D] p-6 sm:p-8 space-y-6">
        {/* Mascot + title */}
        <div className="flex flex-col items-center text-center space-y-3">
          <div className="w-20 h-20 bg-[#FFCB3D] rounded-3xl border-3 border-[#2A1E4D] shadow-[3px_3px_0px_#2A1E4D] flex items-center justify-center p-1">
            <TunsayAvatar size="lg" state="explaining" showBadge={false} />
          </div>
          <div className="space-y-1.5">
            <span className="inline-block px-3 py-0.5 bg-[#FF6FA3] text-white text-[11px] font-black rounded-full border-2 border-[#2A1E4D] shadow-[1.5px_1.5px_0px_#2A1E4D] uppercase tracking-wider">
              {isKhmer ? 'របៀបសាកល្បង' : 'Demo mode'}
            </span>
            <h1 className="text-2xl sm:text-3xl font-black font-heading">
              {isKhmer ? 'តោះរៀនជាមួយទន្សាយ!' : "Let's learn with Tunsay!"}
            </h1>
            <p className="text-xs sm:text-sm font-bold text-[#2A1E4D]/75 [text-wrap:balance]">
              {isKhmer
                ? 'មិនចាំបាច់ចុះឈ្មោះទេ។ ជ្រើសរើសថ្នាក់រៀន រួចចាប់ផ្តើមភ្លាម។'
                : 'No sign-up needed. Pick a grade and start right away.'}
            </p>
          </div>
        </div>

        {/* Language toggle */}
        <div className="grid grid-cols-2 gap-2">
          {(['km', 'en'] as Language[]).map((lang) => (
            <button
              key={lang}
              type="button"
              onClick={() => onSelectLanguage(lang)}
              className={`p-3 rounded-xl border-2 border-[#2A1E4D] font-black text-xs transition-all cursor-pointer ${
                language === lang
                  ? 'bg-[#FFCB3D] text-[#2A1E4D] shadow-[2px_2px_0px_#2A1E4D]'
                  : 'bg-white text-[#2A1E4D]/70 hover:bg-[#F8FAFC]'
              }`}
            >
              {lang === 'km' ? 'ភាសាខ្មែរ (Khmer)' : 'English'}
            </button>
          ))}
        </div>

        {/* Grade picker */}
        <div className="space-y-3 pt-1">
          <label className="text-sm font-black font-heading flex items-center gap-2">
            <BookOpen className="w-5 h-5 text-[#6C4FF6] shrink-0" />
            <span>{isKhmer ? 'ជ្រើសរើសថ្នាក់រៀន' : 'Select grade'}</span>
          </label>

          <div className="grid grid-cols-3 gap-2.5">
            {([1, 2, 3, 4, 5, 6] as Grade[]).map((g) => {
              const count = problemsByGrade.get(g) ?? 0;
              const isSelected = grade === g;
              return (
                <button
                  key={g}
                  type="button"
                  onClick={() => setGrade(g)}
                  disabled={isStarting}
                  className={`relative py-3 px-2 rounded-2xl font-black text-xs sm:text-sm border-3 border-[#2A1E4D] transition-all cursor-pointer disabled:opacity-60 ${
                    isSelected
                      ? 'bg-[#FF6FA3] text-white shadow-[2.5px_2.5px_0px_#2A1E4D] -translate-y-0.5'
                      : 'bg-[#EAF2FF] text-[#2A1E4D] hover:bg-[#FFCB3D] shadow-[2px_2px_0px_#2A1E4D]'
                  }`}
                >
                  <span className="truncate">{isKhmer ? `ថ្នាក់ទី ${g}` : `Grade ${g}`}</span>
                  {count > 0 && (
                    <span
                      className="absolute -top-2 -right-2 min-w-[22px] h-[22px] px-1 bg-[#6FCF6F] text-[#2A1E4D] text-[11px] font-black rounded-full border-2 border-[#2A1E4D] flex items-center justify-center"
                      title={isKhmer ? `${count} លំហាត់` : `${count} problems`}
                    >
                      {count}
                    </span>
                  )}
                </button>
              );
            })}
          </div>

          {/* Honest warning rather than a dead-end demo. */}
          {selectedCount === 0 && (
            <div className="p-3 bg-[#FFCB3D] rounded-2xl border-2 border-[#2A1E4D] shadow-[2px_2px_0px_#2A1E4D] flex items-start gap-2 text-xs font-bold">
              <AlertCircle className="w-4 h-4 stroke-[3] shrink-0 mt-0.5" />
              <span>
                {isKhmer
                  ? 'ថ្នាក់នេះមិនទាន់មានលំហាត់នៅឡើយទេ។ អ្នកនៅតែអាចសួរសំណួរបាន ប៉ុន្តែបញ្ជីលំហាត់នឹងទទេ។'
                  : 'No problems authored for this grade yet. You can still ask questions, but the problem list will be empty.'}
              </span>
            </div>
          )}
        </div>

        {/* Start */}
        <button
          type="button"
          onClick={handleStart}
          disabled={isStarting}
          aria-busy={isStarting}
          className="w-full py-4 bg-[#6FCF6F] hover:bg-[#5EBF5E] text-[#2A1E4D] font-black text-base rounded-2xl border-3 border-[#2A1E4D] shadow-[4px_4px_0px_#2A1E4D] hover:-translate-y-0.5 active:translate-y-0.5 transition-all cursor-pointer flex items-center justify-center gap-2 disabled:opacity-60 disabled:hover:translate-y-0"
        >
          {isStarting ? (
            <>
              <Loader2 className="w-5 h-5 stroke-[3] animate-spin" />
              <span>{isKhmer ? 'កំពុងរៀបចំ...' : 'Getting ready...'}</span>
            </>
          ) : (
            <>
              <span>{isKhmer ? 'ចាប់ផ្តើមរៀន' : 'Start learning'}</span>
              <ArrowRight className="w-5 h-5 stroke-[3]" />
            </>
          )}
        </button>

        {failed && (
          <div className="p-3.5 bg-[#FF6FA3] text-white rounded-2xl border-3 border-[#2A1E4D] shadow-[3px_3px_0px_#2A1E4D] flex items-start gap-2 font-black text-sm">
            <AlertCircle className="w-5 h-5 stroke-[3] shrink-0 mt-0.5" />
            <span>
              {isKhmer
                ? 'មិនអាចភ្ជាប់ទៅម៉ាស៊ីនមេបានទេ។ ពិនិត្យមើលថា gateway និង auth_service កំពុងដំណើរការ។'
                : "Couldn't reach the backend. Check that the gateway and auth_service are running."}
            </span>
          </div>
        )}
      </div>

      <p className="mt-4 text-[11px] font-bold text-[#2A1E4D]/55 text-center max-w-lg">
        {isKhmer
          ? 'ការចូលប្រើប្រាស់ត្រូវបានរំលងសម្រាប់ការសាកល្បង (VITE_DEMO_MODE)។'
          : 'Login is skipped for the demo (VITE_DEMO_MODE). Set it to "false" to restore the real sign-in flow.'}
      </p>
    </div>
  );
};
