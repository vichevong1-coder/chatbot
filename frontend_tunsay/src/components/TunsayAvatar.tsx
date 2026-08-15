import React, { useState } from 'react';
import { SayoState } from '../types';

interface SayoAvatarProps {
  state?: SayoState;
  size?: 'sm' | 'md' | 'lg' | 'xl';
  showBadge?: boolean;
  className?: string;
  onClick?: () => void;
  speechBubbleText?: string;
}

export const TunsayAvatar: React.FC<SayoAvatarProps> = ({
  state = 'idle',
  size = 'md',
  showBadge = true,
  className = '',
  onClick,
  speechBubbleText
}) => {
  const [isWiggling, setIsWiggling] = useState(false);

  // Dynamic responsive size dimensions
  const dimensions = {
    sm: 'w-8 h-8 sm:w-10 sm:h-10',
    md: 'w-12 h-12 sm:w-16 sm:h-16',
    lg: 'w-16 h-16 sm:w-24 sm:h-24 lg:w-28 lg:h-28',
    xl: 'w-20 h-20 sm:w-28 sm:h-28 lg:w-36 lg:h-36',
  }[size];

  const handleAvatarClick = () => {
    setIsWiggling(true);
    setTimeout(() => setIsWiggling(false), 900);
    if (onClick) onClick();
  };

  // Dynamic ear classes based on SayoState
  const getLeftEarStyle = () => {
    if (isWiggling || state === 'celebrating') return 'animate-ear-wiggle origin-bottom-right';
    if (state === 'listening') return 'translate-y-[-3px] rotate-[-2deg] transition-all duration-300';
    if (state === 'thinking') return 'rotate-[10deg] translate-x-[2px] transition-all duration-300';
    if (state === 'explaining') return 'animate-ear-perk origin-bottom-right';
    if (state === 'encouraging') return 'rotate-[-6deg] transition-all duration-300';
    if (state === 'sleepy') return 'rotate-[-12deg] translate-y-[2px] transition-all duration-300';
    return 'animate-ear-perk origin-bottom-right';
  };

  const getRightEarStyle = () => {
    if (isWiggling || state === 'celebrating') return 'animate-ear-wiggle origin-bottom-left';
    if (state === 'listening') return 'translate-y-[-3px] rotate-[2deg] transition-all duration-300';
    if (state === 'thinking') return 'rotate-[14deg] translate-x-[4px] transition-all duration-300';
    if (state === 'explaining') return 'animate-ear-perk origin-bottom-left';
    if (state === 'encouraging') return 'rotate-[6deg] transition-all duration-300';
    if (state === 'sleepy') return 'rotate-[12deg] translate-y-[2px] transition-all duration-300';
    return 'animate-ear-perk origin-bottom-left';
  };

  // Eyes rendering depending on state
  const renderEyes = () => {
    if (state === 'celebrating' || state === 'encouraging') {
      // Happy curved ^ ^ eyes
      return (
        <g>
          <path d="M 38 48 Q 43 42 48 48" fill="none" stroke="#2E2A26" strokeWidth="3.5" strokeLinecap="round" />
          <path d="M 52 48 Q 57 42 62 48" fill="none" stroke="#2E2A26" strokeWidth="3.5" strokeLinecap="round" />
        </g>
      );
    }
    if (state === 'thinking') {
      // Looking upward right
      return (
        <g>
          <circle cx="43" cy="46" r="4.5" fill="#2E2A26" />
          <circle cx="57" cy="46" r="4.5" fill="#2E2A26" />
          <circle cx="45" cy="44" r="1.8" fill="#FFFFFF" />
          <circle cx="59" cy="44" r="1.8" fill="#FFFFFF" />
        </g>
      );
    }
    if (state === 'listening') {
      // Big attentive wide eyes
      return (
        <g>
          <circle cx="43" cy="47" r="5.5" fill="#2E2A26" />
          <circle cx="57" cy="47" r="5.5" fill="#2E2A26" />
          <circle cx="41.5" cy="45" r="2.2" fill="#FFFFFF" />
          <circle cx="55.5" cy="45" r="2.2" fill="#FFFFFF" />
        </g>
      );
    }
    if (state === 'sleepy') {
      // Droopy eyes
      return (
        <g>
          <line x1="38" y1="48" x2="48" y2="48" stroke="#2E2A26" strokeWidth="3" strokeLinecap="round" />
          <line x1="52" y1="48" x2="62" y2="48" stroke="#2E2A26" strokeWidth="3" strokeLinecap="round" />
        </g>
      );
    }
    // Normal friendly eyes
    return (
      <g>
        <circle cx="43" cy="47" r="5" fill="#2E2A26" />
        <circle cx="57" cy="47" r="5" fill="#2E2A26" />
        <circle cx="41" cy="45" r="1.8" fill="#FFFFFF" />
        <circle cx="55" cy="45" r="1.8" fill="#FFFFFF" />
      </g>
    );
  };

  // Mouth rendering
  const renderMouth = () => {
    if (state === 'explaining' || state === 'celebrating') {
      // Open happy mouth
      return (
        <path d="M 46 56 Q 50 62 54 56 Z" fill="#E88B7D" stroke="#2E2A26" strokeWidth="1.5" />
      );
    }
    if (state === 'thinking') {
      // Slight cute small 'o' mouth
      return (
        <circle cx="50" cy="56" r="2" fill="#2E2A26" />
      );
    }
    // Friendly 'w' rabbit smile
    return (
      <path d="M 46 55 Q 48 58 50 55 Q 52 58 54 55" fill="none" stroke="#2E2A26" strokeWidth="2.5" strokeLinecap="round" />
    );
  };

  return (
    <div className={`relative inline-flex flex-col items-center select-none ${className}`}>
      {/* Speech bubble if text provided */}
      {speechBubbleText && (
        <div className="absolute -top-12 bg-white text-[#2E2A26] px-3 py-1.5 rounded-2xl shadow-md border-2 border-[#4C9A6A]/20 text-xs sm:text-sm font-semibold whitespace-nowrap animate-bounce z-20">
          {speechBubbleText}
          <div className="absolute -bottom-2 left-1/2 -translate-x-1/2 w-0 h-0 border-l-[6px] border-l-transparent border-r-[6px] border-r-transparent border-t-[8px] border-t-white" />
        </div>
      )}

      {/* Tunsay Main Vector Character */}
      <div 
        onClick={handleAvatarClick}
        className={`${dimensions} cursor-pointer relative transition-transform hover:scale-105 active:scale-95 duration-200 ${
          state === 'thinking' ? 'animate-tunsay-run' : state === 'celebrating' ? 'animate-hop' : 'animate-breathe'
        }`}
        title="Tap Tunsay to wiggle ears! 🐰"
      >
        <svg viewBox="0 0 100 100" className="w-full h-full drop-shadow-sm overflow-visible">
          {/* Subtle halo/shadow under Tunsay */}
          <ellipse cx="50" cy="92" rx="32" ry="7" fill="#2E2A26" opacity="0.08" />

          {/* Running dust puffs and motion lines if thinking/running */}
          {state === 'thinking' && (
            <g className="animate-dust-puff">
              <circle cx="12" cy="84" r="5" fill="#D7CAFF" stroke="#2A1E4D" strokeWidth="1.5" />
              <circle cx="20" cy="88" r="4" fill="#D7CAFF" stroke="#2A1E4D" strokeWidth="1.5" />
              <circle cx="8" cy="88" r="3" fill="#D7CAFF" stroke="#2A1E4D" strokeWidth="1.5" />
              <line x1="6" y1="46" x2="0" y2="46" stroke="#2A1E4D" strokeWidth="2.5" strokeLinecap="round" />
              <line x1="10" y1="36" x2="2" y2="36" stroke="#2A1E4D" strokeWidth="2.5" strokeLinecap="round" />
              <line x1="8" y1="56" x2="1" y2="56" stroke="#2A1E4D" strokeWidth="2.5" strokeLinecap="round" />
            </g>
          )}

          {/* Left Ear */}
          <g className={getLeftEarStyle()}>
            {/* Outer Ear */}
            <path
              d="M 38 42 C 30 22 22 5 33 2 C 42 0 46 20 44 42 Z"
              fill="#FFFFFF"
              stroke="#2E2A26"
              strokeWidth="3"
              strokeLinejoin="round"
            />
            {/* Inner Ear (Blush pink) */}
            <path
              d="M 37 38 C 32 23 26 10 33 8 C 39 6 42 21 41 38 Z"
              fill="#F5A9A0"
            />
          </g>

          {/* Right Ear */}
          <g className={getRightEarStyle()}>
            {/* Outer Ear */}
            <path
              d="M 62 42 C 70 22 78 5 67 2 C 58 0 54 20 56 42 Z"
              fill="#FFFFFF"
              stroke="#2E2A26"
              strokeWidth="3"
              strokeLinejoin="round"
            />
            {/* Inner Ear (Blush pink) */}
            <path
              d="M 63 38 C 68 23 74 10 67 8 C 61 6 58 21 59 38 Z"
              fill="#F5A9A0"
            />
          </g>

          {/* Rabbit Head / Body */}
          <circle cx="50" cy="54" r="32" fill="#FFFFFF" stroke="#2E2A26" strokeWidth="3" />

          {/* Tunsay's Cute Blush Cheeks */}
          <ellipse cx="33" cy="54" rx="5" ry="3.5" fill="#F5A9A0" opacity="0.8" />
          <ellipse cx="67" cy="54" rx="5" ry="3.5" fill="#F5A9A0" opacity="0.8" />

          {/* Eyes */}
          {renderEyes()}

          {/* Cute Nose (Carrot Orange / Soft Pink) */}
          <path d="M 47 51 L 53 51 L 50 54 Z" fill="#F4A93B" stroke="#2E2A26" strokeWidth="1" />

          {/* Mouth */}
          {renderMouth()}

          {/* Small Green Clover Leaf Badge on Ear / Forehead */}
          <g transform="translate(60, 28) scale(0.6)">
            <path
              d="M 10 5 C 10 0 15 0 15 5 C 15 0 20 0 20 5 C 20 10 15 15 15 15 C 15 15 10 10 10 5 Z"
              fill="#4C9A6A"
            />
            <path d="M 15 14 L 17 22" stroke="#357A4E" strokeWidth="2" strokeLinecap="round" />
          </g>

          {/* Sparkles / Leaves if Celebrating */}
          {state === 'celebrating' && (
            <g className="animate-bounce">
              <text x="10" y="25" fontSize="14">🌱</text>
              <text x="75" y="25" fontSize="14">✨</text>
              <text x="50" y="10" fontSize="14">⭐</text>
            </g>
          )}

          {/* Listening State Pulse Ring */}
          {state === 'listening' && (
            <circle cx="50" cy="54" r="38" fill="none" stroke="#8FCFE0" strokeWidth="2" strokeDasharray="4 4" className="animate-spin" />
          )}
        </svg>
      </div>

      {/* WEG / Grade Badge if enabled */}
      {showBadge && (
        <span className="mt-1 px-2 py-0.5 bg-[#4C9A6A]/10 text-[#357A4E] text-[11px] font-extrabold rounded-full tracking-wide uppercase border border-[#4C9A6A]/20">
          {state === 'thinking' ? 'Thinking...' : state === 'listening' ? 'Listening...' : 'Tunsay WEG'}
        </span>
      )}
    </div>
  );
};
