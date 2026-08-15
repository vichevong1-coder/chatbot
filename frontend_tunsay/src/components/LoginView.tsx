import React, { useState } from 'react';
import { UserProfile, Grade, Language } from '../types';
import { registerOrLogin } from '../api/client';
import { TunsayAvatar } from './TunsayAvatar';
import { 
  School, 
  User, 
  ArrowLeft, 
  Sparkles, 
  CheckCircle2, 
  HelpCircle, 
  Lock, 
  KeyRound, 
  Mail, 
  GraduationCap, 
  ArrowRight,
  Zap,
  BookOpen,
  Check
} from 'lucide-react';

interface LoginViewProps {
  language: Language;
  onSelectLanguage: (lang: Language) => void;
  onLoginSuccess: (profile: Partial<UserProfile>) => void;
  onBackToLanding: () => void;
}

export const LoginView: React.FC<LoginViewProps> = ({
  language,
  onSelectLanguage,
  onLoginSuccess,
  onBackToLanding,
}) => {
  const isKhmer = language === 'km';

  // Entry selection state: 'select' | 'school-code' | 'public-signup' | 'returning-login'
  const [flowMode, setFlowMode] = useState<'select' | 'school-code' | 'public-signup' | 'returning-login'>('select');

  // Form Fields
  const [schoolCode, setSchoolCode] = useState('');
  const [schoolCodeConfirmed, setSchoolCodeConfirmed] = useState(false);
  const [studentName, setStudentName] = useState('');
  const [pin, setPin] = useState('');
  const [grade, setGrade] = useState<Grade>(4);
  const [classNameOption, setClassNameOption] = useState<string>('Class A');
  const [parentContact, setParentContact] = useState('');
  const [publicSignupStep, setPublicSignupStep] = useState<1 | 2 | 3>(1);

  // Helper Modal for "Don't have a code?"
  const [showCodeHelpModal, setShowCodeHelpModal] = useState(false);

  // Mock resolved school code data
  const isSchoolCodeValid = schoolCode.trim().toUpperCase().startsWith('TUNSAY') || schoolCode.trim().toUpperCase().startsWith('SAYO') || schoolCode.trim().length >= 4;
  const resolvedSchool = isSchoolCodeValid ? {
    schoolName: 'Primary Learning Campus',
    grade: 4 as Grade,
    className: 'Class 4A (Primary)',
    subjectTrack: isKhmer ? 'គណិតវិទ្យា វិទ្យាសាស្ត្រ និងអង់គ្លេស' : 'Math, Science & English Track',
  } : null;

  // DEV Auto-fill handler
  const handleFillDemoData = () => {
    if (flowMode === 'select' || flowMode === 'school-code') {
      setFlowMode('school-code');
      setSchoolCode('TUNSAY-G4-DEMO');
      setSchoolCodeConfirmed(true);
      setStudentName('សុជា (Sochea)');
      setPin('1234');
    } else if (flowMode === 'public-signup') {
      setStudentName('សុជា (Sochea)');
      setGrade(4);
      setParentContact('parent@tunsay.app');
      setPin('1234');
      setPublicSignupStep(3);
    } else if (flowMode === 'returning-login') {
      setSchoolCode('TUNSAY-G4-DEMO');
      setStudentName('សុជា (Sochea)');
      setPin('1234');
    }
  };

  // P1.10: the three flows now hit the real auth_service through the gateway
  // (school code + optional PIN — no passwords, .claude/contracts.md §4).
  // When the backend is unreachable, registerOrLogin returns null and we fall
  // back to local state so the offline demo keeps working.
  const handleFinishSchoolCodeLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!studentName.trim()) return;
    const profile = await registerOrLogin({
      studentName: studentName.trim(),
      schoolCode: schoolCode.trim() || undefined,
      pin: pin || undefined,
      language,
    });
    onLoginSuccess({
      name: studentName,
      grade: resolvedSchool?.grade || 4,
      language,
      mode: 'student',
      ...(profile ?? {}),
    });
  };

  const handleFinishPublicSignup = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!studentName.trim()) return;
    const profile = await registerOrLogin({
      studentName: studentName.trim(),
      grade,
      className: classNameOption,
      parentContact: parentContact.trim() || undefined,
      pin: pin || undefined,
      language,
    });
    onLoginSuccess({
      name: studentName,
      grade,
      language,
      mode: 'student',
      ...(profile ?? {}),
    });
  };

  const handleFinishReturningLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    const profile = await registerOrLogin({
      studentName: (studentName || 'សុជា (Sochea)').trim(),
      schoolCode: schoolCode.trim() || undefined,
      pin: pin || undefined,
      language,
    });
    onLoginSuccess({
      name: studentName || 'សុជា (Sochea)',
      grade: 4,
      language,
      mode: 'student',
      ...(profile ?? {}),
    });
  };

  return (
    <div className="min-h-screen bg-[#EAF2FF]/60 flex flex-col justify-between p-4 sm:p-6 lg:p-8 font-sans">
      {/* Top Bar with Language Toggle & Back to Welcome */}
      <div className="max-w-2xl mx-auto w-full flex items-center justify-between gap-4 mb-4">
        <button
          type="button"
          onClick={flowMode === 'select' ? onBackToLanding : () => setFlowMode('select')}
          className="px-3.5 py-2 bg-white hover:bg-[#FFCB3D] text-[#2A1E4D] rounded-2xl border-2.5 border-[#2A1E4D] shadow-[2.5px_2.5px_0px_#2A1E4D] font-black text-xs sm:text-sm flex items-center gap-1.5 transition-all cursor-pointer"
        >
          <ArrowLeft className="w-4 h-4 stroke-[3]" />
          <span>{flowMode === 'select' ? (isKhmer ? 'ត្រឡប់ក្រោយ' : 'Welcome Page') : (isKhmer ? 'ជ្រើសរើសឡើងវិញ' : 'Back')}</span>
        </button>

        {/* Language Switcher */}
        <div className="flex items-center p-1 bg-white rounded-2xl border-2.5 border-[#2A1E4D] shadow-[2px_2px_0px_#2A1E4D]">
          <button
            type="button"
            onClick={() => onSelectLanguage('km')}
            className={`px-3 py-1 text-xs font-black rounded-xl transition-all cursor-pointer ${
              isKhmer ? 'bg-[#6C4FF6] text-white shadow-[1px_1px_0px_#2A1E4D]' : 'text-[#2A1E4D]'
            }`}
          >
            ខ្មែរ
          </button>
          <button
            type="button"
            onClick={() => onSelectLanguage('en')}
            className={`px-3 py-1 text-xs font-black rounded-xl transition-all cursor-pointer ${
              !isKhmer ? 'bg-[#6C4FF6] text-white shadow-[1px_1px_0px_#2A1E4D]' : 'text-[#2A1E4D]'
            }`}
          >
            EN
          </button>
        </div>
      </div>

      {/* Main Form Container */}
      <div className="max-w-md sm:max-w-lg mx-auto w-full bg-white rounded-3xl border-2.5 sm:border-3 border-[#2A1E4D] shadow-[4px_4px_0px_#2A1E4D] sm:shadow-[6px_6px_0px_#2A1E4D] p-5 sm:p-8 space-y-5 sm:space-y-6 my-auto relative overflow-hidden">
        
        {/* Header Mascot & Greeting */}
        <div className="text-center space-y-3">
          <div className="w-20 h-20 mx-auto bg-[#FFCB3D] rounded-3xl border-3 border-[#2A1E4D] shadow-[3px_3px_0px_#2A1E4D] flex items-center justify-center p-2 relative">
            <TunsayAvatar size="md" state="encouraging" showBadge={false} />
            <div className="absolute -bottom-2 -right-2 bg-[#6FCF6F] p-1.5 rounded-full border-2 border-[#2A1E4D]">
              <Sparkles className="w-4 h-4 text-[#2A1E4D]" />
            </div>
          </div>

          <h1 className="text-2xl sm:text-3xl font-black font-heading text-[#2A1E4D] leading-snug sm:leading-relaxed [text-wrap:balance]">
            {flowMode === 'select' && (isKhmer ? 'តោះចាប់ផ្តើមរៀន!' : "Let's Get Started!")}
            {flowMode === 'school-code' && (isKhmer ? 'បញ្ចូលលេខកូដសាលារៀន' : 'Enter School Code')}
            {flowMode === 'public-signup' && (isKhmer ? 'ចុះឈ្មោះរៀនដោយខ្លួនឯង' : 'Self Sign-up')}
            {flowMode === 'returning-login' && (isKhmer ? 'ចូលប្រើប្រាស់គណនី' : 'Welcome Back!')}
          </h1>

          <p className="text-xs sm:text-sm font-bold text-[#2A1E4D]/75 leading-relaxed [text-wrap:balance]">
            {flowMode === 'select' && (isKhmer ? 'ជ្រើសរើសវិធីចូលរៀនជាមួយទន្សាយ' : 'Choose how you want to join Tunsay')}
            {flowMode === 'school-code' && (isKhmer ? 'បញ្ចូលលេខកូដដែលទទួលបានពីគ្រូបង្រៀន' : 'Enter the code provided by your teacher')}
            {flowMode === 'public-signup' && (isKhmer ? 'បង្កើតគណនីសម្រាប់សិស្សសេរី' : 'Create an independent student profile')}
            {flowMode === 'returning-login' && (isKhmer ? 'បញ្ចូលលេខកូដ ឬឈ្មោះ និង PIN' : 'Enter your credentials to log in')}
          </p>
        </div>

        {/* FLOW 1: ENTRY CHOICE CARDS */}
        {flowMode === 'select' && (
          <div className="space-y-4 pt-2">
            {/* Option A: School Code Card */}
            <button
              type="button"
              onClick={() => {
                setFlowMode('school-code');
                setSchoolCodeConfirmed(false);
              }}
              className="w-full p-4 sm:p-5 bg-[#EAF2FF] hover:bg-[#FFCB3D] text-left rounded-2xl border-3 border-[#2A1E4D] shadow-[4px_4px_0px_#2A1E4D] hover:-translate-y-0.5 active:translate-y-0.5 transition-all cursor-pointer group flex items-start gap-4"
            >
              <div className="w-12 h-12 bg-[#6C4FF6] text-white rounded-2xl border-2 border-[#2A1E4D] shadow-[2px_2px_0px_#2A1E4D] flex items-center justify-center shrink-0 mt-0.5">
                <School className="w-6 h-6" />
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center justify-between gap-2">
                  <h3 className="text-base font-black font-heading text-[#2A1E4D] leading-snug">
                    {isKhmer ? 'ខ្ញុំមានលេខកូដសាលារៀន' : 'I have a school code'}
                  </h3>
                  <span className="px-2 py-0.5 bg-[#6C4FF6] text-white text-[10px] font-black rounded-md border border-[#2A1E4D] shrink-0">
                    CODE
                  </span>
                </div>
                <p className="text-xs font-bold text-[#2A1E4D]/80 mt-1 leading-relaxed">
                  {isKhmer ? 'គ្រូបង្រៀនបានផ្តល់លេខកូដថ្នាក់រៀនសម្រាប់អ្នក' : 'Your teacher provided a code for your class.'}
                </p>
              </div>
            </button>

            {/* Option B: Public Self-Signup Card */}
            <button
              type="button"
              onClick={() => setFlowMode('public-signup')}
              className="w-full p-4 sm:p-5 bg-[#F8FAFC] hover:bg-[#3EC6E0] text-left rounded-2xl border-3 border-[#2A1E4D] shadow-[4px_4px_0px_#2A1E4D] hover:-translate-y-0.5 active:translate-y-0.5 transition-all cursor-pointer group flex items-start gap-4"
            >
              <div className="w-12 h-12 bg-[#FFCB3D] text-[#2A1E4D] rounded-2xl border-2 border-[#2A1E4D] shadow-[2px_2px_0px_#2A1E4D] flex items-center justify-center shrink-0 font-black mt-0.5">
                <User className="w-6 h-6 stroke-[2.5]" />
              </div>
              <div className="flex-1 min-w-0">
                <h3 className="text-base font-black font-heading text-[#2A1E4D] leading-snug">
                  {isKhmer ? 'ខ្ញុំចុះឈ្មោះដោយខ្លួនឯង' : "I'm signing up on my own"}
                </h3>
                <p className="text-xs font-bold text-[#2A1E4D]/80 mt-1 leading-relaxed">
                  {isKhmer ? 'អ្នកនឹងជ្រើសរើសថ្នាក់រៀន និងភាសានៅជំហានបន្ទាប់' : "You'll pick your grade and language next."}
                </p>
              </div>
            </button>

            {/* Returning User Link */}
            <div className="pt-3 text-center border-t-2 border-[#2A1E4D]/10">
              <button
                type="button"
                onClick={() => setFlowMode('returning-login')}
                className="text-xs font-black text-[#6C4FF6] hover:underline cursor-pointer"
              >
                {isKhmer ? 'មានគណនីរួចហើយ? ចូលប្រើប្រាស់នៅទីនេះ' : 'Already have an account? Log in here'}
              </button>
            </div>
          </div>
        )}

        {/* FLOW 2: SCHOOL CODE PATH */}
        {flowMode === 'school-code' && (
          <form onSubmit={handleFinishSchoolCodeLogin} className="space-y-4 pt-1">
            {!schoolCodeConfirmed ? (
              /* Step 1: Code Input & Confirmation Card */
              <div className="space-y-4">
                <div className="space-y-1.5">
                  <label className="text-xs font-black text-[#2A1E4D] uppercase tracking-wider flex items-center justify-between">
                    <span>{isKhmer ? 'លេខកូដសាលារៀន ឬថ្នាក់រៀន' : 'School / Class Code'}</span>
                    <button
                      type="button"
                      onClick={() => setShowCodeHelpModal(true)}
                      className="text-[#6C4FF6] text-[11px] font-black underline flex items-center gap-1 cursor-pointer"
                    >
                      <HelpCircle className="w-3.5 h-3.5" />
                      <span>{isKhmer ? 'គ្មានលេខកូដ?' : "Don't have a code?"}</span>
                    </button>
                  </label>
                  <div className="relative">
                    <input
                      type="text"
                      value={schoolCode}
                      onChange={(e) => {
                        setSchoolCode(e.target.value.toUpperCase());
                        setSchoolCodeConfirmed(false);
                      }}
                      placeholder="e.g. TUNSAY-G4-DEMO"
                      className="w-full px-4 py-3.5 bg-[#EAF2FF] rounded-2xl border-3 border-[#2A1E4D] text-base font-black text-[#2A1E4D] placeholder-[#2A1E4D]/40 uppercase tracking-wide focus:bg-white focus:outline-none focus:ring-2 focus:ring-[#6C4FF6]"
                      required
                    />
                    {isSchoolCodeValid && (
                      <CheckCircle2 className="w-6 h-6 text-[#6FCF6F] absolute right-3.5 top-1/2 -translate-y-1/2 stroke-[2.5]" />
                    )}
                  </div>
                </div>

                {/* Read-Only Confirmation Card */}
                {isSchoolCodeValid && resolvedSchool ? (
                  <div className="p-4 bg-[#ECFDF5] rounded-2xl border-3 border-[#2A1E4D] shadow-[4px_4px_0px_#2A1E4D] space-y-3.5 animate-fadeIn">
                    <div className="flex items-start gap-3">
                      <div className="w-10 h-10 bg-[#6FCF6F] text-[#2A1E4D] rounded-xl border-2 border-[#2A1E4D] flex items-center justify-center shrink-0">
                        <CheckCircle2 className="w-6 h-6 stroke-[2.5]" />
                      </div>
                      <div>
                        <div className="text-[11px] font-black text-[#059669] uppercase tracking-wider">
                          {isKhmer ? 'រកឃើញថ្នាក់រៀនរបស់អ្នក!' : 'Class Found!'}
                        </div>
                        <h4 className="text-base font-black font-heading text-[#2A1E4D] leading-snug">
                          {isKhmer ? 'តើនេះជាថ្នាក់របស់អ្នកមែនទេ?' : 'Is this your class?'}
                        </h4>
                      </div>
                    </div>

                    <div className="bg-white rounded-xl border-2 border-[#2A1E4D] p-3.5 space-y-2 text-xs font-bold text-[#2A1E4D]">
                      <div className="flex items-center gap-2">
                        <School className="w-4 h-4 text-[#6C4FF6] shrink-0" />
                        <span className="font-black text-sm">{resolvedSchool.schoolName}</span>
                      </div>
                      <div className="flex items-center gap-2 text-[#2A1E4D]/80">
                        <GraduationCap className="w-4 h-4 text-[#FF6FA3] shrink-0" />
                        <span className="px-2 py-0.5 bg-[#EAF2FF] rounded-md border border-[#2A1E4D] font-extrabold">
                          {isKhmer ? `ថ្នាក់ទី ${resolvedSchool.grade}` : `Grade ${resolvedSchool.grade}`}
                        </span>
                        <span className="font-extrabold">{resolvedSchool.className}</span>
                      </div>
                      <div className="flex items-center gap-2 text-[#2A1E4D]/70 pt-1 border-t border-[#2A1E4D]/10">
                        <BookOpen className="w-3.5 h-3.5 text-[#3EC6E0] shrink-0" />
                        <span className="text-[11px] font-medium">{resolvedSchool.subjectTrack}</span>
                      </div>
                    </div>

                    <button
                      type="button"
                      onClick={() => setSchoolCodeConfirmed(true)}
                      className="w-full py-3.5 bg-[#FFCB3D] hover:bg-[#FFD768] text-[#2A1E4D] font-black text-sm rounded-xl border-2 border-[#2A1E4D] shadow-[2.5px_2.5px_0px_#2A1E4D] hover:-translate-y-0.5 active:translate-y-0.5 transition-all cursor-pointer flex items-center justify-center gap-2"
                    >
                      <span>{isKhmer ? 'បាទ/ចាស មែនហើយ →' : "Yes, that's me →"}</span>
                    </button>

                    <div className="text-center pt-0.5">
                      <button
                        type="button"
                        onClick={() => {
                          setSchoolCode('');
                          setSchoolCodeConfirmed(false);
                        }}
                        className="text-xs font-extrabold text-[#6C4FF6] hover:underline cursor-pointer"
                      >
                        {isKhmer ? 'លេខកូដមិនត្រឹមត្រូវ? ប្តូរលេខកូដ' : 'Wrong code? Edit code'}
                      </button>
                    </div>
                  </div>
                ) : (
                  <div className="p-3 bg-[#F8FAFC] rounded-2xl border-2 border-dashed border-[#2A1E4D]/30 text-center text-xs text-[#2A1E4D]/70 font-semibold">
                    {isKhmer 
                      ? 'បញ្ចូលលេខកូដ ៤ ខ្ទង់ឡើងទៅ (ឧ. TUNSAY-G4-DEMO)' 
                      : 'Enter a valid school code (e.g. TUNSAY-G4-DEMO)'}
                  </div>
                )}
              </div>
            ) : (
              /* Step 2: Confirmed Badge + Name & PIN fields */
              <div className="space-y-4 animate-fadeIn">
                {/* Confirmed Class Header Summary */}
                <div className="p-3 bg-[#ECFDF5] rounded-2xl border-2 border-[#2A1E4D] flex items-center justify-between gap-2 shadow-[2px_2px_0px_#2A1E4D]">
                  <div className="flex items-center gap-2 min-w-0">
                    <div className="w-7 h-7 bg-[#6FCF6F] text-[#2A1E4D] rounded-lg border border-[#2A1E4D] flex items-center justify-center shrink-0">
                      <Check className="w-4 h-4 stroke-[3]" />
                    </div>
                    <div className="text-xs truncate">
                      <span className="font-black text-[#2A1E4D]">{resolvedSchool?.schoolName}</span>
                      <span className="text-[#2A1E4D]/80 ml-1.5 font-extrabold">({isKhmer ? `ថ្នាក់ទី ${resolvedSchool?.grade}` : `Grade ${resolvedSchool?.grade}`})</span>
                    </div>
                  </div>
                  <button
                    type="button"
                    onClick={() => setSchoolCodeConfirmed(false)}
                    className="text-[11px] font-black text-[#6C4FF6] underline hover:text-[#5839EE] shrink-0 cursor-pointer"
                  >
                    {isKhmer ? 'ប្តូរ' : 'Change'}
                  </button>
                </div>

                {/* Student Name */}
                <div className="space-y-1.5">
                  <label className="text-xs font-black text-[#2A1E4D] uppercase tracking-wider">
                    {isKhmer ? 'ឈ្មោះសិស្ស' : "Student's Name"}
                  </label>
                  <input
                    type="text"
                    value={studentName}
                    onChange={(e) => setStudentName(e.target.value)}
                    placeholder={isKhmer ? 'ឧ. សុជា (Sochea)' : 'e.g. Sochea'}
                    className="w-full px-4 py-3.5 bg-[#F8FAFC] rounded-2xl border-3 border-[#2A1E4D] text-base font-bold text-[#2A1E4D] focus:bg-white focus:outline-none focus:ring-2 focus:ring-[#6C4FF6]"
                    required
                  />
                </div>

                {/* Optional PIN */}
                <div className="space-y-1.5">
                  <label className="text-xs font-black text-[#2A1E4D] uppercase tracking-wider flex items-center gap-1">
                    <KeyRound className="w-3.5 h-3.5 text-[#6C4FF6]" />
                    <span>{isKhmer ? 'លេខ PIN សម្ងាត់ (៤ ខ្ទង់)' : 'Simple 4-digit PIN'}</span>
                  </label>
                  <input
                    type="password"
                    maxLength={4}
                    value={pin}
                    onChange={(e) => setPin(e.target.value)}
                    placeholder="1 2 3 4"
                    className="w-full px-4 py-3 bg-[#F8FAFC] rounded-2xl border-3 border-[#2A1E4D] text-base font-bold text-[#2A1E4D] tracking-widest focus:bg-white focus:outline-none"
                  />
                </div>

                {/* Submit Button */}
                <button
                  type="submit"
                  disabled={!studentName.trim()}
                  className="w-full py-4 bg-[#FFCB3D] hover:bg-[#FFD768] text-[#2A1E4D] font-black text-base rounded-2xl border-3 border-[#2A1E4D] shadow-[4px_4px_0px_#2A1E4D] hover:-translate-y-0.5 active:translate-y-0.5 transition-all cursor-pointer flex items-center justify-center gap-2 mt-2 disabled:opacity-50"
                >
                  <span>{isKhmer ? 'ចូលរៀនជាមួយទន្សាយ' : 'Start Learning with Tunsay'}</span>
                  <ArrowRight className="w-5 h-5 stroke-[3]" />
                </button>
              </div>
            )}
          </form>
        )}

        {/* FLOW 3: PUBLIC SELF-SIGNUP PATH */}
        {flowMode === 'public-signup' && (
          <form onSubmit={handleFinishPublicSignup} className="space-y-4 pt-1">
            {/* Step Progress Indicator */}
            <div className="flex items-center justify-between gap-1 pb-2 border-b-2 border-[#2A1E4D]/10">
              <div className="flex items-center gap-1.5 text-xs font-black text-[#2A1E4D]">
                <span className="w-5 h-5 bg-[#3EC6E0] text-white rounded-full flex items-center justify-center text-[11px]">
                  {publicSignupStep}
                </span>
                <span>
                  {publicSignupStep === 1 && (isKhmer ? 'ជំហានទី ១: ឈ្មោះសិស្ស' : 'Step 1: Your Name')}
                  {publicSignupStep === 2 && (isKhmer ? 'ជំហានទី ២: ថ្នាក់ & បន្ទប់' : 'Step 2: Grade & Class')}
                  {publicSignupStep === 3 && (isKhmer ? 'ជំហានទី ៣: ព័ត៌មាន & PIN' : 'Step 3: Contact & PIN')}
                </span>
              </div>
              <div className="text-[11px] font-extrabold text-[#2A1E4D]/60">
                {publicSignupStep} / 3
              </div>
            </div>

            {/* Step 1: Name & Preferred Language */}
            {publicSignupStep === 1 && (
              <div className="space-y-4 animate-fadeIn">
                <div className="space-y-1.5">
                  <label className="text-xs font-black text-[#2A1E4D] uppercase tracking-wider">
                    {isKhmer ? 'តើអ្នកឈ្មោះអ្វី?' : 'What is your name?'}
                  </label>
                  <input
                    type="text"
                    value={studentName}
                    onChange={(e) => setStudentName(e.target.value)}
                    placeholder={isKhmer ? 'ឧ. សុជា (Sochea)' : 'e.g. Sochea'}
                    className="w-full px-4 py-3.5 bg-[#F8FAFC] rounded-2xl border-3 border-[#2A1E4D] text-base font-bold text-[#2A1E4D] focus:bg-white focus:outline-none focus:ring-2 focus:ring-[#6C4FF6]"
                    required
                  />
                </div>

                <div className="space-y-1.5">
                  <label className="text-xs font-black text-[#2A1E4D] uppercase tracking-wider">
                    {isKhmer ? 'ភាសារៀនសូត្រចម្បង' : 'Preferred Learning Language'}
                  </label>
                  <div className="grid grid-cols-2 gap-2">
                    <button
                      type="button"
                      onClick={() => onSelectLanguage('km')}
                      className={`p-3 rounded-xl border-2 border-[#2A1E4D] font-black text-xs transition-all cursor-pointer ${
                        isKhmer ? 'bg-[#FFCB3D] text-[#2A1E4D] shadow-[2px_2px_0px_#2A1E4D]' : 'bg-white text-[#2A1E4D]/70'
                      }`}
                    >
                      ភាសាខ្មែរ (Khmer)
                    </button>
                    <button
                      type="button"
                      onClick={() => onSelectLanguage('en')}
                      className={`p-3 rounded-xl border-2 border-[#2A1E4D] font-black text-xs transition-all cursor-pointer ${
                        !isKhmer ? 'bg-[#FFCB3D] text-[#2A1E4D] shadow-[2px_2px_0px_#2A1E4D]' : 'bg-white text-[#2A1E4D]/70'
                      }`}
                    >
                      English
                    </button>
                  </div>
                </div>

                <button
                  type="button"
                  disabled={!studentName.trim()}
                  onClick={() => setPublicSignupStep(2)}
                  className="w-full py-3.5 bg-[#3EC6E0] hover:bg-[#32B4CD] text-white font-black text-sm rounded-2xl border-3 border-[#2A1E4D] shadow-[3px_3px_0px_#2A1E4D] disabled:opacity-50 cursor-pointer flex items-center justify-center gap-2 mt-2"
                >
                  <span>{isKhmer ? 'បន្តទៅជ្រើសរើសថ្នាក់ →' : 'Next: Choose Grade & Class →'}</span>
                </button>
              </div>
            )}

            {/* Step 2: Grade & Class Selection */}
            {publicSignupStep === 2 && (
              <div className="space-y-4 animate-fadeIn">
                <div className="space-y-1.5">
                  <label className="text-xs font-black text-[#2A1E4D] uppercase tracking-wider">
                    {isKhmer ? 'ជ្រើសរើសថ្នាក់រៀន (ថ្នាក់ទី ១–៦)' : 'Select Grade (Grades 1–6)'}
                  </label>
                  <div className="grid grid-cols-3 gap-2">
                    {([1, 2, 3, 4, 5, 6] as Grade[]).map((g) => (
                      <button
                        key={g}
                        type="button"
                        onClick={() => setGrade(g)}
                        className={`p-3 rounded-2xl border-3 border-[#2A1E4D] font-black text-sm transition-all cursor-pointer ${
                          grade === g
                            ? 'bg-[#FFCB3D] text-[#2A1E4D] shadow-[3px_3px_0px_#2A1E4D] -translate-y-0.5'
                            : 'bg-white text-[#2A1E4D] hover:bg-[#EAF2FF]'
                        }`}
                      >
                        {isKhmer ? `ថ្នាក់ទី ${g}` : `Grade ${g}`}
                      </button>
                    ))}
                  </div>
                </div>

                <div className="space-y-1.5">
                  <label className="text-xs font-black text-[#2A1E4D] uppercase tracking-wider">
                    {isKhmer ? 'ជ្រើសរើសបន្ទប់ / កម្រិត' : 'Select Class / Section'}
                  </label>
                  <div className="grid grid-cols-2 gap-2">
                    {['Class A', 'Class B', 'Class C', 'Home Study'].map((cls) => (
                      <button
                        key={cls}
                        type="button"
                        onClick={() => setClassNameOption(cls)}
                        className={`p-2.5 rounded-xl border-2 border-[#2A1E4D] font-bold text-xs transition-all cursor-pointer ${
                          classNameOption === cls
                            ? 'bg-[#6C4FF6] text-white shadow-[2px_2px_0px_#2A1E4D]'
                            : 'bg-white text-[#2A1E4D] hover:bg-[#F8FAFC]'
                        }`}
                      >
                        {cls}
                      </button>
                    ))}
                  </div>
                </div>

                <div className="flex gap-2 pt-1">
                  <button
                    type="button"
                    onClick={() => setPublicSignupStep(1)}
                    className="w-1/3 py-3 bg-white hover:bg-[#F8FAFC] text-[#2A1E4D] font-black text-xs rounded-2xl border-2.5 border-[#2A1E4D] cursor-pointer"
                  >
                    {isKhmer ? 'ត្រឡប់' : 'Back'}
                  </button>
                  <button
                    type="button"
                    onClick={() => setPublicSignupStep(3)}
                    className="w-2/3 py-3 bg-[#3EC6E0] hover:bg-[#32B4CD] text-white font-black text-sm rounded-2xl border-3 border-[#2A1E4D] shadow-[3px_3px_0px_#2A1E4D] flex items-center justify-center gap-1 cursor-pointer"
                  >
                    <span>{isKhmer ? 'បន្ត →' : 'Next →'}</span>
                  </button>
                </div>
              </div>
            )}

            {/* Step 3: Parent Contact & PIN + Summary */}
            {publicSignupStep === 3 && (
              <div className="space-y-4 animate-fadeIn">
                {/* Profile Summary Card */}
                <div className="p-3.5 bg-[#ECFDF5] rounded-2xl border-2 border-[#2A1E4D] shadow-[3px_3px_0px_#2A1E4D] space-y-1.5">
                  <div className="text-[11px] font-black text-[#059669] uppercase tracking-wider">
                    {isKhmer ? 'ពិនិត្យប្រវត្តិរូបសង្ខេប' : 'Profile Preview'}
                  </div>
                  <div className="flex items-center justify-between text-xs font-bold text-[#2A1E4D]">
                    <span className="font-black text-sm text-[#2A1E4D]">{studentName}</span>
                    <span className="px-2 py-0.5 bg-[#FFCB3D] rounded-md border border-[#2A1E4D] text-[#2A1E4D]">
                      {isKhmer ? `ថ្នាក់ទី ${grade}` : `Grade ${grade}`} • {classNameOption}
                    </span>
                  </div>
                </div>

                <div className="space-y-1.5">
                  <label className="text-xs font-black text-[#2A1E4D] uppercase tracking-wider">
                    {isKhmer ? 'អ៊ីមែល ឬលេខទូរស័ព្ទអាណាព្យាបាល' : 'Parent / Guardian Contact'}
                  </label>
                  <input
                    type="text"
                    value={parentContact}
                    onChange={(e) => setParentContact(e.target.value)}
                    placeholder="parent@example.com / 012 345 678"
                    className="w-full px-4 py-3 bg-[#F8FAFC] rounded-2xl border-3 border-[#2A1E4D] text-sm font-bold text-[#2A1E4D] focus:bg-white focus:outline-none"
                    required
                  />
                </div>

                <div className="space-y-1.5">
                  <label className="text-xs font-black text-[#2A1E4D] uppercase tracking-wider flex items-center gap-1">
                    <KeyRound className="w-3.5 h-3.5 text-[#6C4FF6]" />
                    <span>{isKhmer ? 'លេខ PIN សម្ងាត់ (៤ ខ្ទង់)' : 'Simple 4-digit PIN (Optional)'}</span>
                  </label>
                  <input
                    type="password"
                    maxLength={4}
                    value={pin}
                    onChange={(e) => setPin(e.target.value)}
                    placeholder="1 2 3 4"
                    className="w-full px-4 py-3 bg-[#F8FAFC] rounded-2xl border-3 border-[#2A1E4D] text-base font-bold text-[#2A1E4D] tracking-widest focus:bg-white focus:outline-none"
                  />
                </div>

                <div className="flex gap-2 pt-1">
                  <button
                    type="button"
                    onClick={() => setPublicSignupStep(2)}
                    className="w-1/3 py-3.5 bg-white hover:bg-[#F8FAFC] text-[#2A1E4D] font-black text-xs rounded-2xl border-2.5 border-[#2A1E4D] cursor-pointer"
                  >
                    {isKhmer ? 'ត្រឡប់' : 'Back'}
                  </button>
                  <button
                    type="submit"
                    className="w-2/3 py-3.5 bg-[#6FCF6F] hover:bg-[#5EBF5E] text-[#2A1E4D] font-black text-sm rounded-2xl border-3 border-[#2A1E4D] shadow-[4px_4px_0px_#2A1E4D] hover:-translate-y-0.5 active:translate-y-0.5 transition-all cursor-pointer flex items-center justify-center gap-2"
                  >
                    <Check className="w-5 h-5 stroke-[3]" />
                    <span>{isKhmer ? 'បង្កើតគណនី និងរៀន' : 'Create Account & Start'}</span>
                  </button>
                </div>
              </div>
            )}
          </form>
        )}

        {/* FLOW 4: RETURNING USER LOGIN PATH */}
        {flowMode === 'returning-login' && (
          <form onSubmit={handleFinishReturningLogin} className="space-y-4 pt-1">
            <div className="space-y-1.5">
              <label className="text-xs font-black text-[#2A1E4D] uppercase tracking-wider">
                {isKhmer ? 'ឈ្មោះសិស្ស ឬលេខកូដ' : 'Student Name or School Code'}
              </label>
              <input
                type="text"
                value={studentName}
                onChange={(e) => setStudentName(e.target.value)}
                placeholder={isKhmer ? 'បញ្ចូលឈ្មោះ ឬលេខកូដ' : 'Enter name or code'}
                className="w-full px-4 py-3.5 bg-[#F8FAFC] rounded-2xl border-3 border-[#2A1E4D] text-base font-bold text-[#2A1E4D] focus:bg-white focus:outline-none"
                required
              />
            </div>

            <div className="space-y-1.5">
              <label className="text-xs font-black text-[#2A1E4D] uppercase tracking-wider">
                {isKhmer ? 'លេខ PIN សម្ងាត់ (៤ ខ្ទង់)' : '4-Digit PIN'}
              </label>
              <input
                type="password"
                maxLength={4}
                value={pin}
                onChange={(e) => setPin(e.target.value)}
                placeholder="1 2 3 4"
                className="w-full px-4 py-3 bg-[#F8FAFC] rounded-2xl border-3 border-[#2A1E4D] text-base font-bold text-[#2A1E4D] tracking-widest focus:bg-white focus:outline-none"
                required
              />
            </div>

            <button
              type="submit"
              className="w-full py-4 bg-[#FFCB3D] hover:bg-[#FFD768] text-[#2A1E4D] font-black text-base rounded-2xl border-3 border-[#2A1E4D] shadow-[4px_4px_0px_#2A1E4D] hover:-translate-y-0.5 active:translate-y-0.5 transition-all cursor-pointer flex items-center justify-center gap-2 mt-2"
            >
              <span>{isKhmer ? 'ចូលប្រើប្រាស់' : 'Log In'}</span>
              <ArrowRight className="w-5 h-5 stroke-[3]" />
            </button>
          </form>
        )}

        {/* DEV AUTO-FILL TESTING TOOL BUTTON */}
        <div className="pt-4 border-t-2 border-dashed border-[#2A1E4D]/20 text-center">
          {/* Note: This is a testing helper tool for developers/testing */}
          <button
            type="button"
            onClick={handleFillDemoData}
            className="w-full py-2 px-3 bg-[#F1F5F9] hover:bg-[#FFCB3D]/30 text-[#2A1E4D] text-xs font-extrabold rounded-xl border-2 border-dashed border-[#2A1E4D]/40 transition-all cursor-pointer flex items-center justify-center gap-1.5"
          >
            <Zap className="w-3.5 h-3.5 text-[#6C4FF6]" />
            <span>Fill Demo Data</span>
            <span className="px-1.5 py-0.2 bg-[#6C4FF6] text-white text-[9px] font-black rounded uppercase">
              DEV
            </span>
          </button>
        </div>
      </div>

      {/* Footer Disclaimer */}
      <div className="max-w-md mx-auto w-full text-center text-xs text-[#2A1E4D]/60 font-medium py-2">
        Tunsay Homework Tutor • Personal AI Companion
      </div>

      {/* Code Help Modal */}
      {showCodeHelpModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-[#2A1E4D]/60 backdrop-blur-sm p-4 animate-fadeIn">
          <div className="bg-white rounded-3xl border-3 border-[#2A1E4D] shadow-[6px_6px_0px_#2A1E4D] max-w-sm w-full p-6 space-y-4 text-center">
            <div className="w-12 h-12 bg-[#FFCB3D] rounded-2xl border-2 border-[#2A1E4D] flex items-center justify-center mx-auto text-2xl font-black">
              <School className="w-6 h-6 text-[#2A1E4D]" />
            </div>
            <h3 className="text-lg font-black font-heading text-[#2A1E4D]">
              {isKhmer ? 'តើស្វែងរកលេខកូដនៅឯណា?' : 'Where to find your School Code?'}
            </h3>
            <p className="text-xs sm:text-sm font-medium text-[#2A1E4D]/80 leading-relaxed text-left">
              {isKhmer 
                ? 'លេខកូដសាលារៀន (ដូចជា TUNSAY-G4-DEMO) ត្រូវបានផ្តល់ជូនដោយលោកគ្រូ ឬអ្នកគ្រូណែនាំថ្នាក់។ ប្រសិនបើមិនទាន់មានទេ អ្នកអាចចុះឈ្មោះដោយខ្លួនឯងបាន!' 
                : 'School codes (like TUNSAY-G4-DEMO) are provided by your teacher or school administrator. If you do not have one yet, you can sign up on your own or try our demo button!'}
            </p>
            <button
              type="button"
              onClick={() => setShowCodeHelpModal(false)}
              className="w-full py-3 bg-[#6C4FF6] text-white font-black text-sm rounded-2xl border-2 border-[#2A1E4D] cursor-pointer"
            >
              {isKhmer ? 'យល់ព្រម' : 'Got it!'}
            </button>
          </div>
        </div>
      )}
    </div>
  );
};
