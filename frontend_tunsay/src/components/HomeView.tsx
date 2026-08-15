import React, { useRef, useState, useEffect } from 'react';
import { UserProfile, HomeworkProblem } from '../types';
import { TunsayAvatar } from './TunsayAvatar';
import { Mic, Camera, MessageSquare, Sparkles, BookOpen, ChevronLeft, ChevronRight, Star, GraduationCap, Footprints, Trophy, Send, ArrowRight } from 'lucide-react';
import { MOCK_PROBLEMS } from '../data/mockProblems';
import { getDisplayName } from '../utils/language';

interface HomeViewProps {
  profile: UserProfile;
  onStartVoiceChat: () => void;
  onStartScan: () => void;
  onStartChat: (problem?: HomeworkProblem, initialQuery?: string) => void;
  onSelectGrade?: (grade: UserProfile['grade']) => void;
}

export const HomeView: React.FC<HomeViewProps> = ({
  profile,
  onStartVoiceChat,
  onStartScan,
  onStartChat,
}) => {
  const isKhmer = profile.language === 'km';
  const marqueeRef = useRef<HTMLDivElement>(null);
  const [isHovered, setIsHovered] = useState(false);
  const [heroChatInput, setHeroChatInput] = useState('');

  useEffect(() => {
    if (isHovered) return;
    const interval = setInterval(() => {
      if (marqueeRef.current) {
        const { scrollLeft, scrollWidth, clientWidth } = marqueeRef.current;
        if (scrollLeft + clientWidth >= scrollWidth - 10) {
          marqueeRef.current.scrollTo({ left: 0, behavior: 'smooth' });
        } else {
          marqueeRef.current.scrollBy({ left: 300, behavior: 'smooth' });
        }
      }
    }, 3500);
    return () => clearInterval(interval);
  }, [isHovered]);

  const handleScrollLeft = () => {
    if (marqueeRef.current) {
      marqueeRef.current.scrollBy({ left: -300, behavior: 'smooth' });
    }
  };

  const handleScrollRight = () => {
    if (marqueeRef.current) {
      marqueeRef.current.scrollBy({ left: 300, behavior: 'smooth' });
    }
  };

  const handleHeroChatSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (heroChatInput.trim()) {
      onStartChat(undefined, heroChatInput.trim());
      setHeroChatInput('');
    } else {
      onStartChat();
    }
  };

  return (
    <div className="space-y-7 sm:space-y-9 animate-fadeIn pb-12 w-full max-w-full overflow-hidden">
      {/* Cyan-Mint Hero Section with Chat Input Space */}
      <div className="bg-[#6EE7D8] rounded-3xl border-3 border-[#2A1E4D] p-4 sm:p-8 lg:p-9 shadow-[4px_4px_0px_#2A1E4D] sm:shadow-[6px_6px_0px_#2A1E4D] relative overflow-hidden transition-all">
        {/* Background Decorative Pattern Circles */}
        <div className="absolute top-2 right-4 w-10 sm:w-12 h-10 sm:h-12 bg-[#FFCB3D] rounded-full border-2 border-[#2A1E4D] opacity-40 pointer-events-none" />
        <div className="absolute bottom-2 left-6 w-7 sm:w-8 h-7 sm:h-8 bg-[#3EC6E0] rounded-full border-2 border-[#2A1E4D] opacity-40 pointer-events-none" />

        <div className="relative z-10 flex flex-col items-center gap-4 sm:gap-7 text-center">
          <div className="space-y-3 sm:space-y-4 flex-1 text-[#2A1E4D] min-w-0 w-full py-1 flex flex-col items-center text-center">
            <div className="flex flex-wrap items-center justify-center gap-2">
              <div className="inline-flex items-center gap-1.5 px-3 py-1 sm:px-3.5 sm:py-1.5 rounded-full bg-[#2A1E4D] text-[#FFCB3D] text-[10px] sm:text-xs font-black border-2 border-[#2A1E4D] shadow-[2px_2px_0px_#2A1E4D]">
                <Sparkles className="w-3.5 h-3.5 text-[#FFCB3D] shrink-0" />
                <span className="truncate">{isKhmer ? 'គ្រូបង្រៀន AI កិច្ចការផ្ទះ' : 'AI Homework Companion'}</span>
              </div>
              <span className="px-2.5 py-1 bg-white text-[#2A1E4D] rounded-full border-2 border-[#2A1E4D] text-[10px] sm:text-xs font-black shadow-[1.5px_1.5px_0px_#2A1E4D]">
                {isKhmer ? `ថ្នាក់ទី ${profile.grade}` : `Grade ${profile.grade}`}
              </span>
              <span className="px-2.5 py-1 bg-[#FFCB3D] text-[#2A1E4D] rounded-full border-2 border-[#2A1E4D] text-[10px] sm:text-xs font-black shadow-[1.5px_1.5px_0px_#2A1E4D] flex items-center gap-1">
                <Star className="w-3 h-3 fill-[#2A1E4D]" />
                {profile.starsEarned}
              </span>
            </div>
            
            <h2 className="text-lg sm:text-3xl font-black font-heading leading-snug sm:leading-normal text-[#2A1E4D] drop-shadow-[1px_1px_0px_#FFFFFF] break-words text-center">
              {isKhmer 
                ? `សួស្តី ${getDisplayName(profile.name, true)}! តោះដោះស្រាយលំហាត់ជាមួយគ្នា!`
                : `Hello ${getDisplayName(profile.name, false)}! Ready to solve homework together?`}
            </h2>
            <p className="text-xs sm:text-base font-black text-[#2A1E4D]/85 leading-relaxed text-center">
              {isKhmer
                ? "ទន្សាយនឹងជួយណែនាំអ្នកជាជំហានៗយ៉ាងងាយស្រួល!"
                : "Tunsay will guide you step-by-step with ease!"}
            </p>

            {/* Chat Space Input Box where users can type and click send to navigate to homework page */}
            <form
              onSubmit={handleHeroChatSubmit}
              className="pt-2 sm:pt-3 w-full"
            >
              <div className="flex items-center gap-2 p-1.5 sm:p-2 bg-white rounded-2xl sm:rounded-3xl border-2.5 sm:border-3 border-[#2A1E4D] shadow-[3px_3px_0px_#2A1E4D] sm:shadow-[4.5px_4.5px_0px_#2A1E4D] focus-within:shadow-[5px_5px_0px_#2A1E4D] focus-within:-translate-y-0.5 transition-all">
                <input
                  type="text"
                  value={heroChatInput}
                  onChange={(e) => setHeroChatInput(e.target.value)}
                  placeholder={
                    isKhmer
                      ? "វាយសំណួរ ឬលំហាត់របស់អ្នកនៅទីនេះ... (ឧ. 15 + 27 = ?)"
                      : "Type your homework question here... (e.g. 15 + 27 = ?)"
                  }
                  className="flex-1 min-w-0 px-3 sm:px-4 py-2 sm:py-2.5 text-xs sm:text-base font-black text-[#2A1E4D] placeholder-[#2A1E4D]/45 bg-transparent border-none outline-none focus:ring-0"
                />

                {/* Send Button to Homework Page */}
                <button
                  type="submit"
                  className="px-4 sm:px-6 py-2 sm:py-2.5 bg-[#FFCB3D] hover:bg-[#ffd768] text-[#2A1E4D] rounded-xl sm:rounded-2xl font-black text-xs sm:text-base border-2 sm:border-2.5 border-[#2A1E4D] shadow-[2px_2px_0px_#2A1E4D] sm:shadow-[2.5px_2.5px_0px_#2A1E4D] hover:-translate-y-0.5 active:translate-y-0.5 transition-all cursor-pointer flex items-center gap-1.5 shrink-0"
                >
                  <span>{isKhmer ? 'ផ្ញើ' : 'Send'}</span>
                  <Send className="w-3.5 h-3.5 sm:w-4 sm:h-4 stroke-[3]" />
                </button>
              </div>
            </form>
          </div>
        </div>
      </div>

      {/* 3-Column Action Grid (Voice / Photo / Chat) in Distinct Bright Colors */}
      <div className="space-y-3.5 sm:space-y-5">
        <h3 className="text-sm sm:text-xl font-black text-[#2A1E4D] font-heading flex items-center gap-2">
          <BookOpen className="w-4 h-4 sm:w-6 sm:h-6 text-[#6C4FF6] shrink-0" />
          <span>{isKhmer ? 'តើអ្នកចង់ធ្វើអ្វីថ្ងៃនេះ?' : 'What would you like to do today?'}</span>
        </h3>

        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3 sm:gap-6">
          {/* Action 1: Voice Chat with Sayo (Sky Turquoise #3EC6E0) */}
          <button
            type="button"
            onClick={onStartVoiceChat}
            className="p-4 sm:p-6 bg-[#3EC6E0] text-[#2A1E4D] rounded-2xl sm:rounded-3xl border-2.5 sm:border-3 border-[#2A1E4D] shadow-[3px_3px_0px_#2A1E4D] sm:shadow-[5px_5px_0px_#2A1E4D] hover:-translate-x-0.5 hover:-translate-y-0.5 hover:shadow-[5px_5px_0px_#2A1E4D] active:translate-x-0.5 active:translate-y-0.5 active:shadow-[1px_1px_0px_#2A1E4D] text-left transition-all flex flex-col justify-between group cursor-pointer relative overflow-hidden"
          >
            <div>
              <div className="p-2.5 sm:p-3 bg-white rounded-xl sm:rounded-2xl border-2 sm:border-3 border-[#2A1E4D] shadow-[2px_2px_0px_#2A1E4D] w-fit text-[#2A1E4D] mb-3 sm:mb-5 group-hover:scale-110 transition-transform">
                <Mic className="w-6 h-6 sm:w-8 sm:h-8 text-[#6C4FF6]" />
              </div>
              <h4 className="text-base sm:text-xl font-black font-heading leading-tight mb-1">
                {isKhmer ? 'និយាយជាមួយទន្សាយ' : 'Voice Chat with Tunsay'}
              </h4>
            </div>
            <div className="mt-3 sm:mt-6 pt-2.5 sm:pt-4 border-t-2 border-[#2A1E4D]/30 flex items-center text-xs sm:text-sm font-black gap-1.5 group-hover:translate-x-1 transition-transform">
              <span>{isKhmer ? 'ចាប់ផ្តើមនិយាយ' : 'Start Speaking'}</span> <ChevronRight className="w-4 h-4 stroke-[3]" />
            </div>
          </button>

          {/* Action 2: Scan Homework Photo (Grass Green #6FCF6F) */}
          <button
            type="button"
            onClick={onStartScan}
            className="p-4 sm:p-6 bg-[#6FCF6F] text-[#2A1E4D] rounded-2xl sm:rounded-3xl border-2.5 sm:border-3 border-[#2A1E4D] shadow-[3px_3px_0px_#2A1E4D] sm:shadow-[5px_5px_0px_#2A1E4D] hover:-translate-x-0.5 hover:-translate-y-0.5 hover:shadow-[5px_5px_0px_#2A1E4D] active:translate-x-0.5 active:translate-y-0.5 active:shadow-[1px_1px_0px_#2A1E4D] text-left transition-all flex flex-col justify-between group cursor-pointer relative overflow-hidden"
          >
            <div>
              <div className="p-2.5 sm:p-3 bg-white rounded-xl sm:rounded-2xl border-2 sm:border-3 border-[#2A1E4D] shadow-[2px_2px_0px_#2A1E4D] w-fit text-[#2A1E4D] mb-3 sm:mb-5 group-hover:scale-110 transition-transform">
                <Camera className="w-6 h-6 sm:w-8 sm:h-8 text-[#2A1E4D]" />
              </div>
              <h4 className="text-base sm:text-xl font-black font-heading leading-tight mb-1">
                {isKhmer ? 'ស្កែនរូបថតលំហាត់' : 'Scan Homework Photo'}
              </h4>
            </div>
            <div className="mt-3 sm:mt-6 pt-2.5 sm:pt-4 border-t-2 border-[#2A1E4D]/30 flex items-center text-xs sm:text-sm font-black gap-1.5 group-hover:translate-x-1 transition-transform">
              <span>{isKhmer ? 'ថតរូបលំហាត់' : 'Take Photo'}</span> <ChevronRight className="w-4 h-4 stroke-[3]" />
            </div>
          </button>

          {/* Action 3: Ask Sayo via Chat (Sunshine Yellow #FFCB3D) */}
          <button
            type="button"
            onClick={() => onStartChat()}
            className="p-4 sm:p-6 bg-[#FFCB3D] text-[#2A1E4D] rounded-2xl sm:rounded-3xl border-2.5 sm:border-3 border-[#2A1E4D] shadow-[3px_3px_0px_#2A1E4D] sm:shadow-[5px_5px_0px_#2A1E4D] hover:-translate-x-0.5 hover:-translate-y-0.5 hover:shadow-[5px_5px_0px_#2A1E4D] active:translate-x-0.5 active:translate-y-0.5 active:shadow-[1px_1px_0px_#2A1E4D] text-left transition-all flex flex-col justify-between group cursor-pointer relative overflow-hidden sm:col-span-2 md:col-span-1"
          >
            <div>
              <div className="p-2.5 sm:p-3 bg-white rounded-xl sm:rounded-2xl border-2 sm:border-3 border-[#2A1E4D] shadow-[2px_2px_0px_#2A1E4D] w-fit text-[#2A1E4D] mb-3 sm:mb-5 group-hover:scale-110 transition-transform">
                <MessageSquare className="w-6 h-6 sm:w-8 sm:h-8 text-[#FF6FA3]" />
              </div>
              <h4 className="text-base sm:text-xl font-black font-heading leading-tight mb-1">
                {isKhmer ? 'វាយសួរ ទន្សាយ' : 'Ask Tunsay via Chat'}
              </h4>
            </div>
            <div className="mt-3 sm:mt-6 pt-2.5 sm:pt-4 border-t-2 border-[#2A1E4D]/30 flex items-center text-xs sm:text-sm font-black gap-1.5 group-hover:translate-x-1 transition-transform">
              <span>{isKhmer ? 'សួរទន្សាយ' : 'Ask Tunsay'}</span> <ChevronRight className="w-4 h-4 stroke-[3]" />
            </div>
          </button>
        </div>
      </div>

      {/* Featured Guided Homework Practice Cards */}
      <div className="space-y-4 sm:space-y-5 pt-3 sm:pt-5">
        <div className="flex items-center justify-between flex-wrap gap-3">
          <h3 className="text-base sm:text-xl font-black text-[#2A1E4D] font-heading flex items-center gap-2.5">
            <Trophy className="w-5 h-5 sm:w-6 sm:h-6 text-[#FFCB3D]" />
            {isKhmer ? 'ប្រវត្តិលំហាត់រៀនជាមួយទន្សាយ' : 'Homework History with Tunsay'}
          </h3>
          <div className="flex items-center gap-2">
            <span className="text-[11px] sm:text-xs font-black text-[#2A1E4D] bg-[#FFCB3D] px-3 py-1 rounded-full border-2 border-[#2A1E4D] shadow-[2px_2px_0px_#2A1E4D]">
              {isKhmer ? `ថ្នាក់ទី ${profile.grade} • WEG` : `Grade ${profile.grade} • WEG`}
            </span>
            <div className="flex items-center gap-1.5 ml-1">
              <button
                type="button"
                onClick={handleScrollLeft}
                aria-label="Previous problem"
                className="p-1.5 bg-white text-[#2A1E4D] hover:bg-[#3EC6E0] rounded-xl border-2 border-[#2A1E4D] shadow-[2px_2px_0px_#2A1E4D] hover:-translate-y-0.5 active:translate-y-0.5 active:shadow-[1px_1px_0px_#2A1E4D] transition-all cursor-pointer"
              >
                <ChevronLeft className="w-4 h-4 sm:w-5 sm:h-5 stroke-[3]" />
              </button>
              <button
                type="button"
                onClick={handleScrollRight}
                aria-label="Next problem"
                className="p-1.5 bg-white text-[#2A1E4D] hover:bg-[#3EC6E0] rounded-xl border-2 border-[#2A1E4D] shadow-[2px_2px_0px_#2A1E4D] hover:-translate-y-0.5 active:translate-y-0.5 active:shadow-[1px_1px_0px_#2A1E4D] transition-all cursor-pointer"
              >
                <ChevronRight className="w-4 h-4 sm:w-5 sm:h-5 stroke-[3]" />
              </button>
            </div>
          </div>
        </div>

        {/* Single Row Infinite Marquee & Manual Scrollable Container */}
        <div className="w-full relative py-2 group/slideshow">
          <button
            type="button"
            onClick={handleScrollLeft}
            className="absolute left-1 top-1/2 -translate-y-1/2 z-20 p-2.5 bg-white text-[#2A1E4D] hover:bg-[#FFCB3D] rounded-full border-3 border-[#2A1E4D] shadow-[3px_3px_0px_#2A1E4D] hover:scale-110 active:scale-95 transition-all cursor-pointer opacity-90 sm:opacity-0 group-hover/slideshow:opacity-100"
          >
            <ChevronLeft className="w-5 h-5 stroke-[3]" />
          </button>
          <button
            type="button"
            onClick={handleScrollRight}
            className="absolute right-1 top-1/2 -translate-y-1/2 z-20 p-2.5 bg-white text-[#2A1E4D] hover:bg-[#FFCB3D] rounded-full border-3 border-[#2A1E4D] shadow-[3px_3px_0px_#2A1E4D] hover:scale-110 active:scale-95 transition-all cursor-pointer opacity-90 sm:opacity-0 group-hover/slideshow:opacity-100"
          >
            <ChevronRight className="w-5 h-5 stroke-[3]" />
          </button>

          <div
            ref={marqueeRef}
            onMouseEnter={() => setIsHovered(true)}
            onMouseLeave={() => setIsHovered(false)}
            className="overflow-x-auto scrollbar-none scroll-smooth flex gap-4 sm:gap-6 py-1 px-1"
          >
            {[...MOCK_PROBLEMS, ...MOCK_PROBLEMS, ...MOCK_PROBLEMS].map((prob, idx) => (
              <div
                key={`${prob.id}-${idx}`}
                onClick={() => onStartChat(prob)}
                className="w-[240px] sm:w-[300px] shrink-0 p-4 sm:p-6 bg-white rounded-2xl sm:rounded-3xl border-2.5 sm:border-3 border-[#2A1E4D] shadow-[3px_3px_0px_#2A1E4D] sm:shadow-[4px_4px_0px_#2A1E4D] hover:-translate-y-1 hover:shadow-[5px_5px_0px_#2A1E4D] active:translate-y-0.5 active:shadow-[1px_1px_0px_#2A1E4D] transition-all cursor-pointer flex flex-col justify-between group"
              >
                <div className="space-y-3">
                  <div className="flex items-center justify-between flex-wrap gap-2">
                    <span className={`px-2.5 py-1 text-[#2A1E4D] text-xs font-black rounded-full border-2 border-[#2A1E4D] shadow-[1.5px_1.5px_0px_#2A1E4D] flex items-center gap-1.5 ${
                      prob.subject === 'math' ? 'bg-[#3EC6E0]' : prob.subject === 'science' ? 'bg-[#6FCF6F]' : 'bg-[#FFCB3D]'
                    }`}>
                      <GraduationCap className="w-3.5 h-3.5" />
                      {isKhmer 
                        ? `ថ្នាក់ទី ${prob.grade} • ${prob.subject === 'math' ? 'គណិត' : prob.subject === 'science' ? 'វិទ្យាសាស្ត្រ' : 'អង់គ្លេស'}` 
                        : `Grade ${prob.grade} • ${prob.subject === 'math' ? 'Math' : prob.subject === 'science' ? 'Science' : 'English'}`}
                    </span>
                    <span className="text-[11px] font-black text-[#2A1E4D] bg-[#FFCB3D] px-2 py-0.5 rounded-full border-2 border-[#2A1E4D]">
                      {isKhmer ? `${prob.steps.length} ជំហាន` : `${prob.steps.length} Steps`}
                    </span>
                  </div>
                  <h4 className="font-black text-sm sm:text-base text-[#2A1E4D] group-hover:text-[#6C4FF6] transition-colors font-heading line-clamp-2">
                    {isKhmer ? prob.titleKhmer : prob.titleEng}
                  </h4>
                </div>

                <div className="mt-4 pt-3 border-t-2 border-[#2A1E4D]/15 flex items-center justify-between gap-2">
                  <span className="px-3 py-1.5 bg-[#6FCF6F] text-[#2A1E4D] font-black text-xs rounded-full border-2 border-[#2A1E4D] shadow-[1.5px_1.5px_0px_#2A1E4D] group-hover:bg-[#FFCB3D] transition-colors flex items-center gap-1.5 shrink-0">
                    <Footprints className="w-3.5 h-3.5" />
                    {isKhmer ? 'ដោះស្រាយ' : 'Solve'}
                  </span>
                  <ChevronRight className="w-4 h-4 text-[#2A1E4D] stroke-[3] group-hover:translate-x-1 transition-transform shrink-0" />
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};
