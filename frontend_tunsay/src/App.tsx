import React, { useState } from 'react';
import { UserProfile, HomeworkProblem, Grade, Subject, Language, ChatMessage } from './types';
import { Header } from './components/Header';
import { HomeView } from './components/HomeView';
import { ChatView } from './components/ChatView';
import { ProfileView } from './components/ProfileView';
import { HomeworkScanner } from './components/HomeworkScanner';
import { VoiceModal } from './components/VoiceModal';
import { CelebrationOverlay } from './components/CelebrationOverlay';
import { LandingView } from './components/LandingView';
import { LoginView } from './components/LoginView';
import { getDisplayName } from './utils/language';
import { signOut } from './api/client';

export default function App() {
  // Page mode: 'landing' (Public Welcome) | 'login' (Sign-in Page) | 'app' (In-app student experience)
  const [pageMode, setPageMode] = useState<'landing' | 'login' | 'app'>('landing');

  const [profile, setProfile] = useState<UserProfile>({
    name: 'សុជា (Sochea)',
    grade: 4,
    subject: 'math',
    mode: 'student',
    language: 'km',
    completedProblemsCount: 3,
    starsEarned: 12
  });

  const [activeTab, setActiveTab] = useState<'home' | 'chat' | 'profile'>('home');
  const [activeProblem, setActiveProblem] = useState<HomeworkProblem | undefined>(undefined);
  const [initialChatQuery, setInitialChatQuery] = useState<string | undefined>(undefined);

  // Global Chat Messages Transcript
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([
    {
      id: 'init-msg',
      sender: 'sayo',
      textKhmer: `សួស្តី សុជា! ខ្ញុំគឺទន្សាយ (Tunsay) គ្រូបង្រៀន AI។ តើអ្នកមានលំហាត់អ្វីចង់ឱ្យខ្ញុំជួយទេ? អ្នកអាចថតរូបស្កែនលំហាត់ ប្រើសំឡេង ឬវាយបញ្ចូលសំណួរនៅខាងក្រោម!`,
      textEng: `Hi Sochea! I am Tunsay, your AI Tutor. What homework would you like help with? You can scan a photo, use voice, or type your question below!`,
      timestamp: 'Just now'
    }
  ]);

  // Modal overlays
  const [isScannerOpen, setIsScannerOpen] = useState(false);
  const [isVoiceModalOpen, setIsVoiceModalOpen] = useState(false);
  const [isCelebrationOpen, setIsCelebrationOpen] = useState(false);

  const handleUpdateProfile = (updated: Partial<UserProfile>) => {
    setProfile((prev) => ({ ...prev, ...updated }));
  };

  const handleStartChatWithProblem = (problem?: HomeworkProblem, initialQuery?: string) => {
    setActiveProblem(problem);
    setInitialChatQuery(initialQuery);
    setActiveTab('chat');
  };

  const handleHomeworkScanned = (problem: HomeworkProblem) => {
    setActiveProblem(problem);
    setInitialChatQuery(undefined);
    setIsScannerOpen(false);
    setActiveTab('chat');
  };

  const handleProblemCompleted = () => {
    setProfile((prev) => ({
      ...prev,
      starsEarned: prev.starsEarned + 5,
      completedProblemsCount: prev.completedProblemsCount + 1
    }));
    setIsCelebrationOpen(true);
  };

  // 1. PUBLIC MARKETING LANDING PAGE
  if (pageMode === 'landing') {
    return (
      <LandingView
        language={profile.language}
        onSelectLanguage={(language: Language) => handleUpdateProfile({ language })}
        onNavigateToLogin={() => setPageMode('login')}
      />
    );
  }

  // 2. LOGIN / SIGN-IN PAGE
  if (pageMode === 'login') {
    return (
      <LoginView
        language={profile.language}
        onSelectLanguage={(language: Language) => handleUpdateProfile({ language })}
        onLoginSuccess={(updatedProfile) => {
          handleUpdateProfile(updatedProfile);
          setPageMode('app');
          setActiveTab('home');
        }}
        onBackToLanding={() => setPageMode('landing')}
      />
    );
  }

  // 3. IN-APP STUDENT EXPERIENCE
  return (
    <div className={`bg-white text-[#2A1E4D] flex flex-col font-sans w-full max-w-full overflow-x-hidden ${activeTab === 'chat' ? 'h-screen h-[100dvh] overflow-hidden' : 'min-h-screen'}`}>
      {/* Top Header & Sticky Pill Nav Bar */}
      <Header
        profile={profile}
        activeTab={activeTab}
        onSelectTab={setActiveTab}
        onSelectLanguage={(language: Language) => handleUpdateProfile({ language })}
      />

      {/* Main Responsive Body Container */}
      <main className={`flex-1 min-h-0 w-full mx-auto ${activeTab === 'chat' ? 'w-full px-2.5 sm:px-5 pt-5 sm:pt-7 pb-2.5 sm:pb-4 h-full overflow-hidden flex flex-col' : 'max-w-7xl p-4 sm:p-6 lg:p-8'}`}>
        {activeTab === 'home' && (
          <HomeView
            profile={profile}
            onStartVoiceChat={() => setIsVoiceModalOpen(true)}
            onStartScan={() => setIsScannerOpen(true)}
            onStartChat={handleStartChatWithProblem}
            onSelectGrade={(grade: Grade) => handleUpdateProfile({ grade })}
          />
        )}

        {activeTab === 'chat' && (
          <ChatView
            profile={profile}
            initialProblem={activeProblem}
            initialQuery={initialChatQuery}
            onClearInitialQuery={() => setInitialChatQuery(undefined)}
            chatMessages={chatMessages}
            onUpdateMessages={setChatMessages}
            onOpenVoiceModal={() => setIsVoiceModalOpen(true)}
            onOpenScanner={() => setIsScannerOpen(true)}
            onProblemCompleted={handleProblemCompleted}
            onBackToHome={() => setActiveTab('home')}
          />
        )}

        {activeTab === 'profile' && (
          <ProfileView
            profile={profile}
            chatMessages={chatMessages}
            onClearChatMessages={() => {
              setChatMessages([
                {
                  id: Date.now().toString(),
                  sender: 'sayo',
                  textKhmer: `សួស្តី ${getDisplayName(profile.name, true)}! ខ្ញុំគឺទន្សាយ គ្រូបង្រៀន AI។ តើអ្នកមានលំហាត់អ្វីចង់ឱ្យខ្ញុំជួយទេ?`,
                  textEng: `Hi ${getDisplayName(profile.name, false)}! I am Tunsay, your AI Tutor. What homework would you like help with?`,
                  timestamp: 'Just now'
                }
              ]);
            }}
            onUpdateProfile={handleUpdateProfile}
            onSignOut={() => {
              signOut();
              setPageMode('landing');
            }}
          />
        )}
      </main>

      {/* Modals & Overlays */}
      {isScannerOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-[#2A1E4D]/60 backdrop-blur-sm p-4 animate-fadeIn">
          <HomeworkScanner
            language={profile.language}
            onHomeworkConfirmed={handleHomeworkScanned}
            onCancel={() => setIsScannerOpen(false)}
          />
        </div>
      )}

      <VoiceModal
        isOpen={isVoiceModalOpen}
        language={profile.language}
        onClose={() => setIsVoiceModalOpen(false)}
        onTranscriptSubmitted={() => {
          handleStartChatWithProblem();
        }}
      />

      <CelebrationOverlay
        isOpen={isCelebrationOpen}
        language={profile.language}
        onRestart={() => setIsCelebrationOpen(false)}
        onContinue={() => {
          setIsCelebrationOpen(false);
          setActiveTab('home');
        }}
      />
    </div>
  );
}

