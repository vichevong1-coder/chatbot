/**
 * Core type definitions for Tunsay AI Homework Tutor
 */

export type Grade = 1 | 2 | 3 | 4 | 5 | 6;

export type Subject = 'math' | 'science' | 'english';

export type UserMode = 'student' | 'parent';

export type Language = 'km' | 'en';

export type TunsayState = 
  | 'idle' 
  | 'listening' 
  | 'thinking' 
  | 'explaining' 
  | 'encouraging' 
  | 'celebrating' 
  | 'sleepy';

export type SayoState = TunsayState;

export interface StepItem {
  id: string;
  stepNumber: number;
  totalSteps: number;
  questionKhmer: string;
  questionEng: string;
  inputFormat: 'mcq' | 'number' | 'text';
  /** OPTIONAL and currently never populated — absent from .claude/contracts.md,
   *  from dal's StepItem schema, and from every seed_data YAML. StepCard renders
   *  a "Guiding Prompt" panel from it, which is why it is typed at all; the panel
   *  hides itself when the field is missing. Authoring these, or dropping the
   *  panel, is a content decision nobody has made yet. */
  socraticPromptKhmer?: string;
  socraticPromptEng?: string;
  options?: string[];
  correctAnswer: string;
  hint1: {
    khmer: string;
    eng: string;
  };
  hint2: {
    khmer: string;
    eng: string;
  };
  hint3: {
    titleKhmer: string;
    titleEng: string;
    exampleKhmer: string;
    exampleEng: string;
  };
  explainDifferently: {
    simpleKhmer: string;
    simpleEng: string;
    analogyTitle: string;
    analogyKhmer: string;
    analogyEng: string;
    analogyType: 'apples' | 'pizza' | 'water' | 'plants';
  };
}

export interface HomeworkProblem {
  id: string;
  titleKhmer: string;
  titleEng: string;
  grade: Grade;
  subject: Subject;
  problemStatementKhmer: string;
  problemStatementEng: string;
  imageUri?: string;
  steps: StepItem[];
}

export interface ChatMessage {
  id: string;
  sender: 'user' | 'sayo' | 'system';
  textKhmer?: string;
  textEng: string;
  timestamp: string;
  imageUri?: string;
  problem?: HomeworkProblem;
  activeStepIndex?: number;
  isSafetyRefusal?: boolean;
  isParentHelp?: boolean;
  suggestedNext?: string | null;
}

export interface UserProfile {
  name: string;
  grade: Grade;
  subject: Subject;
  mode: UserMode;
  language: Language;
  completedProblemsCount: number;
  starsEarned: number;
}
