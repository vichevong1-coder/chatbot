import React from 'react';
import { UserMode, Language } from '../types';
import { User, Users } from 'lucide-react';

interface ModeSwitcherProps {
  mode: UserMode;
  language?: Language;
  onToggleMode: (mode: UserMode) => void;
}

export const ModeSwitcher: React.FC<ModeSwitcherProps> = ({ 
  mode, 
  language = 'km',
  onToggleMode 
}) => {
  const isKhmer = language === 'km';

  return (
    <div className="inline-flex p-1 bg-[#EAF2FF] border-3 border-[#2A1E4D] rounded-2xl shadow-[3px_3px_0px_#2A1E4D] text-xs">
      <button
        type="button"
        onClick={() => onToggleMode('student')}
        className={`px-3 py-1.5 rounded-xl font-black flex items-center gap-1.5 transition-all cursor-pointer ${
          mode === 'student'
            ? 'bg-[#FF6FA3] text-white border-2 border-[#2A1E4D] shadow-[2px_2px_0px_#2A1E4D] -translate-y-0.5'
            : 'text-[#2A1E4D] hover:bg-black/5'
        }`}
        title={isKhmer ? 'របៀបសិស្ស' : 'Student Mode'}
      >
        <User className="w-4 h-4 stroke-[2.5]" />
        <span>{isKhmer ? 'សិស្ស' : 'Student'}</span>
      </button>

      <button
        type="button"
        onClick={() => onToggleMode('parent')}
        className={`px-3 py-1.5 rounded-xl font-black flex items-center gap-1.5 transition-all cursor-pointer ${
          mode === 'parent'
            ? 'bg-[#FFCB3D] text-[#2A1E4D] border-2 border-[#2A1E4D] shadow-[2px_2px_0px_#2A1E4D] -translate-y-0.5'
            : 'text-[#2A1E4D] hover:bg-black/5'
        }`}
        title={isKhmer ? 'របៀបអាណាព្យាបាល' : 'Parent Mode'}
      >
        <Users className="w-4 h-4 stroke-[2.5]" />
        <span>{isKhmer ? 'អាណាព្យាបាល' : 'Parent'}</span>
      </button>
    </div>
  );
};
