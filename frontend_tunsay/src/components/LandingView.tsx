import React, { useState } from 'react';
import { Language } from '../types';
import { TunsayAvatar } from './TunsayAvatar';
import { 
  Sparkles, 
  BookOpen, 
  Calculator, 
  Atom, 
  Languages, 
  CheckCircle2, 
  XCircle, 
  ShieldCheck, 
  GraduationCap, 
  HeartHandshake, 
  ArrowRight, 
  Check, 
  Award, 
  School,
  Smile,
  Footprints,
  Globe,
  X,
  Mail,
  Shield,
  Send
} from 'lucide-react';

interface LandingViewProps {
  language: Language;
  onSelectLanguage: (lang: Language) => void;
  onNavigateToLogin: () => void;
}

export const LandingView: React.FC<LandingViewProps> = ({
  language,
  onSelectLanguage,
  onNavigateToLogin,
}) => {
  const isKhmer = language === 'km';
  const [activeModal, setActiveModal] = useState<'privacy' | 'contact' | null>(null);
  const [contactForm, setContactForm] = useState({ name: '', email: '', message: '' });
  const [contactSent, setContactSent] = useState(false);

  const scrollToHowItWorks = () => {
    const el = document.getElementById('how-it-works');
    if (el) {
      el.scrollIntoView({ behavior: 'smooth' });
    }
  };

  const scrollToAboutTunsay = () => {
    const el = document.getElementById('about-tunsay');
    if (el) {
      el.scrollIntoView({ behavior: 'smooth' });
    }
  };

  return (
    <div className="min-h-screen w-full max-w-full overflow-x-hidden bg-[#F8FAFC] text-[#2A1E4D] font-sans selection:bg-[#FFCB3D] selection:text-[#2A1E4D]">
      {/* Public Top Navbar */}
      <nav className="sticky top-0 z-50 bg-white/90 backdrop-blur-md border-b-2 border-[#2A1E4D]/10">
        <div className="max-w-6xl mx-auto px-2.5 sm:px-6 lg:px-8 h-16 sm:h-20 flex items-center justify-between gap-1.5 sm:gap-4">
          {/* Brand Logo */}
          <div className="flex items-center gap-2 sm:gap-3 shrink-0">
            <div className="w-9 h-9 sm:w-11 sm:h-11 bg-[#FFCB3D] rounded-xl sm:rounded-2xl flex items-center justify-center border-2 sm:border-2.5 border-[#2A1E4D] shadow-[2px_2px_0px_#2A1E4D] sm:shadow-[2.5px_2.5px_0px_#2A1E4D] shrink-0">
              <TunsayAvatar size="sm" state="idle" showBadge={false} />
            </div>
            <div>
              <div className="flex items-center gap-1.5">
                <span className="text-lg sm:text-2xl font-black font-heading text-[#2A1E4D] tracking-tight">
                  Tunsay
                </span>
              </div>
              <p className="text-[10px] sm:text-xs font-bold text-[#6C4FF6] hidden min-[400px]:block">
                {isKhmer ? 'គ្រូបង្រៀន AI កិច្ចការផ្ទះ' : 'AI Homework Tutor'}
              </p>
            </div>
          </div>

          {/* Nav Controls */}
          <div className="flex items-center gap-1.5 sm:gap-3 shrink-0">
            {/* Language Switcher */}
            <div className="flex items-center p-0.5 sm:p-1 bg-[#EAF2FF] rounded-lg sm:rounded-xl border border-[#2A1E4D]/20">
              <button
                type="button"
                onClick={() => onSelectLanguage('km')}
                className={`px-1.5 sm:px-2.5 py-0.5 sm:py-1 text-[11px] sm:text-xs font-black rounded sm:rounded-lg transition-all cursor-pointer ${
                  isKhmer
                    ? 'bg-[#6C4FF6] text-white shadow-[1px_1px_0px_#2A1E4D]'
                    : 'text-[#2A1E4D] hover:bg-white/60'
                }`}
              >
                ខ្មែរ
              </button>
              <button
                type="button"
                onClick={() => onSelectLanguage('en')}
                className={`px-1.5 sm:px-2.5 py-0.5 sm:py-1 text-[11px] sm:text-xs font-black rounded sm:rounded-lg transition-all cursor-pointer ${
                  !isKhmer
                    ? 'bg-[#6C4FF6] text-white shadow-[1px_1px_0px_#2A1E4D]'
                    : 'text-[#2A1E4D] hover:bg-white/60'
                }`}
              >
                EN
              </button>
            </div>

            {/* Login / Entry Button */}
            <button
              type="button"
              onClick={onNavigateToLogin}
              className="hidden sm:inline-flex px-3 sm:px-4 py-1.5 sm:py-2 bg-white hover:bg-[#EAF2FF] text-[#2A1E4D] text-xs sm:text-sm font-black rounded-lg sm:rounded-xl border sm:border-2 border-[#2A1E4D] shadow-[1.5px_1.5px_0px_#2A1E4D] transition-all cursor-pointer whitespace-nowrap"
            >
              {isKhmer ? 'ចូលប្រើប្រាស់' : 'Sign In'}
            </button>

            {/* Main Primary CTA */}
            <button
              type="button"
              onClick={onNavigateToLogin}
              className="px-2.5 sm:px-5 py-1.5 sm:py-2.5 bg-[#FFCB3D] hover:bg-[#FFD768] text-[#2A1E4D] text-xs sm:text-sm font-black rounded-lg sm:rounded-xl border sm:border-2 border-[#2A1E4D] shadow-[2px_2px_0px_#2A1E4D] hover:-translate-y-0.5 active:translate-y-0.5 transition-all cursor-pointer flex items-center gap-1 sm:gap-1.5 whitespace-nowrap"
            >
              <span className="hidden min-[360px]:inline">{isKhmer ? 'សាកល្បងទន្សាយ' : 'Get Started'}</span>
              <span className="inline min-[360px]:hidden">{isKhmer ? 'សាកល្បង' : 'Start'}</span>
              <ArrowRight className="w-3.5 h-3.5 sm:w-4 sm:h-4 stroke-[2.5]" />
            </button>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="relative overflow-hidden pt-8 pb-16 sm:pt-14 sm:pb-24 bg-gradient-to-b from-white via-[#EAF2FF]/40 to-[#F8FAFC]">
        {/* Subtle Meadow / Leaf Motifs in background */}
        <div className="absolute top-10 left-5 w-24 h-24 bg-[#6FCF6F]/10 rounded-full blur-2xl pointer-events-none" />
        <div className="absolute bottom-10 right-10 w-32 h-32 bg-[#FFCB3D]/15 rounded-full blur-2xl pointer-events-none" />

        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-10 items-center">
            {/* Left Column: Headlines & CTAs */}
            <div className="lg:col-span-7 space-y-6 text-center lg:text-left">
              {/* Trust Badge Header */}
              <div className="inline-flex items-center gap-2 px-3.5 py-1.5 bg-[#EAF2FF] border-2 border-[#6C4FF6]/30 rounded-full text-xs font-black text-[#6C4FF6]">
                <Sparkles className="w-4 h-4 text-[#6C4FF6]" />
                <span>
                  {isKhmer 
                    ? 'ជំនួយការ AI ធ្វើកិច្ចការផ្ទះផ្ទាល់ខ្លួន' 
                    : 'Personal AI Homework Companion'}
                </span>
              </div>

              {/* Main Headline (Baloo 2 / Siemreap styling) */}
              <h1 className="text-3xl sm:text-4xl lg:text-5xl font-black font-heading text-[#2A1E4D] leading-[1.2] tracking-tight">
                {isKhmer ? (
                  <>
                    ទន្សាយជួយកូនរបស់អ្នក <span className="text-[#6C4FF6]">ឱ្យយល់អំពីកិច្ចការផ្ទះ</span> មិនមែនគ្រាន់តែផ្តល់ចម្លើយ
                  </>
                ) : (
                  <>
                    Tunsay helps your child <span className="text-[#6C4FF6]">understand homework</span>, not just get the answer
                  </>
                )}
              </h1>

              {/* Subheadline */}
              <p className="text-base sm:text-lg text-[#2A1E4D]/80 font-medium max-w-2xl mx-auto lg:mx-0 leading-relaxed">
                {isKhmer 
                  ? 'គ្រូបង្រៀន AI ផ្ទាល់ខ្លួន សម្រាប់សិស្សបឋមសិក្សា (ថ្នាក់ទី ១–៦)។ ទន្សាយជួយណែនាំកុមារជាជំហានៗ ជាភាសាខ្មែរ និងអង់គ្លេស ដើម្បីបង្កើតទំនុកចិត្ត និងសមត្ថភាពគិតដោយខ្លួនឯង។' 
                  : 'The AI homework companion designed for primary students (Grades 1–6). Tunsay guides children step-by-step in Khmer and English, building real confidence and independent thinking.'}
              </p>

              {/* CTA Buttons */}
              <div className="pt-2 flex flex-col sm:flex-row items-center justify-center lg:justify-start gap-3.5">
                <button
                  type="button"
                  onClick={onNavigateToLogin}
                  className="w-full sm:w-auto px-7 py-3.5 bg-[#FFCB3D] hover:bg-[#FFD768] text-[#2A1E4D] font-black text-base rounded-2xl border-3 border-[#2A1E4D] shadow-[4px_4px_0px_#2A1E4D] hover:-translate-y-0.5 active:translate-y-0.5 transition-all cursor-pointer flex items-center justify-center gap-2"
                >
                  <Sparkles className="w-5 h-5 text-[#2A1E4D]" />
                  <span>{isKhmer ? 'សាកល្បងប្រើប្រាស់ដោយឥតគិតថ្លៃ' : 'Try Tunsay Free'}</span>
                </button>

                <button
                  type="button"
                  onClick={scrollToHowItWorks}
                  className="w-full sm:w-auto px-6 py-3.5 bg-white hover:bg-[#EAF2FF] text-[#2A1E4D] font-black text-base rounded-2xl border-3 border-[#2A1E4D]/20 hover:border-[#2A1E4D] transition-all cursor-pointer flex items-center justify-center gap-2"
                >
                  <span>{isKhmer ? 'មើលពីរបៀបដំណើរការ' : 'See how it works'}</span>
                  <ArrowRight className="w-4 h-4 stroke-[2.5]" />
                </button>
              </div>

              {/* Quick Trust Highlights */}
              <div className="pt-4 flex flex-wrap items-center justify-center lg:justify-start gap-y-2 gap-x-5 text-xs font-black text-[#2A1E4D]/75">
                <div className="flex items-center gap-1.5">
                  <Check className="w-4 h-4 text-[#6FCF6F] stroke-[3]" />
                  <span>{isKhmer ? 'គាំទ្រភាសាខ្មែរ & អង់គ្លេស' : 'Bilingual Khmer & English'}</span>
                </div>
                <div className="flex items-center gap-1.5">
                  <Check className="w-4 h-4 text-[#6FCF6F] stroke-[3]" />
                  <span>{isKhmer ? 'សម្រាប់ថ្នាក់ទី ១ ដល់ ថ្នាក់ទី ៦' : 'Designed for Grades 1–6'}</span>
                </div>
                <div className="flex items-center gap-1.5">
                  <Check className="w-4 h-4 text-[#6FCF6F] stroke-[3]" />
                  <span>{isKhmer ? 'សុវត្ថិភាពកុមារ ១០០%' : '100% Child-Safe Environment'}</span>
                </div>
              </div>
            </div>

            {/* Right Column: Hero Mascot Card Illustration */}
            <div className="lg:col-span-5 flex justify-center">
              <div className="relative w-full max-w-sm sm:max-w-md">
                {/* Background decorative card */}
                <div className="absolute -inset-2 bg-gradient-to-tr from-[#6C4FF6] to-[#3EC6E0] rounded-3xl border-3 border-[#2A1E4D] shadow-[6px_6px_0px_#2A1E4D] transform rotate-1" />
                
                {/* Foreground Card */}
                <div className="relative bg-white p-6 sm:p-8 rounded-3xl border-3 border-[#2A1E4D] shadow-[4px_4px_0px_#2A1E4D] space-y-6 text-center">
                  {/* Floating Paw Badge */}
                  <div className="absolute -top-4 -right-2 px-3 py-1 bg-[#FFCB3D] text-[#2A1E4D] text-xs font-black rounded-full border-2 border-[#2A1E4D] shadow-[2px_2px_0px_#2A1E4D] flex items-center gap-1.5">
                    <Footprints className="w-4 h-4 text-[#2A1E4D]" />
                    <span>{isKhmer ? 'វិធីសាស្ត្រណែនាំជាជំហាន' : '4-Step Guidance'}</span>
                  </div>

                  {/* Tunsay Mascot Visual Container */}
                  <div className="w-32 h-32 sm:w-36 sm:h-36 mx-auto bg-[#EAF2FF] rounded-full border-3 border-[#2A1E4D] shadow-[3px_3px_0px_#2A1E4D] flex items-center justify-center p-2 relative group">
                    <TunsayAvatar size="lg" state="encouraging" showBadge={false} />
                    <div className="absolute -bottom-1 -right-1 bg-[#6FCF6F] p-2 rounded-full border-2 border-[#2A1E4D]">
                      <Smile className="w-5 h-5 text-[#2A1E4D]" />
                    </div>
                  </div>

                  {/* Sample Dialogue Bubble */}
                  <div className="p-4 bg-[#EAF2FF] rounded-2xl border-2.5 border-[#2A1E4D] text-left text-xs sm:text-sm font-bold text-[#2A1E4D] relative">
                    <div className="flex items-center gap-2 text-[#6C4FF6] font-black text-xs mb-1">
                      <Sparkles className="w-3.5 h-3.5" />
                      <span>{isKhmer ? 'ទន្សាយ និយាយថា៖' : 'Tunsay says:'}</span>
                    </div>
                    <p className="leading-snug">
                      {isKhmer 
                        ? '« កុំបារម្ភអី! តោះយើងពិនិត្យមើលរូបមន្តប្រមាណវិធីនេះទាំងអស់គ្នាជាមុនសិនណា! »' 
                        : '"Don\'t worry! Let\'s break this problem down together step-by-step. What do we know first?"'}
                    </p>
                  </div>

                  {/* Quick Card Features */}
                  <div className="grid grid-cols-3 gap-2 text-center pt-1">
                    <div className="p-2 bg-[#F8FAFC] rounded-xl border-1.5 border-[#2A1E4D]/20">
                      <div className="text-lg font-black text-[#6C4FF6]">1–6</div>
                      <div className="text-[10px] font-bold text-[#2A1E4D]/70">{isKhmer ? 'ថ្នាក់រៀន' : 'Grades'}</div>
                    </div>
                    <div className="p-2 bg-[#F8FAFC] rounded-xl border-1.5 border-[#2A1E4D]/20">
                      <div className="text-lg font-black text-[#3EC6E0]">KM/EN</div>
                      <div className="text-[10px] font-bold text-[#2A1E4D]/70">{isKhmer ? 'ពីរភាសា' : 'Bilingual'}</div>
                    </div>
                    <div className="p-2 bg-[#F8FAFC] rounded-xl border-1.5 border-[#2A1E4D]/20">
                      <div className="text-lg font-black text-[#6FCF6F]">WEG</div>
                      <div className="text-[10px] font-bold text-[#2A1E4D]/70">{isKhmer ? 'កម្មវិធីសិក្សា' : 'Aligned'}</div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* How It Works Section (Step-Trail Metaphor) */}
      <section id="how-it-works" className="py-16 sm:py-24 bg-white border-y-2 border-[#2A1E4D]/10">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 space-y-12">
          {/* Section Header */}
          <div className="text-center max-w-2xl mx-auto space-y-3">
            <div className="inline-flex items-center gap-1.5 px-3 py-1 bg-[#FFCB3D] text-[#2A1E4D] text-xs font-black rounded-full border-2 border-[#2A1E4D] shadow-[2px_2px_0px_#2A1E4D]">
              <Footprints className="w-4 h-4 text-[#2A1E4D]" />
              <span>{isKhmer ? 'វិធីសាស្ត្រនៃការរៀន' : 'The Learning Journey'}</span>
            </div>
            <h2 className="text-2xl sm:text-3xl lg:text-4xl font-black font-heading text-[#2A1E4D]">
              {isKhmer ? 'របៀបដែលទន្សាយជួយណែនាំកូនរបស់អ្នក' : 'How Tunsay Guides Your Child'}
            </h2>
            <p className="text-sm sm:text-base font-medium text-[#2A1E4D]/75">
              {isKhmer 
                ? 'ជំនួសឱ្យការផ្តល់ចម្លើយភ្លាមៗ ទន្សាយប្រើប្រាស់ « ផ្លូវស្នាមជើង » ដើម្បីប្រែក្លាយកិច្ចការផ្ទះទៅជាការសន្ទនារៀនសូត្រប្រកបដោយការលើកទឹកចិត្ត។' 
                : 'Rather than dumping instant answers, Tunsay uses the Step-Trail method to transform homework into an encouraging, guided dialogue.'}
            </p>
          </div>

          {/* 4 Step Cards Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 relative">
            {/* Step 1 */}
            <div className="bg-[#F8FAFC] p-6 rounded-3xl border-3 border-[#2A1E4D] shadow-[4px_4px_0px_#2A1E4D] space-y-4 relative flex flex-col justify-between hover:-translate-y-1 transition-transform">
              <div className="space-y-3">
                <div className="w-12 h-12 bg-[#FFCB3D] rounded-2xl border-2 border-[#2A1E4D] shadow-[2px_2px_0px_#2A1E4D] flex items-center justify-center text-xl font-black font-heading text-[#2A1E4D]">
                  1
                </div>
                <h3 className="text-lg font-black font-heading text-[#2A1E4D]">
                  {isKhmer ? 'ថតរូប ឬសួរសំណួរ' : '1. Ask or Scan'}
                </h3>
                <p className="text-xs sm:text-sm font-medium text-[#2A1E4D]/80 leading-relaxed">
                  {isKhmer 
                    ? 'ថតរូបលំហាត់គណិតវិទ្យា វិទ្យាសាស្ត្រ ឬភាសាអង់គ្លេស ឬវាយបញ្ចូលសំណួរដោយផ្ទាល់។' 
                    : 'Snap a photo of any Math, Science, or English homework problem, or ask Tunsay with voice or text.'}
                </p>
              </div>
              <div className="pt-3 border-t-2 border-[#2A1E4D]/10 flex items-center gap-1.5 text-xs font-black text-[#6C4FF6]">
                <Footprints className="w-3.5 h-3.5" />
                <span>{isKhmer ? 'ចាប់ផ្តើមស្កែន' : 'Simple photo scan'}</span>
              </div>
            </div>

            {/* Step 2 */}
            <div className="bg-[#F8FAFC] p-6 rounded-3xl border-3 border-[#2A1E4D] shadow-[4px_4px_0px_#2A1E4D] space-y-4 relative flex flex-col justify-between hover:-translate-y-1 transition-transform">
              <div className="space-y-3">
                <div className="w-12 h-12 bg-[#3EC6E0] text-white rounded-2xl border-2 border-[#2A1E4D] shadow-[2px_2px_0px_#2A1E4D] flex items-center justify-center text-xl font-black font-heading">
                  2
                </div>
                <h3 className="text-lg font-black font-heading text-[#2A1E4D]">
                  {isKhmer ? 'ទន្សាយផ្តល់ការណែនាំ' : '2. Tunsay Guides'}
                </h3>
                <p className="text-xs sm:text-sm font-medium text-[#2A1E4D]/80 leading-relaxed">
                  {isKhmer 
                    ? 'ទន្សាយពន្លាតសំណួរស្មុគស្មាញជាជំហានតូចៗ ងាយយល់ និងផ្តល់តម្រុយ ៣ កម្រិត។' 
                    : 'Tunsay breaks complex questions into small bite-sized sub-steps with 3 progressive tiers of hints.'}
                </p>
              </div>
              <div className="pt-3 border-t-2 border-[#2A1E4D]/10 flex items-center gap-1.5 text-xs font-black text-[#3EC6E0]">
                <Footprints className="w-3.5 h-3.5" />
                <span>{isKhmer ? 'តម្រុយ និងឧទាហរណ៍' : 'Hints & analogies'}</span>
              </div>
            </div>

            {/* Step 3 */}
            <div className="bg-[#F8FAFC] p-6 rounded-3xl border-3 border-[#2A1E4D] shadow-[4px_4px_0px_#2A1E4D] space-y-4 relative flex flex-col justify-between hover:-translate-y-1 transition-transform">
              <div className="space-y-3">
                <div className="w-12 h-12 bg-[#FF6FA3] text-white rounded-2xl border-2 border-[#2A1E4D] shadow-[2px_2px_0px_#2A1E4D] flex items-center justify-center text-xl font-black font-heading">
                  3
                </div>
                <h3 className="text-lg font-black font-heading text-[#2A1E4D]">
                  {isKhmer ? 'សិស្សគិត និងឆ្លើយ' : '3. Student Thinks'}
                </h3>
                <p className="text-xs sm:text-sm font-medium text-[#2A1E4D]/80 leading-relaxed">
                  {isKhmer 
                    ? 'កុមារសាកល្បងឆ្លើយសំណួរជំហាននីមួយៗ ដោយប្រើឧទាហរណ៍រូបភាព (ដូចជាផ្លែប៉ោម ឬនំភីហ្សា)។' 
                    : 'The child answers guided sub-questions using visual models, reinforcing understanding.'}
                </p>
              </div>
              <div className="pt-3 border-t-2 border-[#2A1E4D]/10 flex items-center gap-1.5 text-xs font-black text-[#FF6FA3]">
                <Footprints className="w-3.5 h-3.5" />
                <span>{isKhmer ? 'អភិវឌ្ឍការគិត' : 'Active thinking'}</span>
              </div>
            </div>

            {/* Step 4 */}
            <div className="bg-[#F8FAFC] p-6 rounded-3xl border-3 border-[#2A1E4D] shadow-[4px_4px_0px_#2A1E4D] space-y-4 relative flex flex-col justify-between hover:-translate-y-1 transition-transform">
              <div className="space-y-3">
                <div className="w-12 h-12 bg-[#6FCF6F] text-[#2A1E4D] rounded-2xl border-2 border-[#2A1E4D] shadow-[2px_2px_0px_#2A1E4D] flex items-center justify-center text-xl font-black font-heading">
                  4
                </div>
                <h3 className="text-lg font-black font-heading text-[#2A1E4D]">
                  {isKhmer ? 'ដោះស្រាយបានដោយជោគជ័យ' : '4. Solved & Mastered'}
                </h3>
                <p className="text-xs sm:text-sm font-medium text-[#2A1E4D]/80 leading-relaxed">
                  {isKhmer 
                    ? 'សិស្សយល់ច្បាស់ពីមេរៀន ទទួលបានផ្កាយរង្វាន់ និងកសាងទំនុកចិត្តសម្រាប់ការប្រឡង។' 
                    : 'The student masters the concept, earns stars, and builds lasting academic confidence.'}
                </p>
              </div>
              <div className="pt-3 border-t-2 border-[#2A1E4D]/10 flex items-center gap-1.5 text-xs font-black text-[#6FCF6F]">
                <Footprints className="w-3.5 h-3.5" />
                <span>{isKhmer ? 'អបអរសាទរជោគជ័យ' : 'Celebration & Stars'}</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Why Tunsay is Different (Comparison Framing) */}
      <section id="about-tunsay" className="py-16 sm:py-24 bg-[#EAF2FF]/50 scroll-mt-20">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 space-y-12">
          {/* Section Heading */}
          <div className="text-center max-w-2xl mx-auto space-y-3">
            <h2 className="text-2xl sm:text-3xl lg:text-4xl font-black font-heading text-[#2A1E4D]">
              {isKhmer ? 'មិនមែនជាម៉ាស៊ីនផ្តល់ចម្លើយ — តែជាមិត្តរៀនសូត្រពិតប្រាកដ' : 'Not an Answer Machine — A True Learning Companion'}
            </h2>
            <p className="text-sm sm:text-base font-medium text-[#2A1E4D]/75">
              {isKhmer 
                ? 'ទន្សាយត្រូវបានបង្កើតឡើងដោយឈរលើគោលការណ៍អប់រំត្រឹមត្រូវ ដើម្បីធានាថាកុមាររៀនចេះពិតប្រាកដ។' 
                : 'Tunsay is engineered with strict educational guardrails to ensure your child truly learns.'}
            </p>
          </div>

          {/* Side-by-side comparison box */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 max-w-4xl mx-auto">
            {/* Generic Answer Bots (Red/Gray Cross) */}
            <div className="p-6 sm:p-8 bg-white rounded-3xl border-3 border-[#2A1E4D]/20 space-y-4">
              <div className="flex items-center gap-2 text-[#EF4444] font-black text-base font-heading">
                <XCircle className="w-6 h-6 stroke-[2.5]" />
                <span>{isKhmer ? 'ប្រព័ន្ធ AI ផ្តល់ចម្លើយទូទៅ' : 'Standard AI Answer Bots'}</span>
              </div>
              <ul className="space-y-3 text-xs sm:text-sm font-medium text-[#2A1E4D]/80">
                <li className="flex items-start gap-2">
                  <XCircle className="w-4 h-4 text-[#EF4444] shrink-0 mt-0.5" />
                  <span>{isKhmer ? 'ផ្តល់ចម្លើយចុងក្រោយភ្លាមៗ ដោយមិនបានពន្យល់' : 'Dumps instant final answers without explaining'}</span>
                </li>
                <li className="flex items-start gap-2">
                  <XCircle className="w-4 h-4 text-[#EF4444] shrink-0 mt-0.5" />
                  <span>{isKhmer ? 'ធ្វើឱ្យកុមារទម្លាប់ចម្លង មិនបណ្តុះការគិត' : 'Encourages copy-pasting, causing dependency'}</span>
                </li>
                <li className="flex items-start gap-2">
                  <XCircle className="w-4 h-4 text-[#EF4444] shrink-0 mt-0.5" />
                  <span>{isKhmer ? 'ខ្វះការយល់ដឹងពីកម្មវិធីសិក្សាបឋម' : 'Lacks understanding of primary school curriculum'}</span>
                </li>
              </ul>
            </div>

            {/* Tunsay AI Tutor (Green/Purple Check) */}
            <div className="p-6 sm:p-8 bg-white rounded-3xl border-3 border-[#2A1E4D] shadow-[5px_5px_0px_#2A1E4D] space-y-4 relative overflow-hidden">
              <div className="absolute top-0 right-0 bg-[#FFCB3D] text-[#2A1E4D] text-[10px] font-black px-3 py-1 border-b-2 border-l-2 border-[#2A1E4D] rounded-bl-xl uppercase">
                {isKhmer ? 'វិធីសាស្ត្រទន្សាយ' : 'The Tunsay Way'}
              </div>
              <div className="flex items-center gap-2 text-[#6C4FF6] font-black text-base font-heading">
                <CheckCircle2 className="w-6 h-6 stroke-[2.5]" />
                <span>{isKhmer ? 'គ្រូបង្រៀន AI ទន្សាយ (Tunsay)' : 'Tunsay AI Learning Companion'}</span>
              </div>
              <ul className="space-y-3 text-xs sm:text-sm font-bold text-[#2A1E4D]">
                <li className="flex items-start gap-2">
                  <Check className="w-4 h-4 text-[#6FCF6F] stroke-[3] shrink-0 mt-0.5" />
                  <span>{isKhmer ? 'ណែនាំជាជំហានៗ និងចោទសួរដើម្បីឱ្យកុមារគិត' : 'Asks guiding sub-questions so the student discovers solutions'}</span>
                </li>
                <li className="flex items-start gap-2">
                  <Check className="w-4 h-4 text-[#6FCF6F] stroke-[3] shrink-0 mt-0.5" />
                  <span>{isKhmer ? 'ផ្តល់តម្រុយ ៣ កម្រិត និងឧទាហរណ៍រូបភាពងាយយល់' : 'Provides 3 hint tiers and visual analogies (pizza, apples)'}</span>
                </li>
                <li className="flex items-start gap-2">
                  <Check className="w-4 h-4 text-[#6FCF6F] stroke-[3] shrink-0 mt-0.5" />
                  <span>{isKhmer ? 'ស្របតាមកម្មវិធីសិក្សាបឋមសិក្សា (ថ្នាក់ទី ១–៦)' : 'Strictly aligned with primary grade standards'}</span>
                </li>
              </ul>
            </div>
          </div>

          {/* 3 Core Value Cards */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 pt-4">
            <div className="p-6 bg-white rounded-3xl border-2.5 border-[#2A1E4D] shadow-[3px_3px_0px_#2A1E4D] space-y-2">
              <div className="w-10 h-10 bg-[#FFCB3D] rounded-xl border-2 border-[#2A1E4D] flex items-center justify-center font-black">
                <Footprints className="w-5 h-5 text-[#2A1E4D]" />
              </div>
              <h3 className="text-base font-black font-heading text-[#2A1E4D]">
                {isKhmer ? 'ណែនាំជាជំហានៗ' : 'Step-by-Step Guidance'}
              </h3>
              <p className="text-xs text-[#2A1E4D]/80 font-medium leading-relaxed">
                {isKhmer 
                  ? 'មិនផ្តល់ចម្លើយផ្ទាល់ភ្លាមៗទេ ប៉ុន្តែជួយណែនាំកុមារឱ្យរកឃើញចម្លើយដោយខ្លួនឯង។' 
                  : 'Tunsay never dumps final answers; it guides students through manageable sub-steps.'}
              </p>
            </div>

            <div className="p-6 bg-white rounded-3xl border-2.5 border-[#2A1E4D] shadow-[3px_3px_0px_#2A1E4D] space-y-2">
              <div className="w-10 h-10 bg-[#3EC6E0] rounded-xl border-2 border-[#2A1E4D] flex items-center justify-center font-black text-white">
                <Globe className="w-5 h-5 text-white" />
              </div>
              <h3 className="text-base font-black font-heading text-[#2A1E4D]">
                {isKhmer ? 'ពីរភាសា ខ្មែរ + អង់គ្លេស' : 'Bilingual Khmer & English'}
              </h3>
              <p className="text-xs text-[#2A1E4D]/80 font-medium leading-relaxed">
                {isKhmer 
                  ? 'ផ្លាស់ប្តូរភាសាយ៉ាងរហ័ស សម្រួលដល់ការរៀនសូត្រនៅផ្ទះ និងសាលារៀន។' 
                  : 'Fluent in Khmer and English, creating a seamless bridge between school and home.'}
              </p>
            </div>

            <div className="p-6 bg-white rounded-3xl border-2.5 border-[#2A1E4D] shadow-[3px_3px_0px_#2A1E4D] space-y-2">
              <div className="w-10 h-10 bg-[#6FCF6F] rounded-xl border-2 border-[#2A1E4D] flex items-center justify-center font-black">
                <GraduationCap className="w-5 h-5 text-[#2A1E4D]" />
              </div>
              <h3 className="text-base font-black font-heading text-[#2A1E4D]">
                {isKhmer ? 'សម្រាប់ថ្នាក់ទី ១ ដល់ ៦' : 'Built for Grades 1–6'}
              </h3>
              <p className="text-xs text-[#2A1E4D]/80 font-medium leading-relaxed">
                {isKhmer 
                  ? 'ការរចនាងាយស្រួលសម្រាប់កុមារ ប៊ូតុងធំៗ និងភាសាសាមញ្ញសមស្របតាមវ័យ។' 
                  : 'Kid-safe interface with large tap targets, simple words, and encouraging feedback.'}
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Trust & Credibility Section */}
      <section className="py-16 sm:py-20 bg-white border-b-2 border-[#2A1E4D]/10">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 space-y-10">
          {/* Smart Companion Header */}
          <div className="p-6 sm:p-8 bg-[#6C4FF6] text-white rounded-3xl border-3 border-[#2A1E4D] shadow-[6px_6px_0px_#2A1E4D] flex flex-col sm:flex-row items-center justify-between gap-6">
            <div className="space-y-2 text-center sm:text-left">
              <span className="px-3 py-1 bg-[#FFCB3D] text-[#2A1E4D] text-xs font-black rounded-full border-1.5 border-[#2A1E4D] uppercase">
                Tunsay AI Tutor
              </span>
              <h3 className="text-xl sm:text-2xl font-black font-heading">
                {isKhmer ? 'ជំនួយការអប់រំឌីជីថលឆ្លាតវៃសម្រាប់កូនរបស់អ្នក' : 'Your Child\'s Personal Digital AI Tutor'}
              </h3>
              <p className="text-xs sm:text-sm text-white/90 font-medium max-w-xl">
                {isKhmer 
                  ? 'ទន្សាយត្រូវបានបង្កើតឡើងដើម្បីគាំទ្រដល់ការរៀនសូត្ររបស់កុមារនៅផ្ទះ ដោយសហការយ៉ាងជិតស្និទ្ធជាមួយវិធីសាស្ត្រអប់រំបឋមសិក្សា។' 
                  : 'Tunsay is integrated with school curriculum standards to ensure seamless learning support for parents and students.'}
              </p>
            </div>
            <div className="px-5 py-3 bg-white text-[#2A1E4D] rounded-2xl border-2 border-[#2A1E4D] shadow-[3px_3px_0px_#2A1E4D] font-black text-xs sm:text-sm shrink-0 flex items-center gap-2">
              <Award className="w-5 h-5 text-[#FFCB3D]" />
              <span>100% Kid Safe</span>
            </div>
          </div>

          {/* Testimonial Quote */}
          <div className="p-6 sm:p-8 bg-[#F8FAFC] rounded-3xl border-2.5 border-[#2A1E4D] space-y-4 max-w-3xl mx-auto text-center">
            <div className="text-3xl text-[#FFCB3D] font-black">“</div>
            <p className="text-sm sm:text-base font-bold text-[#2A1E4D] italic leading-relaxed">
              {isKhmer 
                ? '« ទន្សាយបានផ្លាស់ប្តូរការធ្វើកិច្ចការផ្ទះរបស់កូនខ្ញុំយ៉ាងខ្លាំង! កាលពីមុន កូនប្រុសខ្ញុំរៀនថ្នាក់ទី ៤ តែងតែជួបការលំបាកជាមួយមុខវិជ្ជាគណិតវិទ្យា ប៉ុន្តែឥឡូវនេះ ទន្សាយជួយណែនាំគាត់ជាជំហានៗ ជាភាសាខ្មែរ ដោយមិនប្រាប់ចម្លើយភ្លាមៗនោះទេ។ គាត់រៀនយល់ និងសប្បាយចិត្ត! »' 
                : '"Tunsay transformed our evening homework routine. My 4th grader used to get frustrated with Math, but now Tunsay guides him step-by-step in Khmer without giving away answers. Highly recommended for families!"'}
            </p>
            <div className="pt-2">
              <div className="font-black text-sm text-[#2A1E4D]">លោក ឡេង & អ្នកស្រី សុភាព (Lok Leng & Neakrue Sopheap)</div>
              <div className="text-xs font-semibold text-[#6C4FF6]">
                {isKhmer ? 'មាតាបិតាសិស្សថ្នាក់ទី ៤' : 'Parents of Grade 4 Student'}
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Subjects & Grades Supported */}
      <section className="py-14 bg-[#F8FAFC]">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 space-y-8 text-center">
          <div className="space-y-2">
            <h2 className="text-xl sm:text-2xl font-black font-heading text-[#2A1E4D]">
              {isKhmer ? 'មុខវិជ្ជា និងថ្នាក់រៀនដែលគាំទ្រ' : 'Subjects & Grades Supported'}
            </h2>
            <p className="text-xs sm:text-sm font-medium text-[#2A1E4D]/70">
              {isKhmer ? 'រចនាឡើងយ៉ាងពិសេសសម្រាប់សិស្សបឋមសិក្សា' : 'Specially designed for primary school students'}
            </p>
          </div>

          {/* Subjects Row */}
          <div className="flex flex-wrap items-center justify-center gap-4">
            <div className="px-5 py-3 bg-[#3EC6E0]/20 text-[#2A1E4D] rounded-2xl border-2 border-[#2A1E4D] shadow-[2px_2px_0px_#2A1E4D] font-black text-sm flex items-center gap-2">
              <Calculator className="w-5 h-5 text-[#2A1E4D]" />
              <span>{isKhmer ? 'គណិតវិទ្យា (Math)' : 'Mathematics'}</span>
            </div>
            <div className="px-5 py-3 bg-[#6FCF6F]/20 text-[#2A1E4D] rounded-2xl border-2 border-[#2A1E4D] shadow-[2px_2px_0px_#2A1E4D] font-black text-sm flex items-center gap-2">
              <Atom className="w-5 h-5 text-[#2A1E4D]" />
              <span>{isKhmer ? 'វិទ្យាសាស្ត្រ (Science)' : 'Science'}</span>
            </div>
            <div className="px-5 py-3 bg-[#FFCB3D]/30 text-[#2A1E4D] rounded-2xl border-2 border-[#2A1E4D] shadow-[2px_2px_0px_#2A1E4D] font-black text-sm flex items-center gap-2">
              <Languages className="w-5 h-5 text-[#2A1E4D]" />
              <span>{isKhmer ? 'ភាសាអង់គ្លេស (English)' : 'English Language'}</span>
            </div>
          </div>

          {/* Grade Badges Row */}
          <div className="flex flex-wrap items-center justify-center gap-2.5 pt-2">
            {[1, 2, 3, 4, 5, 6].map((g) => (
              <div
                key={g}
                className="px-4 py-2 bg-white text-[#2A1E4D] font-black text-xs rounded-xl border-2 border-[#2A1E4D] shadow-[2px_2px_0px_#2A1E4D]"
              >
                {isKhmer ? `ថ្នាក់ទី ${g}` : `Grade ${g}`}
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Final CTA Band */}
      <section className="py-16 bg-[#6C4FF6] text-white relative overflow-hidden">
        <div className="max-w-4xl mx-auto px-4 text-center space-y-6 relative z-10">
          <TunsayAvatar size="md" state="celebrating" showBadge={false} className="mx-auto" />
          <h2 className="text-2xl sm:text-4xl font-black font-heading text-[#FFCB3D]">
            {isKhmer ? 'ត្រៀមខ្លួនធ្វើឱ្យការធ្វើកិច្ចការផ្ទះលែងជាការលំបាកហើយឬនៅ?' : 'Ready to Make Homework Stress-Free?'}
          </h2>
          <p className="text-sm sm:text-base font-medium text-white/90 max-w-xl mx-auto">
            {isKhmer 
              ? 'ចូលរួមជាមួយទន្សាយ ដើម្បីជួយឱ្យកូនរបស់អ្នករៀនយល់ និងរីកចម្រើនជារៀងរាល់ថ្ងៃ។' 
              : 'Join Tunsay today and help your child build confidence and problem-solving skills.'}
          </p>

          <div className="pt-2 flex flex-col sm:flex-row items-center justify-center gap-4">
            <button
              type="button"
              onClick={onNavigateToLogin}
              className="px-8 py-4 bg-[#FFCB3D] hover:bg-[#FFD768] text-[#2A1E4D] font-black text-base rounded-2xl border-3 border-[#2A1E4D] shadow-[4px_4px_0px_#2A1E4D] hover:-translate-y-0.5 active:translate-y-0.5 transition-all cursor-pointer flex items-center gap-2"
            >
              <span>{isKhmer ? 'ចាប់ផ្តើមរៀនជាមួយទន្សាយ' : 'Start Learning with Tunsay'}</span>
              <ArrowRight className="w-5 h-5 stroke-[2.5]" />
            </button>
          </div>
        </div>
      </section>

      {/* Public Footer */}
      <footer className="bg-[#2A1E4D] text-white py-10 border-t-4 border-[#FFCB3D]">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 space-y-6">
          <div className="flex flex-col md:flex-row items-center justify-between gap-6 pb-6 border-b border-white/10">
            {/* Footer Brand */}
            <div className="flex items-center gap-3">
              <div className="w-9 h-9 bg-[#FFCB3D] rounded-xl flex items-center justify-center border border-white/20">
                <TunsayAvatar size="sm" state="idle" showBadge={false} />
              </div>
              <div>
                <div className="font-black text-base font-heading text-white">Tunsay — Homework Tutor</div>
                <div className="text-xs text-white/70">Personal AI Companion</div>
              </div>
            </div>

            {/* Footer Links */}
            <div className="flex flex-wrap items-center justify-center gap-6 text-xs font-bold text-white/80">
              <button
                type="button"
                onClick={scrollToHowItWorks}
                className="hover:text-[#FFCB3D] transition-colors cursor-pointer"
              >
                {isKhmer ? 'របៀបដំណើរការ' : 'How it works'}
              </button>
              <span className="opacity-30">•</span>
              <button
                type="button"
                onClick={scrollToAboutTunsay}
                className="hover:text-[#FFCB3D] transition-colors cursor-pointer"
              >
                {isKhmer ? 'អំពីទន្សាយ' : 'About Tunsay'}
              </button>
              <span className="opacity-30">•</span>
              <button
                type="button"
                onClick={() => setActiveModal('privacy')}
                className="hover:text-[#FFCB3D] transition-colors cursor-pointer"
              >
                {isKhmer ? 'សុវត្ថិភាព & ឯកជនភាព' : 'Safety & Privacy'}
              </button>
              <span className="opacity-30">•</span>
              <button
                type="button"
                onClick={() => setActiveModal('contact')}
                className="hover:text-[#FFCB3D] transition-colors cursor-pointer"
              >
                {isKhmer ? 'ទំនាក់ទំនង' : 'Contact Support'}
              </button>
            </div>
          </div>

          <div className="text-center text-xs text-white/60 font-medium">
            © 2026 Tunsay. All rights reserved. Tunsay Homework Tutor is built for educational support.
          </div>
        </div>
      </footer>

      {/* Safety & Privacy Modal */}
      {activeModal === 'privacy' && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-[#2A1E4D]/70 backdrop-blur-sm p-4 animate-fadeIn">
          <div className="bg-white rounded-3xl border-3 border-[#2A1E4D] shadow-[8px_8px_0px_#2A1E4D] max-w-lg w-full p-6 sm:p-8 space-y-6 relative max-h-[90vh] overflow-y-auto text-[#2A1E4D]">
            <button
              type="button"
              onClick={() => setActiveModal(null)}
              className="absolute top-4 right-4 w-9 h-9 bg-[#F1F5F9] hover:bg-[#FF6FA3] hover:text-white text-[#2A1E4D] rounded-full border-2 border-[#2A1E4D] flex items-center justify-center transition-all cursor-pointer font-black"
            >
              <X className="w-5 h-5" />
            </button>

            <div className="flex items-center gap-3 border-b-2 border-[#2A1E4D]/10 pb-4">
              <div className="w-12 h-12 bg-[#3EC6E0] text-white rounded-2xl border-2 border-[#2A1E4D] shadow-[2px_2px_0px_#2A1E4D] flex items-center justify-center shrink-0">
                <Shield className="w-6 h-6" />
              </div>
              <div>
                <h3 className="text-xl font-black font-heading text-[#2A1E4D]">
                  {isKhmer ? 'សុវត្ថិភាពកុមារ & ឯកជនភាព' : 'Child Safety & Privacy'}
                </h3>
                <p className="text-xs text-[#2A1E4D]/70 font-bold">
                  {isKhmer ? 'គោលការណ៍ណែនាំសុវត្ថិភាព AI សម្រាប់កុមារ' : 'Safe AI Principles for Young Learners'}
                </p>
              </div>
            </div>

            <div className="space-y-4 text-xs sm:text-sm font-medium leading-relaxed">
              <div className="p-3.5 bg-[#EAF2FF] rounded-2xl border-2 border-[#2A1E4D]/20 space-y-1">
                <div className="font-extrabold text-[#2A1E4D] flex items-center gap-2">
                  <ShieldCheck className="w-4 h-4 text-[#6C4FF6]" />
                  <span>{isKhmer ? '១. សុវត្ថិភាពកុមារ ១០០%' : '1. 100% Child-Safe AI Guardrails'}</span>
                </div>
                <p className="text-[#2A1E4D]/80 text-xs">
                  {isKhmer 
                    ? 'ទន្សាយ ត្រូវបានរចនាឡើងយ៉ាងម៉ត់ចត់ ដើម្បីឆ្លើយតបតែសំណួរដែលទាក់ទងនឹងការសិក្សា (គណិតវិទ្យា វិទ្យាសាស្ត្រ និងភាសា) ដោយមិនមានខ្លឹមសារមិនសមរម្យឡើយ។' 
                    : 'Tunsay is strictly guardrailed for educational topics (Math, Science, English). Unsuitable content or non-educational topics are automatically filtered.'}
                </p>
              </div>

              <div className="p-3.5 bg-[#FEF3C7] rounded-2xl border-2 border-[#2A1E4D]/20 space-y-1">
                <div className="font-extrabold text-[#2A1E4D] flex items-center gap-2">
                  <CheckCircle2 className="w-4 h-4 text-[#D97706]" />
                  <span>{isKhmer ? '២. រក្សាឯកជនភាពទិន្នន័យ' : '2. Strict Data Privacy & No Data Selling'}</span>
                </div>
                <p className="text-[#2A1E4D]/80 text-xs">
                  {isKhmer 
                    ? 'រាល់រូបថតលំហាត់ និងការសន្ទនាត្រូវបានការពារយ៉ាងមានសុវត្ថិភាព។ យើងមិនលក់ ឬចែករំលែកទិន្នន័យរបស់សិស្ស ឬមាតាបិតា ទៅកាន់ក្រុមហ៊ុនពាណិជ្ជកម្មឡើយ។' 
                    : 'All homework scans and student chats are encrypted and kept confidential. We never sell or share student data with third-party advertisers.'}
                </p>
              </div>

              <div className="p-3.5 bg-[#ECFDF5] rounded-2xl border-2 border-[#2A1E4D]/20 space-y-1">
                <div className="font-extrabold text-[#2A1E4D] flex items-center gap-2">
                  <HeartHandshake className="w-4 h-4 text-[#059669]" />
                  <span>{isKhmer ? '៣. គ្មានផ្ទាំងពាណិជ្ជកម្មរំខាន' : '3. Ad-Free & Focus-Oriented'}</span>
                </div>
                <p className="text-[#2A1E4D]/80 text-xs">
                  {isKhmer 
                    ? 'គ្មានពាណិជ្ជកម្ម គ្មានការរំខាន ដើម្បីឱ្យកុមារអាចផ្តោតអារម្មណ៍រៀនសូត្របានពេញលេញ។' 
                    : 'Tunsay is completely ad-free, ensuring a quiet and distraction-free learning environment for students.'}
                </p>
              </div>
            </div>

            <div className="pt-2">
              <button
                type="button"
                onClick={() => setActiveModal(null)}
                className="w-full py-3 bg-[#FFCB3D] hover:bg-[#FFD768] text-[#2A1E4D] font-extrabold text-sm rounded-2xl border-2 border-[#2A1E4D] shadow-[3px_3px_0px_#2A1E4D] transition-all cursor-pointer"
              >
                {isKhmer ? 'យល់ព្រម និងបិទ' : 'Understood & Close'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Contact Support Modal */}
      {activeModal === 'contact' && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-[#2A1E4D]/70 backdrop-blur-sm p-4 animate-fadeIn">
          <div className="bg-white rounded-3xl border-3 border-[#2A1E4D] shadow-[8px_8px_0px_#2A1E4D] max-w-lg w-full p-6 sm:p-8 space-y-6 relative max-h-[90vh] overflow-y-auto text-[#2A1E4D]">
            <button
              type="button"
              onClick={() => {
                setActiveModal(null);
                setContactSent(false);
              }}
              className="absolute top-4 right-4 w-9 h-9 bg-[#F1F5F9] hover:bg-[#FF6FA3] hover:text-white text-[#2A1E4D] rounded-full border-2 border-[#2A1E4D] flex items-center justify-center transition-all cursor-pointer font-black"
            >
              <X className="w-5 h-5" />
            </button>

            <div className="flex items-center gap-3 border-b-2 border-[#2A1E4D]/10 pb-4">
              <div className="w-12 h-12 bg-[#FFCB3D] text-[#2A1E4D] rounded-2xl border-2 border-[#2A1E4D] shadow-[2px_2px_0px_#2A1E4D] flex items-center justify-center shrink-0">
                <Mail className="w-6 h-6" />
              </div>
              <div>
                <h3 className="text-xl font-black font-heading text-[#2A1E4D]">
                  {isKhmer ? 'ទំនាក់ទំនងក្រុមការងារ ទន្សាយ' : 'Contact Tunsay Support'}
                </h3>
                <p className="text-xs text-[#2A1E4D]/70 font-bold">
                  {isKhmer ? 'យើងរង់ចាំជួយសម្រួលការរៀនសូត្ររបស់កូនអ្នក' : 'We are here to help parents, students & teachers'}
                </p>
              </div>
            </div>

            {contactSent ? (
              <div className="bg-[#ECFDF5] p-6 rounded-2xl border-2 border-[#2A1E4D] text-center space-y-3">
                <div className="w-12 h-12 bg-[#6FCF6F] text-[#2A1E4D] rounded-full border-2 border-[#2A1E4D] flex items-center justify-center mx-auto">
                  <Check className="w-6 h-6 stroke-[3]" />
                </div>
                <h4 className="text-base font-black font-heading text-[#2A1E4D]">
                  {isKhmer ? 'សាររបស់អ្នកត្រូវបានផ្ញើដោយជោគជ័យ!' : 'Message Sent Successfully!'}
                </h4>
                <p className="text-xs font-medium text-[#2A1E4D]/80">
                  {isKhmer 
                    ? 'សូមអរគុណសម្រាប់ការទាក់ទងមកកាន់ ទន្សាយ។ ក្រុមការងារនឹងឆ្លើយតបទៅកាន់អ៊ីមែលរបស់អ្នកក្នុងពេលឆាប់ៗនេះ។' 
                    : 'Thank you for reaching out to Tunsay! Our support team will get back to your email shortly.'}
                </p>
                <button
                  type="button"
                  onClick={() => {
                    setContactSent(false);
                    setActiveModal(null);
                  }}
                  className="px-6 py-2 bg-[#FFCB3D] text-[#2A1E4D] font-black text-xs rounded-xl border-2 border-[#2A1E4D] shadow-[2px_2px_0px_#2A1E4D] cursor-pointer"
                >
                  {isKhmer ? 'បិទ' : 'Done'}
                </button>
              </div>
            ) : (
              <form
                onSubmit={(e) => {
                  e.preventDefault();
                  setContactSent(true);
                }}
                className="space-y-4 text-xs sm:text-sm font-medium"
              >
                <div className="space-y-1.5">
                  <label className="block text-xs font-extrabold text-[#2A1E4D]">
                    {isKhmer ? 'ឈ្មោះរបស់អ្នក / Name' : 'Your Name'}
                  </label>
                  <input
                    type="text"
                    required
                    value={contactForm.name}
                    onChange={(e) => setContactForm({ ...contactForm, name: e.target.value })}
                    placeholder={isKhmer ? 'ឧ. សុខា / Sokha' : 'e.g. Sochea Parent'}
                    className="w-full px-3.5 py-2.5 bg-[#F8FAFC] border-2 border-[#2A1E4D] rounded-xl focus:outline-none focus:bg-white focus:ring-2 focus:ring-[#6C4FF6] text-xs font-bold"
                  />
                </div>

                <div className="space-y-1.5">
                  <label className="block text-xs font-extrabold text-[#2A1E4D]">
                    {isKhmer ? 'អ៊ីមែល ឬលេខទូរស័ព្ទ / Email or Phone' : 'Email or Phone'}
                  </label>
                  <input
                    type="text"
                    required
                    value={contactForm.email}
                    onChange={(e) => setContactForm({ ...contactForm, email: e.target.value })}
                    placeholder="parent@example.com"
                    className="w-full px-3.5 py-2.5 bg-[#F8FAFC] border-2 border-[#2A1E4D] rounded-xl focus:outline-none focus:bg-white focus:ring-2 focus:ring-[#6C4FF6] text-xs font-bold"
                  />
                </div>

                <div className="space-y-1.5">
                  <label className="block text-xs font-extrabold text-[#2A1E4D]">
                    {isKhmer ? 'សារ ឬសំណួររបស់អ្នក / Message' : 'Your Question or Feedback'}
                  </label>
                  <textarea
                    required
                    rows={3}
                    value={contactForm.message}
                    onChange={(e) => setContactForm({ ...contactForm, message: e.target.value })}
                    placeholder={isKhmer ? 'សូមសរសេរ សំណួរ ឬមតិយោបល់នៅទីនេះ...' : 'How can we assist you with Tunsay?'}
                    className="w-full px-3.5 py-2.5 bg-[#F8FAFC] border-2 border-[#2A1E4D] rounded-xl focus:outline-none focus:bg-white focus:ring-2 focus:ring-[#6C4FF6] text-xs font-bold resize-none"
                  />
                </div>

                <div className="p-3 bg-[#F1F5F9] rounded-xl border border-[#2A1E4D]/20 flex items-center justify-between text-[11px] font-bold text-[#2A1E4D]/80">
                  <span className="flex items-center gap-1.5">
                    <Mail className="w-3.5 h-3.5 text-[#6C4FF6]" />
                    <span>Direct Email: support@tunsay.app</span>
                  </span>
                </div>

                <button
                  type="submit"
                  className="w-full py-3 bg-[#6C4FF6] hover:bg-[#5839EE] text-white font-extrabold text-sm rounded-2xl border-2 border-[#2A1E4D] shadow-[3px_3px_0px_#2A1E4D] transition-all cursor-pointer flex items-center justify-center gap-2"
                >
                  <span>{isKhmer ? 'ផ្ញើសារ' : 'Send Message'}</span>
                  <Send className="w-4 h-4" />
                </button>
              </form>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

