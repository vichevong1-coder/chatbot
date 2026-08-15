import React, { useState, useEffect } from 'react';
import { UserProfile, Grade, Language, ChatMessage } from '../types';
import { TunsayAvatar } from './TunsayAvatar';
import { GradeSubjectSelector } from './GradeSubjectSelector';
import { ModeSwitcher } from './ModeSwitcher';
import { LanguageSwitcher } from './LanguageSwitcher';
import { Star, Award, Sparkles, User, Globe, GraduationCap, MessageSquare, Trash2, Shield, Save, CheckCircle2, Edit3 } from 'lucide-react';
import { getDisplayName } from '../utils/language';

interface ProfileViewProps {
  profile: UserProfile;
  chatMessages?: ChatMessage[];
  onClearChatMessages?: () => void;
  onUpdateProfile: (updated: Partial<UserProfile>) => void;
  onSignOut?: () => void;
}

export const ProfileView: React.FC<ProfileViewProps> = ({
  profile,
  chatMessages = [],
  onClearChatMessages,
  onUpdateProfile,
  onSignOut
}) => {
  // Local draft state for user profile settings
  const [draftName, setDraftName] = useState(profile.name);
  const [draftGrade, setDraftGrade] = useState<Grade>(profile.grade);
  const [draftLanguage, setDraftLanguage] = useState<Language>(profile.language);
  const [draftMode, setDraftMode] = useState<'student' | 'parent'>(profile.mode);

  const [isSaved, setIsSaved] = useState(false);

  // Sync state if profile prop changes
  useEffect(() => {
    setDraftName(profile.name);
    setDraftGrade(profile.grade);
    setDraftLanguage(profile.language);
    setDraftMode(profile.mode);
  }, [profile]);

  const isKhmer = draftLanguage === 'km';

  const hasChanges =
    draftName !== profile.name ||
    draftGrade !== profile.grade ||
    draftLanguage !== profile.language ||
    draftMode !== profile.mode;

  const handleSave = () => {
    onUpdateProfile({
      name: draftName,
      grade: draftGrade,
      language: draftLanguage,
      mode: draftMode,
    });
    setIsSaved(true);
    setTimeout(() => {
      setIsSaved(false);
    }, 3000);
  };

  return (
    <div className="space-y-7 sm:space-y-9 animate-fadeIn w-full max-w-full overflow-hidden pb-12">
      {/* Sunshine Yellow Hero Card (#FFCB3D) with Large Mascot Avatar */}
      <div className="bg-[#FFCB3D] rounded-3xl border-3 border-[#2A1E4D] p-4 sm:p-8 shadow-[5px_5px_0px_#2A1E4D] sm:shadow-[6px_6px_0px_#2A1E4D] flex flex-col sm:flex-row items-center gap-4 sm:gap-6 text-center sm:text-left relative overflow-hidden">
        {/* Background Decorative Circles */}
        <div className="absolute -top-4 -right-4 w-12 sm:w-16 h-12 sm:h-16 bg-[#FF6FA3] rounded-full border-2 border-[#2A1E4D] opacity-30" />
        <div className="absolute -bottom-4 -left-4 w-12 sm:w-16 h-12 sm:h-16 bg-[#3EC6E0] rounded-full border-2 border-[#2A1E4D] opacity-30" />

        <div className="p-2.5 sm:p-3 bg-white rounded-3xl border-3 border-[#2A1E4D] shadow-[3px_3px_0px_#2A1E4D] sm:shadow-[4px_4px_0px_#2A1E4D] shrink-0 transform -rotate-3">
          <TunsayAvatar size="lg" state="celebrating" showBadge={false} />
        </div>

        <div className="space-y-2 sm:space-y-3 flex-1 relative z-10 w-full min-w-0">
          <div className="inline-flex items-center gap-1.5 px-3 sm:px-3.5 py-1 rounded-full bg-[#2A1E4D] text-[#FFCB3D] text-[11px] sm:text-xs font-black border-2 border-[#2A1E4D] shadow-[2px_2px_0px_#2A1E4D]">
            <Sparkles className="w-3.5 h-3.5 text-[#FFCB3D] shrink-0" /> 
            <span className="truncate">{isKhmer ? 'សិស្សរៀនជាមួយទន្សាយ' : 'Tunsay Student'}</span>
          </div>

          <h2 className="text-xl sm:text-3xl font-black text-[#2A1E4D] font-heading drop-shadow-[1px_1px_0px_white] break-words">
            {getDisplayName(profile.name, isKhmer)}
          </h2>

          <div className="flex flex-wrap items-center justify-center sm:justify-start gap-2 pt-1">
            <span className="px-3 py-1 sm:px-3.5 sm:py-1.5 bg-white text-[#2A1E4D] rounded-full border-2 border-[#2A1E4D] text-xs font-black flex items-center gap-1.5 shadow-[2px_2px_0px_#2A1E4D]">
              <GraduationCap className="w-3.5 h-3.5 sm:w-4 sm:h-4 text-[#6C4FF6]" />
              {isKhmer ? `ថ្នាក់ទី ${profile.grade}` : `Grade ${profile.grade}`}
            </span>
            <span className="px-3 py-1 sm:px-3.5 sm:py-1.5 bg-[#3EC6E0] text-[#2A1E4D] rounded-full border-2 border-[#2A1E4D] text-xs font-black flex items-center gap-1.5 shadow-[2px_2px_0px_#2A1E4D]">
              <Sparkles className="w-3.5 h-3.5 sm:w-4 sm:h-4" />
              {isKhmer ? 'រៀនគ្រប់មុខវិជ្ជា' : 'All Subjects AI'}
            </span>
          </div>
        </div>

        {/* Stars Earned Sticker Pill Badge */}
        <div className="w-full sm:w-auto bg-[#FF6FA3] text-white p-3.5 sm:p-5 rounded-3xl border-3 border-[#2A1E4D] shadow-[4px_4px_0px_#2A1E4D] text-center space-y-0.5 sm:space-y-1 shrink-0 transform rotate-1 sm:rotate-2">
          <div className="flex items-center justify-center gap-1.5 font-black text-xl sm:text-3xl font-heading text-[#FFCB3D] drop-shadow-[2px_2px_0px_#2A1E4D]">
            <Star className="w-5 h-5 sm:w-7 sm:h-7 fill-[#FFCB3D] text-[#2A1E4D]" />
            {profile.starsEarned}
          </div>
          <p className="text-[10px] sm:text-[11px] font-black text-white uppercase tracking-wider drop-shadow-[1px_1px_0px_#2A1E4D]">
            {isKhmer ? 'ផ្កាយទទួលបាន' : 'Stars Earned'}
          </p>
        </div>
      </div>

      {/* Parent Mode Conversation History Log (Gated behind Parent Mode) */}
      {draftMode === 'parent' && (
        <div className="bg-white rounded-3xl border-3 border-[#2A1E4D] shadow-[5px_5px_0px_#2A1E4D] p-5 sm:p-7 space-y-4 animate-fadeIn">
          <div className="flex items-center justify-between flex-wrap gap-3 border-b-2 border-[#2A1E4D]/15 pb-3">
            <div className="space-y-1">
              <div className="inline-flex items-center gap-1.5 px-3 py-1 bg-[#FFCB3D] text-[#2A1E4D] rounded-full text-xs font-black border-2 border-[#2A1E4D] shadow-[1.5px_1.5px_0px_#2A1E4D]">
                <Shield className="w-3.5 h-3.5 text-[#2A1E4D]" />
                <span>{isKhmer ? 'របៀបអាណាព្យាបាល (Parent Mode)' : 'Parent Mode Active'}</span>
              </div>
              <h3 className="text-base sm:text-xl font-black text-[#2A1E4D] font-heading flex items-center gap-2 pt-1">
                <MessageSquare className="w-5 h-5 text-[#6C4FF6]" />
                <span>{isKhmer ? 'ប្រវត្តិសន្ទនាទាំងស្រុងរវាងកូន និងទន្សាយ' : 'Full Conversation History Transcript'}</span>
              </h3>
            </div>

            {onClearChatMessages && chatMessages.length > 0 && (
              <button
                type="button"
                onClick={onClearChatMessages}
                className="px-3.5 py-1.5 bg-[#FF6FA3] text-white hover:bg-red-600 rounded-xl text-xs font-black border-2 border-[#2A1E4D] shadow-[2px_2px_0px_#2A1E4D] flex items-center gap-1.5 transition-all cursor-pointer"
              >
                <Trash2 className="w-3.5 h-3.5" />
                <span>{isKhmer ? 'លុបប្រវត្តិ' : 'Clear Transcript'}</span>
              </button>
            )}
          </div>

          <p className="text-xs sm:text-sm font-bold text-[#2A1E4D]/80 leading-relaxed">
            {isKhmer 
              ? 'ប្រវត្តិសន្ទនា និងសំណួរដែលកូនបានសួរទៅកាន់ទន្សាយ AI Tutor ត្រូវបានកត់ត្រានៅទីនេះ ដើម្បីឲ្យអាណាព្យាបាលងាយស្រួលតាមដានការរៀនសូត្រ។' 
              : 'Detailed transcript log of questions and answers between student and Tunsay AI Tutor for parent monitoring.'}
          </p>

          <div className="max-h-80 overflow-y-auto space-y-3 p-3.5 sm:p-4 bg-[#F1EFFF] rounded-2xl border-2 border-[#2A1E4D] shadow-[2px_2px_0px_#2A1E4D]">
            {chatMessages.length === 0 ? (
              <div className="text-center py-6 space-y-2">
                <TunsayAvatar size="sm" state="idle" showBadge={false} />
                <p className="text-xs sm:text-sm font-black text-[#2A1E4D]">
                  {isKhmer ? 'មិនទាន់មានប្រវត្តិសន្ទនានៅឡើយទេ' : 'No conversation transcript logged yet.'}
                </p>
              </div>
            ) : (
              chatMessages.map((msg) => {
                const isUser = msg.sender === 'user';
                let text = isUser ? (msg.textEng || msg.textKhmer || '') : (isKhmer ? (msg.textKhmer || msg.textEng || '') : (msg.textEng || msg.textKhmer || ''));
                return (
                  <div
                    key={msg.id}
                    className={`p-3 sm:p-3.5 rounded-2xl border-2 border-[#2A1E4D] space-y-1 ${
                      isUser ? 'bg-[#3EC6E0]/20 ml-4 border-[#2A1E4D]' : 'bg-white mr-4 border-[#2A1E4D]'
                    }`}
                  >
                    <div className="flex items-center justify-between text-[11px] font-black">
                      <span className={`px-2 py-0.5 rounded-md border border-[#2A1E4D] uppercase text-[10px] ${
                        isUser ? 'bg-[#3EC6E0] text-[#2A1E4D]' : 'bg-[#FFCB3D] text-[#2A1E4D]'
                      }`}>
                        {isUser ? (isKhmer ? 'សិស្ស' : 'Student') : (isKhmer ? 'ទន្សាយ AI' : 'Tunsay AI')}
                      </span>
                      <span className="text-[#2A1E4D]/70">{msg.timestamp}</span>
                    </div>
                    <p className="text-xs sm:text-sm font-bold text-[#2A1E4D] leading-relaxed pt-1">
                      {text}
                    </p>
                  </div>
                );
              })
            )}
          </div>
        </div>
      )}

      {/* Editable Student Name Card */}
      <div className="bg-white rounded-3xl border-3 border-[#2A1E4D] shadow-[4px_4px_0px_#2A1E4D] p-4 sm:p-6 space-y-3">
        <label className="font-black text-base sm:text-lg text-[#2A1E4D] flex items-center gap-2 font-heading">
          <Edit3 className="w-5 h-5 text-[#6C4FF6] shrink-0" />
          <span>{isKhmer ? 'ឈ្មោះសិស្ស' : 'Student Name'}</span>
        </label>
        <input
          type="text"
          value={draftName}
          onChange={(e) => setDraftName(e.target.value)}
          placeholder={isKhmer ? 'បញ្ចូលឈ្មោះរបស់អ្នក...' : 'Enter your name...'}
          className="w-full px-4 py-3 bg-[#F8FAFC] border-3 border-[#2A1E4D] rounded-2xl font-black text-sm sm:text-base text-[#2A1E4D] focus:outline-none focus:ring-4 focus:ring-[#3EC6E0]/40 shadow-[2px_2px_0px_#2A1E4D]"
        />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 sm:gap-6">
        {/* Language Switcher Card */}
        <div className="bg-white rounded-3xl border-3 border-[#2A1E4D] shadow-[4px_4px_0px_#2A1E4D] p-4 sm:p-6 space-y-3">
          <div className="flex items-center justify-between flex-wrap gap-2">
            <h3 className="font-black text-base sm:text-lg text-[#2A1E4D] flex items-center gap-2 font-heading">
              <Globe className="w-5 h-5 text-[#6C4FF6] shrink-0" />
              <span>{isKhmer ? 'ភាសាកម្មវិធី' : 'Language'}</span>
            </h3>
            <LanguageSwitcher 
              language={draftLanguage} 
              onSelectLanguage={(lang: Language) => setDraftLanguage(lang)} 
            />
          </div>
          <p className="text-xs font-bold text-[#2A1E4D]/80">
            {isKhmer 
              ? 'ជ្រើសរើសភាសាដែលអ្នកចង់ប្រើប្រាស់នៅក្នុងកម្មវិធី' 
              : 'Select your preferred application display language'}
          </p>
        </div>

        {/* Mode Selector Card */}
        <div className="bg-white rounded-3xl border-3 border-[#2A1E4D] shadow-[4px_4px_0px_#2A1E4D] p-4 sm:p-6 space-y-3">
          <div className="flex items-center justify-between flex-wrap gap-2">
            <h3 className="font-black text-base sm:text-lg text-[#2A1E4D] flex items-center gap-2 font-heading">
              <User className="w-5 h-5 text-[#FF6FA3] shrink-0" />
              <span>{isKhmer ? 'របៀបប្រើប្រាស់' : 'User Mode'}</span>
            </h3>
            <ModeSwitcher 
              mode={draftMode} 
              language={draftLanguage}
              onToggleMode={(mode) => setDraftMode(mode)} 
            />
          </div>
          <p className="text-xs font-bold text-[#2A1E4D]/80">
            {isKhmer 
              ? 'ជ្រើសរើសរវាងរបៀបសិស្ស ឬអាណាព្យាបាលដើម្បីទទួលបានការពន្យល់សមស្រប' 
              : 'Select between Student or Parent mode for tailored explanations'}
          </p>
        </div>
      </div>

      {/* Grade Selector (Subject selection removed per user request) */}
      <GradeSubjectSelector
        currentGrade={draftGrade}
        language={draftLanguage}
        onSelectGrade={(grade: Grade) => setDraftGrade(grade)}
      />

      {/* Prominent Save Changes Button */}
      <div className="bg-white p-5 sm:p-6 rounded-3xl border-3 border-[#2A1E4D] shadow-[5px_5px_0px_#2A1E4D] flex flex-col sm:flex-row items-center justify-between gap-4">
        <div className="space-y-1 text-center sm:text-left">
          <h4 className="font-black text-base sm:text-lg text-[#2A1E4D] font-heading flex items-center justify-center sm:justify-start gap-2">
            <Save className="w-5 h-5 text-[#6C4FF6]" />
            <span>{isKhmer ? 'រក្សាទុកការកំណត់' : 'Save Profile Settings'}</span>
          </h4>
          <p className="text-xs font-bold text-[#2A1E4D]/70">
            {hasChanges 
              ? (isKhmer ? 'អ្នកមានការផ្លាស់ប្តូរដែលមិនទាន់បានរក្សាទុក!' : 'You have unsaved changes!')
              : (isKhmer ? 'ការកំណត់ទាំងអស់ទាន់សម័យ' : 'All settings are up to date')}
          </p>
        </div>

        <button
          type="button"
          onClick={handleSave}
          className={`w-full sm:w-auto px-6 py-3.5 rounded-2xl font-black text-sm sm:text-base border-3 border-[#2A1E4D] transition-all flex items-center justify-center gap-2.5 cursor-pointer ${
            isSaved
              ? 'bg-[#6FCF6F] text-[#2A1E4D] shadow-[3px_3px_0px_#2A1E4D]'
              : hasChanges
              ? 'bg-[#FF6FA3] text-white shadow-[4px_4px_0px_#2A1E4D] hover:-translate-y-0.5 active:translate-y-0.5 active:shadow-[1px_1px_0px_#2A1E4D]'
              : 'bg-[#6FCF6F] text-[#2A1E4D] shadow-[3px_3px_0px_#2A1E4D] hover:opacity-95'
          }`}
        >
          {isSaved ? (
            <>
              <CheckCircle2 className="w-5 h-5 text-[#2A1E4D]" />
              <span>{isKhmer ? 'បានរក្សាទុកជោគជ័យ!' : 'Saved Successfully!'}</span>
            </>
          ) : (
            <>
              <Save className="w-5 h-5" />
              <span>{isKhmer ? 'រក្សាទុកការផ្លាស់ប្តូរ' : 'Save Changes'}</span>
            </>
          )}
        </button>
      </div>

      {/* Sign Out / Switch Account Button */}
      {onSignOut && (
        <div className="bg-white p-5 rounded-3xl border-3 border-[#2A1E4D] shadow-[4px_4px_0px_#2A1E4D] flex items-center justify-between gap-4">
          <div>
            <h4 className="font-black text-sm sm:text-base text-[#2A1E4D]">
              {isKhmer ? 'ចាកចេញ ឬប្តូរគណនី' : 'Sign Out or Switch Account'}
            </h4>
            <p className="text-xs font-bold text-[#2A1E4D]/70">
              {isKhmer ? 'ត្រឡប់ទៅកាន់ទំព័រដើម ឬទំព័រចូលប្រើប្រាស់' : 'Return to the welcome or login page'}
            </p>
          </div>
          <button
            type="button"
            onClick={onSignOut}
            className="px-4 py-2 bg-[#EAF2FF] hover:bg-[#FFCB3D] text-[#2A1E4D] font-black text-xs sm:text-sm rounded-xl border-2 border-[#2A1E4D] shadow-[2px_2px_0px_#2A1E4D] transition-all cursor-pointer shrink-0"
          >
            {isKhmer ? 'ចាកចេញ' : 'Sign Out'}
          </button>
        </div>
      )}

      {/* Learning Journey Banner */}
      <div className="bg-[#6C4FF6] text-[#2A1E4D] p-6 sm:p-8 rounded-3xl border-3 border-[#2A1E4D] shadow-[4px_4px_0px_#2A1E4D] space-y-3">
        <div className="flex items-center gap-2 font-black text-lg text-[#FFCB3D] font-heading">
          <Award className="w-6 h-6 text-[#FFCB3D]" />
          {isKhmer ? 'អំពីកម្មវិធី ទន្សាយ' : 'About Tunsay AI Homework Tutor'}
        </div>
        <p className="text-xs sm:text-sm font-bold leading-relaxed text-white drop-shadow-[1px_1px_0px_#2A1E4D]">
          {isKhmer 
            ? 'ទន្សាយ គឺជាជំនួយការរៀនសូត្រឆ្លាតវៃសម្រាប់សិស្សានុសិស្ស។ ទន្សាយជួយបកស្រាយលំហាត់គ្រប់មុខវិជ្ជា (គណិតវិទ្យា វិទ្យាសាស្ត្រ ភាសាអង់គ្លេស និងមុខវិជ្ជាផ្សេងៗទៀត) ជាជំហានៗដោយមិនប្រាប់ចម្លើយភ្លាមៗឡើយ ដើម្បីឲ្យសិស្សចេះគិត និងយល់ដោយខ្លួនឯង!'
            : 'Tunsay is a smart learning tutor for students. Tunsay guides students through all subjects (Math, Science, English, and more) step-by-step without giving away direct answers, fostering independent thinking and deep understanding!'}
        </p>
      </div>
    </div>
  );
};
