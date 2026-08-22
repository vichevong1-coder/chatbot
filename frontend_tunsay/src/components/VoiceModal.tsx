import React, { useState, useEffect, useRef } from 'react';
import { Mic, X, Volume2 } from 'lucide-react';
import { TunsayAvatar } from './TunsayAvatar';
import { Language } from '../types';
import { sendVoiceTurn } from '../services/geminiService';

interface VoiceModalProps {
  isOpen: boolean;
  language?: Language;
  onClose: () => void;
  onTranscriptSubmitted?: (text: string) => void;
}

export const VoiceModal: React.FC<VoiceModalProps> = ({
  isOpen,
  language = 'km',
  onClose,
  onTranscriptSubmitted
}) => {
  const isKhmer = language === 'km';
  const [isListening, setIsListening] = useState(false);
  const [transcript, setTranscript] = useState('');
  const [tunsaySpeech, setTunsaySpeech] = useState('');
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);

  useEffect(() => {
    if (isOpen) {
      setTunsaySpeech(
        isKhmer 
          ? 'សួស្តី! ខ្ញុំគឺទន្សាយ។ តើមានអ្វីឲ្យខ្ញុំជួយអ្នកទេ?' 
          : 'Hi! I am Tunsay. How can I help you?'
      );
    }
  }, [isOpen, isKhmer]);

  if (!isOpen) return null;

  const handleStartListening = async () => {
    setIsListening(true);
    setTranscript('');
    setTunsaySpeech('');
    audioChunksRef.current = [];

    try {
      if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        const mediaRecorder = new MediaRecorder(stream);
        mediaRecorderRef.current = mediaRecorder;

        mediaRecorder.ondataavailable = (event) => {
          if (event.data.size > 0) {
            audioChunksRef.current.push(event.data);
          }
        };

        mediaRecorder.onstop = async () => {
          stream.getTracks().forEach((track) => track.stop());
          const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
          if (audioBlob.size > 0) {
            const res = await sendVoiceTurn(audioBlob, 'student', undefined, language);
            const speechText = isKhmer ? (res.textKhmer || res.textEng) : (res.textEng || res.textKhmer);
            setTunsaySpeech(speechText || (isKhmer ? 'ខ្ញុំបានស្តាប់ឮហើយ! តោះគិតទាំងអស់គ្នា 🐰' : "I heard you! Let's think together 🐰"));
          }
        };

        mediaRecorder.start();
        return;
      }
    } catch {
      /* Fallback to simulated mic */
    }

    // Simulated voice fallback
    setTimeout(() => {
      setTranscript(isKhmer ? 'ខ្ញុំមិនយល់សំណួរនេះទេ...' : 'I do not understand this question...');
    }, 1200);

    setTimeout(() => {
      setIsListening(false);
      setTunsaySpeech(
        isKhmer 
          ? 'មិនអីទេ! តោះយើងពិនិត្យសំណួរនេះជាមួយគ្នាណា' 
          : "No problem! Let's look at it together."
      );
    }, 3200);
  };

  const handleStopListening = () => {
    setIsListening(false);
    if (mediaRecorderRef.current && mediaRecorderRef.current.state === 'recording') {
      mediaRecorderRef.current.stop();
    }
  };

  const handleSendVoiceQuery = () => {
    if (transcript && onTranscriptSubmitted) {
      onTranscriptSubmitted(transcript);
      onClose();
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-[#2A1E4D]/60 backdrop-blur-xs p-4 animate-fadeIn">
      <div 
        className="w-full max-w-md bg-white rounded-3xl border-3 border-[#2A1E4D] shadow-[6px_6px_0px_#2A1E4D] p-6 relative overflow-hidden flex flex-col items-center text-center space-y-6 text-[#2A1E4D]"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Close Button */}
        <button
          type="button"
          onClick={onClose}
          className="absolute top-4 right-4 p-2 rounded-2xl bg-[#EAF2FF] border-2 border-[#2A1E4D] text-[#2A1E4D] hover:bg-[#FF6FA3] hover:text-white transition-colors cursor-pointer"
        >
          <X className="w-5 h-5 stroke-[3]" />
        </button>

        <span className="px-3.5 py-1 bg-[#3EC6E0] text-[#2A1E4D] text-xs font-black rounded-full border-2 border-[#2A1E4D] shadow-[2px_2px_0px_#2A1E4D] flex items-center gap-1.5">
          <Volume2 className="w-4 h-4 stroke-[2.5]" /> {isKhmer ? 'របៀបនិយាយផ្ទាល់' : 'Voice Chat Mode'}
        </span>

        {/* Big Tunsay Avatar */}
        <div className="relative my-2">
          {/* Animated Waveform Ring if listening */}
          {isListening && (
            <div className="absolute inset-0 -m-6 rounded-full bg-[#3EC6E0]/40 animate-ping z-0" />
          )}
          <TunsayAvatar 
            size="xl" 
            state={isListening ? 'listening' : tunsaySpeech ? 'explaining' : 'idle'} 
            showBadge={false} 
            className="relative z-10"
          />
        </div>

        {/* Tunsay Response Speech */}
        {tunsaySpeech && (
          <div className="p-4 bg-[#EAF2FF] rounded-2xl border-3 border-[#2A1E4D] shadow-[3px_3px_0px_#2A1E4D] text-sm sm:text-base font-black text-[#2A1E4D] animate-fadeIn">
            {tunsaySpeech}
          </div>
        )}

        {/* Transcribed Text Display */}
        {transcript && (
          <div className="p-3 bg-[#FFCB3D] rounded-xl border-2 border-[#2A1E4D] text-xs sm:text-sm text-[#2A1E4D] font-black animate-fadeIn">
            " {transcript} "
          </div>
        )}

        {/* Big Mic Toggle Button */}
        <div className="space-y-3 w-full">
          {!isListening ? (
            <button
              type="button"
              onClick={handleStartListening}
              className="w-full py-4 bg-[#3EC6E0] hover:bg-[#FFCB3D] text-[#2A1E4D] font-black text-base rounded-2xl border-3 border-[#2A1E4D] shadow-[4px_4px_0px_#2A1E4D] flex items-center justify-center gap-2 transition-all cursor-pointer hover:-translate-y-0.5 active:translate-y-0.5"
            >
              <Mic className="w-6 h-6 stroke-[2.5]" />
              {isKhmer ? 'ចុចដើម្បីនិយាយ' : 'Tap to talk'}
            </button>
          ) : (
            <button
              type="button"
              onClick={handleStopListening}
              className="w-full py-4 bg-[#FF6FA3] text-white font-black text-base rounded-2xl border-3 border-[#2A1E4D] shadow-[4px_4px_0px_#2A1E4D] flex items-center justify-center gap-2 animate-pulse cursor-pointer"
            >
              <span className="w-3 h-3 rounded-full bg-white animate-ping" />
              {isKhmer ? 'កំពុងស្តាប់...' : 'Listening...'}
            </button>
          )}

          {transcript && !isListening && (
            <button
              type="button"
              onClick={handleSendVoiceQuery}
              className="w-full py-3.5 bg-[#6FCF6F] hover:bg-[#FFCB3D] text-[#2A1E4D] font-black text-sm rounded-2xl border-3 border-[#2A1E4D] shadow-[3px_3px_0px_#2A1E4D] transition-all cursor-pointer hover:-translate-y-0.5"
            >
              {isKhmer ? 'ផ្ញើសំណួរនេះទៅទន្សាយ' : 'Send to Tunsay'}
            </button>
          )}
        </div>
      </div>
    </div>
  );
};
