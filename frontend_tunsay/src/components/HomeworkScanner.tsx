import React, { useState, useRef } from 'react';
import { Camera, Upload, RefreshCw, CheckCircle, ArrowLeft, Sparkles, ChevronLeft, ChevronRight } from 'lucide-react';
import { TunsayAvatar } from './TunsayAvatar';
import { HomeworkProblem, Language } from '../types';
import { MOCK_PROBLEMS } from '../data/mockProblems';
import { sendImageTurn } from '../services/geminiService';

interface HomeworkScannerProps {
  language?: Language;
  onHomeworkConfirmed: (problem: HomeworkProblem) => void;
  onCancel: () => void;
}

export const HomeworkScanner: React.FC<HomeworkScannerProps> = ({
  language = 'km',
  onHomeworkConfirmed,
  onCancel
}) => {
  const isKhmer = language === 'km';
  const [stage, setStage] = useState<'capture' | 'preview' | 'analyzing' | 'confirm'>('capture');
  const [imageUri, setImageUri] = useState<string>('');
  const [uploadedFile, setUploadedFile] = useState<File | null>(null);
  const [selectedProblem, setSelectedProblem] = useState<HomeworkProblem>(MOCK_PROBLEMS[0]);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const sampleScrollRef = useRef<HTMLDivElement>(null);

  const handleSelectSample = (problem: HomeworkProblem) => {
    setSelectedProblem(problem);
    setUploadedFile(null);
    setImageUri(problem.imageUri || 'https://images.unsplash.com/photo-1560806887-1e4cd0b6cbd6?w=600&auto=format&fit=crop&q=80');
    setStage('preview');
  };

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setUploadedFile(file);
      const url = URL.createObjectURL(file);
      setImageUri(url);
      setStage('preview');
    }
  };

  const handleConfirmPhoto = async () => {
    setStage('analyzing');
    if (uploadedFile) {
      try {
        const langParam: Language = language === 'en' ? 'en' : 'km';
        const ocrResult = await sendImageTurn(uploadedFile, 'student', langParam);
        const extractedText = ocrResult?.userTranscript;
        if (extractedText && extractedText.trim()) {
          setSelectedProblem((prev) => ({
            ...prev,
            problemStatementKhmer: isKhmer ? extractedText.trim() : prev.problemStatementKhmer,
            problemStatementEng: !isKhmer ? extractedText.trim() : prev.problemStatementEng,
            titleKhmer: isKhmer ? `លំហាត់ស្កែន៖ ${extractedText.trim()}` : prev.titleKhmer,
            titleEng: !isKhmer ? `Scanned Homework: ${extractedText.trim()}` : prev.titleEng,
          }));
        }
      } catch (err) {
        console.warn('OCR processing fallback:', err);
      }
    }
    setStage('confirm');
  };

  return (
    <div className="w-full max-w-lg mx-auto bg-white rounded-3xl border-3 border-[#2A1E4D] shadow-[6px_6px_0px_#2A1E4D] overflow-hidden animate-fadeIn text-[#2A1E4D] max-h-[85vh] flex flex-col">
      {/* Header */}
      <div className="p-4 bg-[#6C4FF6] border-b-3 border-[#2A1E4D] flex items-center justify-between text-white shrink-0">
        <button
          type="button"
          onClick={onCancel}
          className="px-3 py-1.5 bg-[#FFCB3D] text-[#2A1E4D] rounded-xl border-2 border-[#2A1E4D] shadow-[2px_2px_0px_#2A1E4D] flex items-center gap-1 text-xs font-black cursor-pointer hover:-translate-y-0.5 transition-transform"
        >
          <ArrowLeft className="w-4 h-4 stroke-[3]" /> {isKhmer ? 'ត្រឡប់' : 'Back'}
        </button>
        <div className="flex items-center gap-1.5 font-black text-sm text-[#FFCB3D] drop-shadow-[1px_1px_0px_#2A1E4D]">
          <Camera className="w-4 h-4 stroke-[2.5]" /> {isKhmer ? 'ស្កែនលំហាត់' : 'Homework Scanner'}
        </div>
      </div>

      <div className="flex-1 overflow-y-auto no-scrollbar">
        {/* Stage 1: Capture / Select Sample */}
        {stage === 'capture' && (
          <div className="p-5 sm:p-6 space-y-5 text-center">
            {/* Camera Frame */}
            <div className="relative w-full aspect-4/3 max-h-56 bg-[#EAF2FF] rounded-2xl border-3 border-dashed border-[#2A1E4D] flex flex-col items-center justify-center p-4 text-center group hover:bg-[#FFCB3D]/30 transition-colors">
              {/* Viewfinder Corners */}
              <div className="absolute top-3 left-3 w-5 h-5 border-t-4 border-l-4 border-[#2A1E4D] rounded-tl-lg" />
              <div className="absolute top-3 right-3 w-5 h-5 border-t-4 border-r-4 border-[#2A1E4D] rounded-tr-lg" />
              <div className="absolute bottom-3 left-3 w-5 h-5 border-b-4 border-l-4 border-[#2A1E4D] rounded-bl-lg" />
              <div className="absolute bottom-3 right-3 w-5 h-5 border-b-4 border-r-4 border-[#2A1E4D] rounded-br-lg" />

              <TunsayAvatar size="sm" state="listening" showBadge={false} className="mb-1" />
              <p className="text-sm sm:text-base font-black text-[#2A1E4D] font-heading flex items-center justify-center gap-1.5">
                <Camera className="w-4 h-4 sm:w-5 sm:h-5 text-[#6C4FF6]" />
                {isKhmer ? 'ថតរូបលំហាត់របស់អ្នក' : 'Scan your homework'}
              </p>
              <p className="text-xs font-bold text-[#2A1E4D]/80 mt-0.5 max-w-xs">
                {isKhmer 
                  ? 'ដាក់ក្រដាសលំហាត់របស់អ្នកឲ្យចំកណ្តាលស៊ុម' 
                  : 'Fit your homework page inside the frame'}
              </p>

              <input
                type="file"
                ref={fileInputRef}
                accept="image/*"
                onChange={handleFileUpload}
                className="hidden"
              />

              <button
                type="button"
                onClick={() => fileInputRef.current?.click()}
                className="mt-3 px-5 py-2.5 bg-[#6FCF6F] hover:bg-[#FFCB3D] text-[#2A1E4D] font-black rounded-2xl border-3 border-[#2A1E4D] shadow-[3px_3px_0px_#2A1E4D] hover:-translate-y-0.5 active:translate-y-0.5 active:shadow-[1px_1px_0px_#2A1E4D] transition-all flex items-center gap-2 cursor-pointer text-xs sm:text-sm"
              >
                <Upload className="w-4 h-4 stroke-[2.5]" />
                {isKhmer ? 'ជ្រើសរើសរូបថត' : 'Upload Photo'}
              </button>
            </div>

            {/* Sample Demo Homework Buttons - Single Row Horizontal Scroll with < > */}
            <div className="space-y-2 pt-1 text-left">
              <div className="flex items-center justify-between gap-2">
                <p className="text-xs font-black text-[#2A1E4D] uppercase tracking-wider">
                  {isKhmer 
                    ? 'ឬ ជ្រើសរើសលំហាត់គំរូសម្រាប់ការសាកល្បង៖' 
                    : 'Or select sample homework to try:'}
                </p>
                <div className="flex items-center gap-1 shrink-0">
                  <button
                    type="button"
                    onClick={() => sampleScrollRef.current?.scrollBy({ left: -220, behavior: 'smooth' })}
                    className="p-1 bg-white hover:bg-[#FFCB3D] text-[#2A1E4D] rounded-lg border-2 border-[#2A1E4D] shadow-[1.5px_1.5px_0px_#2A1E4D] cursor-pointer hover:-translate-y-0.5 active:translate-y-0.5 transition-all"
                    aria-label="Previous sample"
                  >
                    <ChevronLeft className="w-3.5 h-3.5 stroke-[3]" />
                  </button>
                  <button
                    type="button"
                    onClick={() => sampleScrollRef.current?.scrollBy({ left: 220, behavior: 'smooth' })}
                    className="p-1 bg-white hover:bg-[#FFCB3D] text-[#2A1E4D] rounded-lg border-2 border-[#2A1E4D] shadow-[1.5px_1.5px_0px_#2A1E4D] cursor-pointer hover:-translate-y-0.5 active:translate-y-0.5 transition-all"
                    aria-label="Next sample"
                  >
                    <ChevronRight className="w-3.5 h-3.5 stroke-[3]" />
                  </button>
                </div>
              </div>

              <div 
                ref={sampleScrollRef}
                className="flex gap-2.5 overflow-x-auto scrollbar-none scroll-smooth pb-1 px-1"
              >
                {MOCK_PROBLEMS.map((prob) => (
                  <button
                    key={prob.id}
                    type="button"
                    onClick={() => handleSelectSample(prob)}
                    className="p-3 rounded-2xl border-3 border-[#2A1E4D] bg-[#EAF2FF] hover:bg-[#FFCB3D] text-left transition-all shadow-[2px_2px_0px_#2A1E4D] flex flex-col justify-between cursor-pointer group shrink-0 w-[210px] sm:w-[230px]"
                  >
                    <div>
                      <span className="text-[10px] font-black text-[#2A1E4D] bg-white px-2 py-0.5 rounded-full border-2 border-[#2A1E4D] inline-block">
                        {isKhmer 
                          ? `ថ្នាក់ទី ${prob.grade} • ${prob.subject === 'math' ? 'គណិត' : prob.subject === 'science' ? 'វិទ្យាសាស្ត្រ' : 'អង់គ្លេស'}` 
                          : `Grade ${prob.grade} • ${prob.subject === 'math' ? 'Math' : prob.subject === 'science' ? 'Science' : 'English'}`}
                      </span>
                      <p className="font-black text-xs text-[#2A1E4D] mt-2 line-clamp-2 leading-tight">
                        {isKhmer ? prob.titleKhmer : prob.titleEng}
                      </p>
                    </div>
                    <div className="flex items-center justify-between mt-2 pt-1 border-t-2 border-[#2A1E4D]/15">
                      <span className="text-[10px] font-black text-[#6C4FF6]">
                        {isKhmer ? 'សាកល្បង' : 'Try sample'}
                      </span>
                      <Sparkles className="w-3.5 h-3.5 text-[#FF6FA3]" />
                    </div>
                  </button>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Stage 2: Preview */}
        {stage === 'preview' && (
          <div className="p-6 space-y-5 text-center">
            <div className="relative rounded-2xl overflow-hidden border-3 border-[#2A1E4D] shadow-[4px_4px_0px_#2A1E4D] max-h-64 bg-black/5">
              <img src={imageUri} alt="Homework preview" className="w-full h-full object-cover" />
            </div>

            <div className="flex gap-3">
              <button
                type="button"
                onClick={() => setStage('capture')}
                className="flex-1 py-3 px-4 rounded-2xl border-3 border-[#2A1E4D] bg-white text-[#2A1E4D] font-black text-sm flex items-center justify-center gap-1.5 shadow-[3px_3px_0px_#2A1E4D] hover:-translate-y-0.5 transition-all cursor-pointer"
              >
                <RefreshCw className="w-4 h-4 stroke-[2.5]" /> {isKhmer ? 'ថតសារថ្មី' : 'Retake'}
              </button>
              <button
                type="button"
                onClick={handleConfirmPhoto}
                className="flex-1 py-3 px-4 rounded-2xl bg-[#6FCF6F] text-[#2A1E4D] font-black text-sm border-3 border-[#2A1E4D] shadow-[3px_3px_0px_#2A1E4D] flex items-center justify-center gap-1.5 hover:-translate-y-0.5 transition-all cursor-pointer"
              >
                <CheckCircle className="w-4 h-4 stroke-[2.5]" /> {isKhmer ? 'ប្រើរូបនេះ' : 'Use Photo'}
              </button>
            </div>
          </div>
        )}

        {/* Stage 3: Tunsay Reading Analysis */}
        {stage === 'analyzing' && (
          <div className="p-10 text-center space-y-4">
            <TunsayAvatar size="lg" state="thinking" showBadge={false} className="mx-auto" />
            <div className="space-y-1">
              <h3 className="text-lg font-black text-[#2A1E4D] font-heading flex items-center justify-center gap-2">
                <Sparkles className="w-5 h-5 text-[#FF6FA3] animate-spin" />
                {isKhmer ? 'ទន្សាយកំពុងអានលំហាត់របស់អ្នក...' : 'Tunsay is reading your homework...'}
              </h3>
            </div>
            <div className="w-48 h-3 bg-[#EAF2FF] border-2 border-[#2A1E4D] rounded-full mx-auto overflow-hidden">
              <div className="h-full bg-[#3EC6E0] animate-pulse rounded-full w-3/4" />
            </div>
          </div>
        )}

        {/* Stage 4: Confirm Analyzed Question */}
        {stage === 'confirm' && (
          <div className="p-6 space-y-5">
            <div className="flex items-center gap-3 p-3 bg-[#FFCB3D] rounded-2xl border-3 border-[#2A1E4D] shadow-[3px_3px_0px_#2A1E4D]">
              <TunsayAvatar size="sm" state="explaining" showBadge={false} />
              <div>
                <p className="font-black text-sm text-[#2A1E4D]">
                  {isKhmer 
                    ? 'ខ្ញុំឃើញលំហាត់របស់អ្នកហើយ! តោះដោះស្រាយវាជាមួយគ្នា!' 
                    : "I can see your homework problem. Let's solve it together!"}
                </p>
              </div>
            </div>

            <div className="p-4 bg-[#EAF2FF] rounded-2xl border-3 border-[#2A1E4D] shadow-[3px_3px_0px_#2A1E4D] space-y-2">
              <p className="text-xs font-black text-[#6C4FF6] uppercase">
                {isKhmer ? 'សំណួរដែលស្កែនបាន៖' : 'Detected Question:'}
              </p>
              <p className="font-black text-base text-[#2A1E4D]">
                {isKhmer ? selectedProblem.problemStatementKhmer : selectedProblem.problemStatementEng}
              </p>
            </div>

            <p className="text-center font-black text-sm text-[#2A1E4D]">
              {isKhmer ? 'តើសំណួរនេះត្រឹមត្រូវទេ?' : 'Does this look correct?'}
            </p>

            <div className="flex gap-3">
              <button
                type="button"
                onClick={() => setStage('capture')}
                className="flex-1 py-3 px-4 rounded-2xl border-3 border-[#2A1E4D] bg-white text-[#2A1E4D] font-black text-xs sm:text-sm shadow-[3px_3px_0px_#2A1E4D] flex items-center justify-center gap-1 transition-all cursor-pointer"
              >
                <RefreshCw className="w-4 h-4 stroke-[2.5]" /> {isKhmer ? 'ថតឡើងវិញ' : 'Retake Photo'}
              </button>
              <button
                type="button"
                onClick={() => onHomeworkConfirmed(selectedProblem)}
                className="flex-1 py-3 px-4 rounded-2xl bg-[#6FCF6F] text-[#2A1E4D] font-black text-xs sm:text-sm border-3 border-[#2A1E4D] shadow-[3px_3px_0px_#2A1E4D] flex items-center justify-center gap-1 transition-all cursor-pointer hover:-translate-y-0.5 active:translate-y-0.5"
              >
                <span>{isKhmer ? 'តោះចាប់ផ្តើម!' : 'Yes, let\'s start!'}</span>
                <CheckCircle className="w-4 h-4 stroke-[2.5]" />
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
