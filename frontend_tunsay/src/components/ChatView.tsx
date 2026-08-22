import React, { useState, useRef, useEffect } from 'react';
import { ChatMessage, HomeworkProblem, UserProfile } from '../types';
import { TunsayAvatar } from './TunsayAvatar';
import { StepTrail } from './StepTrail';
import { StepCard } from './StepCard';
import { HintSheet } from './HintSheet';
import { ExplanationCard } from './ExplanationCard';
import { askTunsayTutor, submitStepAnswer, fetchAIHint, deductHintStars } from '../services/geminiService';
import { getDisplayName } from '../utils/language';
import { MOCK_PROBLEMS, generateHistoryChatForProblem } from '../data/mockProblems';
import { Send, Mic, Camera, User, GraduationCap, Users, ArrowLeft, Plus, Calculator, Atom, BookOpen, Languages, ChevronLeft, ChevronRight } from 'lucide-react';

interface ChatViewProps {
  profile: UserProfile;
  initialProblem?: HomeworkProblem;
  initialQuery?: string;
  onClearInitialQuery?: () => void;
  chatMessages?: ChatMessage[];
  onUpdateMessages?: (messages: ChatMessage[]) => void;
  onOpenVoiceModal: () => void;
  onOpenScanner: () => void;
  onProblemCompleted: () => void;
  onBackToHome?: () => void;
}

export const ChatView: React.FC<ChatViewProps> = ({
  profile,
  initialProblem,
  initialQuery,
  onClearInitialQuery,
  chatMessages,
  onUpdateMessages,
  onOpenVoiceModal,
  onOpenScanner,
  onProblemCompleted,
  onBackToHome
}) => {
  const isKhmer = profile.language === 'km';
  const [activeProblem, setActiveProblem] = useState<HomeworkProblem | undefined>(initialProblem);
  const [currentStepIndex, setCurrentStepIndex] = useState<number>(0);
  
  // Local messages state, falling back to chatMessages or default greeting
  const [messages, setMessages] = useState<ChatMessage[]>(() => {
    if (chatMessages && chatMessages.length > 0) {
      return chatMessages;
    }
    return [
      {
        id: 'init-msg',
        sender: 'sayo',
        textKhmer: `សួស្តី ${getDisplayName(profile.name, true)}! ខ្ញុំគឺទន្សាយ គ្រូបង្រៀន AI។ តើអ្នកមានលំហាត់អ្វីចង់ឱ្យខ្ញុំជួយទេ? អ្នកអាចថតរូបស្កែនលំហាត់ ប្រើសំឡេង ឬវាយបញ្ចូលសំណួរនៅខាងក្រោម!`,
        textEng: `Hi ${getDisplayName(profile.name, false)}! I am Tunsay, your AI Tutor. What homework would you like help with? You can scan a photo, use voice, or type your question below!`,
        timestamp: 'Just now'
      }
    ];
  });

  const [inputQuery, setInputQuery] = useState('');
  const [isSayoThinking, setIsSayoThinking] = useState(false);
  const [sayoStatus, setSayoStatus] = useState<'idle' | 'thinking' | 'celebrating'>('idle');
  const [thinkingTextIdx, setThinkingTextIdx] = useState(0);

  // Sync internal messages changes back to parent state
  const updateMessages = (newMsgs: ChatMessage[]) => {
    setMessages(newMsgs);
    if (onUpdateMessages) {
      onUpdateMessages(newMsgs);
    }
  };

  // Reaction state transitions
  useEffect(() => {
    if (isSayoThinking) {
      setSayoStatus('thinking');
    } else if (sayoStatus === 'thinking') {
      setSayoStatus('celebrating');
      const timer = setTimeout(() => {
        setSayoStatus('idle');
      }, 2800);
      return () => clearTimeout(timer);
    }
  }, [isSayoThinking]);

  // Cycling text variants during thinking state
  useEffect(() => {
    if (sayoStatus === 'thinking') {
      const interval = setInterval(() => {
        setThinkingTextIdx((prev) => (prev + 1) % 3);
      }, 1400);
      return () => clearInterval(interval);
    } else {
      setThinkingTextIdx(0);
    }
  }, [sayoStatus]);

  const thinkingTextsKhmer = [
    'កំពុងគិត...',
    'សាយ៉ូ កំពុងរកចម្លើយ!',
    'ជិតរួចរាល់ហើយ!'
  ];

  const thinkingTextsEng = [
    'Thinking...',
    'Sayo is on it!',
    'Almost there!'
  ];

  const celebratoryTextKhmer = 'រួចរាល់ហើយ! 🎉';
  const celebratoryTextEng = 'Aha! Got it! 🎉';

  const idleTextKhmer = 'សាយ៉ូ រង់ចាំសំណួរ! 🐰';
  const idleTextEng = 'Ready to help! 🐰';

  // Sheets state
  const [isHintOpen, setIsHintOpen] = useState(false);
  const [isExplainOpen, setIsExplainOpen] = useState(false);

  const chatEndRef = useRef<HTMLDivElement>(null);
  const chatMarqueeRef = useRef<HTMLDivElement>(null);
  const [isChatMarqueeHovered, setIsChatMarqueeHovered] = useState(false);

  useEffect(() => {
    if (isChatMarqueeHovered) return;
    const interval = setInterval(() => {
      if (chatMarqueeRef.current) {
        const { scrollLeft, scrollWidth, clientWidth } = chatMarqueeRef.current;
        if (scrollLeft + clientWidth >= scrollWidth - 10) {
          chatMarqueeRef.current.scrollTo({ left: 0, behavior: 'smooth' });
        } else {
          chatMarqueeRef.current.scrollBy({ left: 240, behavior: 'smooth' });
        }
      }
    }, 3500);
    return () => clearInterval(interval);
  }, [isChatMarqueeHovered]);

  const handleChatScrollLeft = () => {
    if (chatMarqueeRef.current) {
      chatMarqueeRef.current.scrollBy({ left: -260, behavior: 'smooth' });
    }
  };

  const handleChatScrollRight = () => {
    if (chatMarqueeRef.current) {
      chatMarqueeRef.current.scrollBy({ left: 260, behavior: 'smooth' });
    }
  };

  useEffect(() => {
    if (initialProblem) {
      setActiveProblem(initialProblem);
      setCurrentStepIndex(0);
      const historyMsgs = generateHistoryChatForProblem(initialProblem, profile.name);
      updateMessages(historyMsgs);
    }
  }, [initialProblem]);

  useEffect(() => {
    if (initialQuery && initialQuery.trim()) {
      const queryText = initialQuery.trim();
      if (onClearInitialQuery) {
        onClearInitialQuery();
      }
      
      const userMsg: ChatMessage = {
        id: Date.now().toString(),
        sender: 'user',
        textEng: queryText,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      };

      const updatedWithUser = [...messages, userMsg];
      updateMessages(updatedWithUser);
      setIsSayoThinking(true);

      askTunsayTutor(queryText, profile.mode, activeProblem, profile.language, currentStepIndex).then((sayoRes) => {
        setIsSayoThinking(false);
        const sayoMsg: ChatMessage = {
          id: (Date.now() + 1).toString(),
          sender: 'sayo',
          textKhmer: sayoRes.textKhmer,
          textEng: sayoRes.textEng,
          isSafetyRefusal: sayoRes.isSafetyRefusal,
          isParentHelp: profile.mode === 'parent',
          suggestedNext: sayoRes.suggestedNext,
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
        };
        updateMessages([...updatedWithUser, sayoMsg]);
      });
    }
  }, [initialQuery]);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isSayoThinking, currentStepIndex]);

  const currentStep = activeProblem?.steps?.[currentStepIndex];

  const handleNewChat = () => {
    setActiveProblem(undefined);
    setCurrentStepIndex(0);
    const freshGreeting: ChatMessage = {
      id: Date.now().toString(),
      sender: 'sayo',
      textKhmer: `សួស្តី ${getDisplayName(profile.name, true)}! ខ្ញុំគឺទន្សាយ គ្រូបង្រៀន AI។ តើអ្នកមានលំហាត់អ្វីចង់ឱ្យខ្ញុំជួយទេ? អ្នកអាចថតរូបស្កែនលំហាត់ ប្រើសំឡេង ឬវាយបញ្ចូលសំណួរនៅខាងក្រោម!`,
      textEng: `Hi ${getDisplayName(profile.name, false)}! I am Tunsay, your AI Tutor. What homework would you like help with? You can scan a photo, use voice, or type your question below!`,
      timestamp: 'Just now'
    };
    updateMessages([freshGreeting]);
  };

  const handleSelectTopicCard = (prob: HomeworkProblem) => {
    setActiveProblem(prob);
    setCurrentStepIndex(0);
    const historyMsgs = generateHistoryChatForProblem(prob, profile.name);
    updateMessages(historyMsgs);
  };

  const handleStepAnswer = async (studentAnswer: string): Promise<boolean> => {
    if (!currentStep || !activeProblem) return false;

    // Call server-side checker
    const gradingRes = await submitStepAnswer(
      activeProblem.id,
      currentStep.id,
      studentAnswer,
      profile.language
    );

    const isCorrect = gradingRes.isCorrect;

    // Record user answer in chat
    const userMsg: ChatMessage = {
      id: Date.now().toString(),
      sender: 'user',
      textKhmer: profile.language === 'km' ? studentAnswer : '',
      textEng: profile.language === 'en' ? studentAnswer : '',
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    };

    let updated = [...messages, userMsg];
    updateMessages(updated);

    // Record Tunsay's feedback in chat
    const sayoMsg: ChatMessage = {
      id: (Date.now() + 1).toString(),
      sender: 'sayo',
      textKhmer: gradingRes.feedbackKhmer,
      textEng: gradingRes.feedbackEng,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    };
    updated = [...updated, sayoMsg];
    updateMessages(updated);

    if (isCorrect) {
      // Progress step
      if (currentStepIndex + 1 < activeProblem.steps.length) {
        setTimeout(() => {
          setCurrentStepIndex((prev) => prev + 1);
        }, 800);
      } else {
        // Full problem complete!
        setTimeout(() => {
          onProblemCompleted();
        }, 1200);
      }
    }

    return isCorrect;
  };

  const handleSendMessage = async () => {
    if (!inputQuery.trim()) return;

    const userText = inputQuery.trim();
    setInputQuery('');

    const userMsg: ChatMessage = {
      id: Date.now().toString(),
      sender: 'user',
      textEng: userText,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    };

    const updatedWithUser = [...messages, userMsg];
    updateMessages(updatedWithUser);
    setIsSayoThinking(true);

    const sayoRes = await askTunsayTutor(userText, profile.mode, activeProblem, profile.language, currentStepIndex);

    setIsSayoThinking(false);

    const sayoMsg: ChatMessage = {
      id: (Date.now() + 1).toString(),
      sender: 'sayo',
      textKhmer: sayoRes.textKhmer,
      textEng: sayoRes.textEng,
      isSafetyRefusal: sayoRes.isSafetyRefusal,
      isParentHelp: profile.mode === 'parent',
      suggestedNext: sayoRes.suggestedNext,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    };

    updateMessages([...updatedWithUser, sayoMsg]);
  };

  return (
    <div className="w-full h-full flex-1 flex flex-row items-stretch gap-4 sm:gap-5 overflow-hidden">
      {/* Standalone Left Mascot Status Panel (30% Width Layout - Hidden on mobile/tablet for full screen chat) */}
      <div className="hidden lg:flex lg:w-[30%] lg:min-w-[220px] lg:max-w-[360px] shrink-0 h-full bg-[#F1EFFF] rounded-3xl border-3 border-[#2A1E4D] shadow-[6px_6px_0px_#2A1E4D] p-4 flex-col justify-between items-center text-center select-none z-10 relative overflow-hidden">
        {/* Decorative background soft glow */}
        <div className="absolute -top-10 -left-10 w-28 h-28 bg-[#FFCB3D]/25 rounded-full blur-sm pointer-events-none" />
        <div className="absolute -bottom-10 -right-10 w-28 h-28 bg-[#FF6FA3]/25 rounded-full blur-sm pointer-events-none" />

        {/* Content Group (Top Badge + Mascot + Status Message) */}
        <div className="w-full flex flex-col items-center gap-4 pt-1 relative z-10 my-auto">
          {/* Top Status Pill Badge */}
          <div className="w-full max-w-[220px]">
            {sayoStatus === 'thinking' ? (
              <span className="px-3 py-1.5 bg-[#FF6FA3] text-white text-xs font-black rounded-full border-2 border-[#2A1E4D] shadow-[2px_2px_0px_#2A1E4D] inline-flex items-center justify-center gap-1.5 animate-pulse uppercase tracking-wider w-full">
                <span className="w-2 h-2 bg-white rounded-full animate-ping shrink-0" />
                <span className="truncate">{isKhmer ? 'កំពុងគិត...' : 'Thinking...'}</span>
              </span>
            ) : sayoStatus === 'celebrating' ? (
              <span className="px-3 py-1.5 bg-[#6FCF6F] text-[#2A1E4D] text-xs font-black rounded-full border-2 border-[#2A1E4D] shadow-[2px_2px_0px_#2A1E4D] inline-flex items-center justify-center gap-1.5 uppercase tracking-wider w-full animate-bounce">
                ✨ <span className="truncate">{isKhmer ? 'រួចរាល់ហើយ!' : 'Done!'}</span>
              </span>
            ) : (
              <span className="px-3 py-1.5 bg-[#3EC6E0] text-[#2A1E4D] text-xs font-black rounded-full border-2 border-[#2A1E4D] shadow-[2px_2px_0px_#2A1E4D] inline-flex items-center justify-center gap-1.5 uppercase tracking-wider w-full">
                <span className="w-2 h-2 bg-[#6FCF6F] rounded-full border border-[#2A1E4D] shrink-0" />
                <span className="truncate">{isKhmer ? 'ទន្សាយ AI Tutor' : 'Tunsay AI Tutor'}</span>
              </span>
            )}
          </div>

          {/* Center Mascot Avatar with bounce/scale reaction */}
          <div className="flex flex-col items-center justify-center my-2 transition-all duration-300 transform w-full">
            <div className={`transition-all duration-300 ${
              sayoStatus === 'thinking' ? 'scale-105' : sayoStatus === 'celebrating' ? 'scale-110 animate-bounce' : 'scale-100 hover:scale-105'
            }`}>
              <TunsayAvatar 
                size="lg" 
                state={sayoStatus} 
                showBadge={false} 
              />
            </div>

            {/* Dynamic Status Speech Bubble Label */}
            <div className="mt-4 px-2 w-full max-w-[240px] bg-white rounded-2xl p-3 border-3 border-[#2A1E4D] shadow-[3px_3px_0px_#2A1E4D] relative">
              <div className="w-3 h-3 bg-white border-t-3 border-l-3 border-[#2A1E4D] rotate-45 absolute -top-2 left-1/2 -translate-x-1/2" />
              <p className="font-heading font-black text-xs sm:text-sm text-[#2A1E4D] leading-snug transition-all duration-300">
                {sayoStatus === 'thinking' && (
                  isKhmer ? thinkingTextsKhmer[thinkingTextIdx] : thinkingTextsEng[thinkingTextIdx]
                )}
                {sayoStatus === 'celebrating' && (
                  isKhmer ? celebratoryTextKhmer : celebratoryTextEng
                )}
                {sayoStatus === 'idle' && (
                  isKhmer ? idleTextKhmer : idleTextEng
                )}
              </p>
            </div>
          </div>
        </div>

        {/* Bottom Footer Label */}
        <div className="w-full pt-2.5 border-t-2 border-[#2A1E4D]/15 relative z-10 shrink-0">
          <p className="text-xs font-black text-[#6C4FF6] uppercase tracking-wider truncate">
            WEG Tutor 🐰
          </p>
        </div>
      </div>

      {/* Standalone Main App Frame (Purple header + blue chat area + input bar) */}
      <div className="flex-1 min-w-0 h-full flex flex-col bg-[#EAF2FF] rounded-2xl sm:rounded-3xl border-2 sm:border-3 border-[#2A1E4D] shadow-[4px_4px_0px_#2A1E4D] sm:shadow-[6px_6px_0px_#2A1E4D] overflow-hidden relative">
        {/* Tutor Fixed Top Navigation Bar */}
        <div className="shrink-0 z-20 px-3 py-2.5 sm:px-6 bg-[#6C4FF6] border-b-2 sm:border-b-3 border-[#2A1E4D] flex items-center justify-between gap-2 sm:gap-3 shadow-[0_3px_0px_#2A1E4D]">
          <div className="flex items-center space-x-2 sm:space-x-3 shrink-0">
            <div className="relative">
              <div className="w-9 h-9 sm:w-11 sm:h-11 bg-[#FFCB3D] rounded-xl sm:rounded-2xl flex items-center justify-center border-2 border-[#2A1E4D] shadow-[2px_2px_0px_#2A1E4D]">
                <TunsayAvatar size="sm" state={isSayoThinking ? 'thinking' : 'idle'} showBadge={false} />
              </div>
              {/* Mascot Online Status Dot */}
              <span className="absolute -bottom-1 -right-1 w-3 h-3 sm:w-3.5 sm:h-3.5 bg-[#6FCF6F] border-2 border-[#2A1E4D] rounded-full" title="Online" />
            </div>

            <div>
              <h3 className="font-black text-xs sm:text-base text-white flex items-center gap-1 font-heading leading-tight drop-shadow-[1px_1px_0px_#2A1E4D]">
                {isKhmer ? 'ទន្សាយ' : 'Tunsay AI'}
              </h3>
              <p className="text-[10px] sm:text-xs text-[#FFCB3D] font-black flex items-center gap-1 drop-shadow-[1px_1px_0px_#2A1E4D]">
                <GraduationCap className="w-3 h-3 sm:w-3.5 sm:h-3.5 text-[#FFCB3D]" />
                {isKhmer 
                  ? `ថ្នាក់ទី ${profile.grade}` 
                  : `Grade ${profile.grade}`}
              </p>
            </div>
          </div>

          <div className="flex items-center gap-1.5 sm:gap-2 shrink-0">
            {profile.mode === 'parent' && (
              <span className="hidden md:flex px-3 py-1 bg-[#FFCB3D] text-[#2A1E4D] rounded-full text-xs font-black border-2 border-[#2A1E4D] shadow-[1.5px_1.5px_0px_#2A1E4D] items-center gap-1">
                <Users className="w-3.5 h-3.5 text-[#2A1E4D]" />
                {isKhmer ? 'របៀបអាណាព្យាបាល' : 'Parent Help'}
              </span>
            )}

            {/* Single "New Chat" Icon Button in Top Right */}
            <button
              type="button"
              onClick={handleNewChat}
              className="w-8 h-8 sm:w-10 sm:h-10 bg-[#FFCB3D] text-[#2A1E4D] hover:bg-white rounded-xl sm:rounded-2xl flex items-center justify-center transition-all cursor-pointer border-2 border-[#2A1E4D] shadow-[1.5px_1.5px_0px_#2A1E4D] sm:shadow-[2px_2px_0px_#2A1E4D] active:translate-x-0.5 active:translate-y-0.5 shrink-0"
              title={isKhmer ? 'ចាប់ផ្តើមជជែកថ្មី' : 'New Chat'}
            >
              <Plus className="w-4 h-4 sm:w-5 sm:h-5 stroke-[3]" />
            </button>

            {onBackToHome && (
              <button
                type="button"
                onClick={onBackToHome}
                className="px-2.5 sm:px-3.5 py-1.5 bg-[#FFCB3D] text-[#2A1E4D] hover:bg-white rounded-xl sm:rounded-2xl text-xs sm:text-sm font-black transition-all flex items-center gap-1 cursor-pointer border-2 border-[#2A1E4D] shadow-[1.5px_1.5px_0px_#2A1E4D] sm:shadow-[2px_2px_0px_#2A1E4D] active:translate-x-0.5 active:translate-y-0.5 shrink-0"
                title={isKhmer ? 'ត្រឡប់ទៅទំព័រដើម' : 'Back to Home'}
              >
                <ArrowLeft className="w-3.5 h-3.5 sm:w-4 sm:h-4 stroke-[3]" />
                <span className="hidden min-[380px]:inline">{isKhmer ? 'ទំព័រដើម' : 'Home'}</span>
              </button>
            )}
          </div>
        </div>

        {/* Scrollable Conversation Area */}
        <div className="flex-1 overflow-y-auto overflow-x-hidden p-4 sm:p-6 space-y-5">
          {/* Step Trail if active problem present */}
          {activeProblem && (
            <div className="space-y-4">
              <StepTrail
                currentStep={currentStepIndex + 1}
                totalSteps={activeProblem.steps.length}
                language={profile.language}
                onSelectStep={(stepIdx) => setCurrentStepIndex(stepIdx)}
              />

              {currentStep && (
                <StepCard
                  step={currentStep}
                  language={profile.language}
                  onAnswerSubmit={handleStepAnswer}
                  onOpenHints={() => setIsHintOpen(true)}
                  onOpenExplainDifferently={() => setIsExplainOpen(true)}
                  onVoiceInputRequested={onOpenVoiceModal}
                />
              )}
            </div>
          )}

          {/* Message Log */}
          {messages.map((msg) => {
            const isUser = msg.sender === 'user';
            // Determine single-language text to render
            let displayText = '';
            if (isUser) {
              displayText = msg.textEng || msg.textKhmer || '';
            } else {
              displayText = isKhmer ? (msg.textKhmer || msg.textEng || '') : (msg.textEng || msg.textKhmer || '');
            }

            return (
              <div
                key={msg.id}
                className={`flex items-start gap-2.5 sm:gap-3 w-full ${isUser ? 'flex-row-reverse' : 'flex-row'} animate-fadeIn`}
              >
                {!isUser ? (
                  <div className="w-9 h-9 sm:w-11 sm:h-11 bg-[#FFCB3D] rounded-xl sm:rounded-2xl shrink-0 border-2 border-[#2A1E4D] shadow-[1.5px_1.5px_0px_#2A1E4D] sm:shadow-[2px_2px_0px_#2A1E4D] flex items-center justify-center p-0.5">
                    <TunsayAvatar size="sm" state={msg.isSafetyRefusal ? 'encouraging' : 'explaining'} showBadge={false} />
                  </div>
                ) : (
                  <div className="w-9 h-9 sm:w-11 sm:h-11 rounded-xl sm:rounded-2xl bg-[#3EC6E0] text-[#2A1E4D] border-2 border-[#2A1E4D] shadow-[1.5px_1.5px_0px_#2A1E4D] sm:shadow-[2px_2px_0px_#2A1E4D] font-black flex items-center justify-center shrink-0">
                    <User className="w-5 h-5 sm:w-6 sm:h-6" />
                  </div>
                )}

                <div
                  className={`max-w-[85%] sm:max-w-[80%] min-w-0 p-3.5 sm:p-5 rounded-2xl sm:rounded-3xl border-2.5 sm:border-3 border-[#2A1E4D] text-sm leading-relaxed break-words overflow-hidden ${
                    isUser
                      ? 'bg-[#6C4FF6] text-white shadow-[2.5px_2.5px_0px_#2A1E4D] sm:shadow-[3px_3px_0px_#2A1E4D] speech-tail-right'
                      : msg.isSafetyRefusal
                      ? 'bg-[#FF6FA3] text-white shadow-[2.5px_2.5px_0px_#2A1E4D] sm:shadow-[3px_3px_0px_#2A1E4D] speech-tail-left'
                      : msg.isParentHelp
                      ? 'bg-[#FFCB3D] text-[#2A1E4D] shadow-[2.5px_2.5px_0px_#2A1E4D] sm:shadow-[3px_3px_0px_#2A1E4D] speech-tail-left'
                      : 'bg-white text-[#2A1E4D] shadow-[2.5px_2.5px_0px_#2A1E4D] sm:shadow-[3px_3px_0px_#2A1E4D] speech-tail-left'
                  }`}
                >
                  <p className="font-black text-xs sm:text-base leading-relaxed break-words whitespace-pre-wrap">
                    {displayText}
                  </p>

                  {msg.suggestedNext && (
                    <div className="mt-3 pt-2 border-t-2 border-[#2A1E4D]/20">
                      <button
                        type="button"
                        onClick={() => {
                          const found = MOCK_PROBLEMS.find((p) => p.id === msg.suggestedNext);
                          if (found) handleSelectTopicCard(found);
                        }}
                        className="px-3.5 py-1.5 bg-[#FFCB3D] hover:bg-[#6FCF6F] text-[#2A1E4D] font-black text-xs rounded-xl border-2 border-[#2A1E4D] shadow-[2px_2px_0px_#2A1E4D] inline-flex items-center gap-1.5 transition-all cursor-pointer hover:-translate-y-0.5"
                      >
                        <span>🎯 {isKhmer ? 'សាកល្បងលំហាត់បន្ទាប់ដែលបានណែនាំ' : 'Try Recommended Next Problem'}</span>
                      </button>
                    </div>
                  )}

                  <span className={`text-[10px] mt-2 block text-right font-black opacity-80`}>
                    {msg.timestamp}
                  </span>
                </div>
              </div>
            );
          })}

          {/* Fresh Start Practice Topic Cards (Icon-Led Row when conversation is fresh) */}
          {!activeProblem && messages.length <= 1 && (
            <div className="space-y-4 pt-1 pl-2 sm:pl-14 animate-fadeIn">
              {/* Action Sticker Pills (Scan / Voice) FIRST */}
              <div className="flex flex-wrap gap-3">
                <button
                  type="button"
                  onClick={onOpenScanner}
                  className="px-4 py-2.5 bg-[#6FCF6F] text-[#2A1E4D] hover:bg-[#FFCB3D] rounded-2xl text-xs sm:text-sm font-black border-3 border-[#2A1E4D] shadow-[3px_3px_0px_#2A1E4D] hover:-translate-y-0.5 active:translate-y-0.5 active:shadow-[1px_1px_0px_#2A1E4D] flex items-center gap-2 transition-all cursor-pointer"
                >
                  <Camera className="w-4 h-4 stroke-[2.5]" />
                  <span>{isKhmer ? 'ស្កែនរូបថតលំហាត់' : 'Scan Homework Photo'}</span>
                </button>

                <button
                  type="button"
                  onClick={onOpenVoiceModal}
                  className="px-4 py-2.5 bg-[#3EC6E0] text-[#2A1E4D] hover:bg-[#FFCB3D] rounded-2xl text-xs sm:text-sm font-black border-3 border-[#2A1E4D] shadow-[3px_3px_0px_#2A1E4D] hover:-translate-y-0.5 active:translate-y-0.5 active:shadow-[1px_1px_0px_#2A1E4D] flex items-center gap-2 transition-all cursor-pointer"
                >
                  <Mic className="w-4 h-4 stroke-[2.5]" />
                  <span>{isKhmer ? 'និយាយសំណួរតាមសំឡេង' : 'Ask by Voice'}</span>
                </button>
              </div>

              {/* Practice Topic Cards SECOND - Single Row Endless Slideshow with < and > arrows */}
              <div className="space-y-2 pt-1 overflow-hidden group/chat-marquee">
                <div className="flex items-center justify-between gap-2">
                  <p className="text-xs font-black text-[#2A1E4D] uppercase tracking-wider flex items-center gap-1.5 font-heading">
                    <BookOpen className="w-4 h-4 text-[#6C4FF6]" />
                    <span>{isKhmer ? 'ប្រវត្តិលំហាត់រៀនជាមួយទន្សាយ' : 'Homework History with Tunsay'}</span>
                  </p>
                  <div className="flex items-center gap-1.5">
                    <button
                      type="button"
                      onClick={handleChatScrollLeft}
                      aria-label="Previous topic"
                      className="p-1 bg-white text-[#2A1E4D] hover:bg-[#3EC6E0] rounded-lg border-2 border-[#2A1E4D] shadow-[1.5px_1.5px_0px_#2A1E4D] hover:-translate-y-0.5 active:translate-y-0.5 transition-all cursor-pointer"
                    >
                      <ChevronLeft className="w-3.5 h-3.5 stroke-[3]" />
                    </button>
                    <button
                      type="button"
                      onClick={handleChatScrollRight}
                      aria-label="Next topic"
                      className="p-1 bg-white text-[#2A1E4D] hover:bg-[#3EC6E0] rounded-lg border-2 border-[#2A1E4D] shadow-[1.5px_1.5px_0px_#2A1E4D] hover:-translate-y-0.5 active:translate-y-0.5 transition-all cursor-pointer"
                    >
                      <ChevronRight className="w-3.5 h-3.5 stroke-[3]" />
                    </button>
                  </div>
                </div>

                <div className="w-full relative py-1">
                  <button
                    type="button"
                    onClick={handleChatScrollLeft}
                    className="absolute left-0 top-1/2 -translate-y-1/2 z-20 p-1.5 bg-white text-[#2A1E4D] hover:bg-[#FFCB3D] rounded-full border-2 border-[#2A1E4D] shadow-[2px_2px_0px_#2A1E4D] hover:scale-110 active:scale-95 transition-all cursor-pointer opacity-90 sm:opacity-0 group-hover/chat-marquee:opacity-100"
                  >
                    <ChevronLeft className="w-4 h-4 stroke-[3]" />
                  </button>
                  <button
                    type="button"
                    onClick={handleChatScrollRight}
                    className="absolute right-0 top-1/2 -translate-y-1/2 z-20 p-1.5 bg-white text-[#2A1E4D] hover:bg-[#FFCB3D] rounded-full border-2 border-[#2A1E4D] shadow-[2px_2px_0px_#2A1E4D] hover:scale-110 active:scale-95 transition-all cursor-pointer opacity-90 sm:opacity-0 group-hover/chat-marquee:opacity-100"
                  >
                    <ChevronRight className="w-4 h-4 stroke-[3]" />
                  </button>

                  <div
                    ref={chatMarqueeRef}
                    onMouseEnter={() => setIsChatMarqueeHovered(true)}
                    onMouseLeave={() => setIsChatMarqueeHovered(false)}
                    className="overflow-x-auto scrollbar-none scroll-smooth flex gap-3 items-center py-1 px-1"
                  >
                    {[...MOCK_PROBLEMS, ...MOCK_PROBLEMS, ...MOCK_PROBLEMS].map((prob, idx) => {
                      const isMath = prob.subject === 'math';
                      const isScience = prob.subject === 'science';
                      return (
                        <button
                          key={`chat-prob-${prob.id}-${idx}`}
                          type="button"
                          onClick={() => handleSelectTopicCard(prob)}
                          className={`flex items-center gap-3 p-3 rounded-2xl border-3 border-[#2A1E4D] shadow-[3px_3px_0px_#2A1E4D] hover:-translate-y-0.5 active:translate-y-0.5 active:shadow-[1px_1px_0px_#2A1E4D] transition-all cursor-pointer text-left shrink-0 w-[230px] sm:w-[260px] ${
                            isMath ? 'bg-[#3EC6E0] text-[#2A1E4D]' : isScience ? 'bg-[#6FCF6F] text-[#2A1E4D]' : 'bg-[#FFCB3D] text-[#2A1E4D]'
                          }`}
                        >
                          <div className="w-9 h-9 bg-white rounded-xl border-2 border-[#2A1E4D] flex items-center justify-center shrink-0 shadow-[1.5px_1.5px_0px_#2A1E4D]">
                            {isMath ? <Calculator className="w-4 h-4 text-[#6C4FF6]" /> : isScience ? <Atom className="w-4 h-4 text-[#6C4FF6]" /> : <Languages className="w-4 h-4 text-[#6C4FF6]" />}
                          </div>
                          <div className="min-w-0 flex-1">
                            <h4 className="font-black text-xs sm:text-sm truncate font-heading leading-tight">
                              {isKhmer ? prob.titleKhmer : prob.titleEng}
                            </h4>
                            <span className="text-[10px] font-black opacity-85 block mt-0.5">
                              {isKhmer ? `${prob.steps.length} ជំហាន` : `${prob.steps.length} Steps`}
                            </span>
                          </div>
                        </button>
                      );
                    })}
                  </div>
                </div>
              </div>
            </div>
          )}

          <div ref={chatEndRef} />
        </div>

        {/* Bottom Chat Input Bar */}
        <div className="px-4 sm:px-6 py-3 sm:py-4 bg-white border-t-3 border-[#2A1E4D] shrink-0">
          <form
            onSubmit={(e) => {
              e.preventDefault();
              handleSendMessage();
            }}
            className="w-full flex items-center gap-2.5"
          >
            <button
              type="button"
              onClick={onOpenScanner}
              className="w-12 h-12 sm:w-14 sm:h-14 bg-[#6FCF6F] text-[#2A1E4D] rounded-2xl border-3 border-[#2A1E4D] shadow-[3px_3px_0px_#2A1E4D] flex items-center justify-center hover:-translate-y-0.5 active:translate-y-0.5 active:shadow-[1px_1px_0px_#2A1E4D] transition-all cursor-pointer shrink-0"
              title={isKhmer ? 'ស្កែនរូបថតលំហាត់' : 'Scan Homework Photo'}
            >
              <Camera className="w-6 h-6 stroke-[2.5]" />
            </button>

            <div className="flex-1 bg-[#EAF2FF] rounded-2xl border-3 border-[#2A1E4D] shadow-[3px_3px_0px_#2A1E4D] px-4 flex items-center">
              <input
                type="text"
                value={inputQuery}
                onChange={(e) => setInputQuery(e.target.value)}
                placeholder={
                  profile.mode === 'parent'
                    ? (isKhmer ? 'សួរទន្សាយអំពីវិធីពន្យល់លំហាត់ទៅកាន់កូន...' : 'Ask Tunsay how to explain this to your child...')
                    : (isKhmer ? 'វាយបញ្ចូលសំណួររបស់អ្នកនៅទីនេះ...' : 'Type your question here...')
                }
                className="flex-1 bg-transparent border-none focus:outline-none focus:ring-0 text-sm sm:text-base py-3 font-bold text-[#2A1E4D] placeholder:text-[#2A1E4D]/50"
              />

              <button
                type="button"
                onClick={onOpenVoiceModal}
                className="w-9 h-9 bg-[#3EC6E0] rounded-xl border-2 border-[#2A1E4D] flex items-center justify-center text-[#2A1E4D] hover:bg-[#FFCB3D] transition-colors cursor-pointer shrink-0 ml-2"
                title={isKhmer ? 'និយាយសារ' : 'Voice Input'}
              >
                <Mic className="w-4 h-4 stroke-[2.5]" />
              </button>
            </div>

            <button
              type="submit"
              disabled={!inputQuery.trim()}
              className="w-12 h-12 sm:w-14 sm:h-14 bg-[#6C4FF6] disabled:bg-gray-200 disabled:border-gray-400 text-white rounded-2xl border-3 border-[#2A1E4D] shadow-[3px_3px_0px_#2A1E4D] font-black hover:-translate-y-0.5 active:translate-y-0.5 active:shadow-[1px_1px_0px_#2A1E4D] transition-all flex items-center justify-center cursor-pointer shrink-0"
            >
              <Send className="w-5 h-5 stroke-[2.5]" />
            </button>
          </form>
        </div>
      </div>

      {/* Sheets Modals */}
      {currentStep && (
        <>
          <HintSheet
            step={currentStep}
            problemId={activeProblem?.id}
            isOpen={isHintOpen}
            language={profile.language}
            onClose={() => setIsHintOpen(false)}
            onRequestAIHint={async (hintLevel) => {
              if (!activeProblem?.id || !currentStep?.id) return { hintKhmer: '', hintEng: '' };
              return await fetchAIHint(activeProblem.id, currentStep.id, hintLevel, profile.language);
            }}
            onDeductStars={async (hintLevel) => {
              return await deductHintStars(hintLevel);
            }}
          />

          <ExplanationCard
            step={currentStep}
            isOpen={isExplainOpen}
            language={profile.language}
            onClose={() => setIsExplainOpen(false)}
          />
        </>
      )}
    </div>
  );
};

