import { HomeworkProblem, UserMode, Language } from '../types';
import { authHeaders } from '../api/client';

// One conversation per page load; "New Chat" is still a frontend-only reset,
// so the id lives for the tab's lifetime. The orchestrator keys the transcript
// on it (P1.7 session store).
const sessionId: string =
  typeof crypto !== 'undefined' && 'randomUUID' in crypto
    ? crypto.randomUUID()
    : `web-${Date.now()}-${Math.floor(Math.random() * 1e6)}`;

export async function askTunsayTutor(
  userPrompt: string,
  mode: UserMode = 'student',
  problemContext?: HomeworkProblem,
  language: Language = 'km',
  activeStepIndex: number = 0
): Promise<{ textKhmer: string; textEng: string; isSafetyRefusal?: boolean; suggestedNext?: string | null }> {
  try {
    let response = await fetch('/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', ...authHeaders() },
      body: JSON.stringify({
        sessionId,
        prompt: userPrompt,
        mode,
        language,
        problemId: problemContext?.id,
        activeStepIndex,
      }),
    });

    if (!response.ok) {
      response = await fetch('/api/tutor', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', ...authHeaders() },
        body: JSON.stringify({
          sessionId,
          prompt: userPrompt,
          mode,
          language,
          problemId: problemContext?.id,
          activeStepIndex,
        }),
      });
    }

    if (response.ok) {
      const data = await response.json();
      return {
        textKhmer: data.textKhmer || data.text_khmer || '',
        textEng: data.textEng || data.text_eng || '',
        isSafetyRefusal: data.isSafetyRefusal || data.is_safety_refusal || false,
        suggestedNext: data.suggestedNext || data.suggested_next || null,
      };
    }
  } catch (err) {
    console.log('Using local Tunsay tutor engine');
  }

  // Fallback intelligent Tunsay response engine — kept deliberately: it is the
  // offline story when the gateway is unreachable (.claude/plan.md P1.10).
  const promptLower = userPrompt.toLowerCase();

  // Safety / Unrelated topic check
  if (promptLower.includes('cheat') || promptLower.includes('hack') || promptLower.includes('fight') || promptLower.includes('game code')) {
    return {
      textKhmer: language === 'km' ? '🛡️ ខ្ញុំនៅទីនេះដើម្បីជួយសិក្សា និងធ្វើលំហាត់ដោយសុវត្ថិភាព។ តោះត្រឡប់ទៅមើលលំហាត់វិញណា! 🐰' : '',
      textEng: language === 'en' ? 'I am here to help with safe and educational topics. Let\'s go back to your homework! 🐰' : '',
      isSafetyRefusal: true
    };
  }

  // Parent Help Mode response
  if (mode === 'parent') {
    return {
      textKhmer: language === 'km' ? '👨‍👩‍👧 ខ្ញុំអាចជួយលោកអ្នកយល់ពីសំណួរនេះ ដើម្បីឲ្យលោកអ្នកអាចពន្យល់បន្តទៅកាន់កូនៗបានយ៉ាងងាយស្រួល។' : '',
      textEng: language === 'en' ? 'I can help you understand the question so you can explain it step-by-step to your child.' : ''
    };
  }

  // Tutor responses
  if (promptLower.includes(' hello') || promptLower.includes(' hi') || promptLower.includes('សួស្តី')) {
    return {
      textKhmer: language === 'km' ? 'សួស្តី! ខ្ញុំគឺទន្សាយ (Tunsay)។ តើយើងរៀនមុខវិជ្ជាអ្វីថ្ងៃនេះ? 🐰🌱' : '',
      textEng: language === 'en' ? 'Hi! I am Tunsay. Ready to solve homework together today? 🐰🌱' : ''
    };
  }

  if (promptLower.includes(' mean') || promptLower.includes('ន័យ') || promptLower.includes('មានន័យ')) {
    return {
      textKhmer: language === 'km' ? 'សំណួរនេះកំពុងសួរអំពីការផ្លាស់ប្តូរសភាពនៃធាតុ។ តោះពិនិត្យមើលពាក្យគន្លឹះទាំងអស់គ្នា! 🔍' : '',
      textEng: language === 'en' ? "This question is asking about state changes. Let's look at the key terms together! 🔍" : ''
    };
  }

  return {
    textKhmer: language === 'km' ? 'សំណួរល្អណាស់! តោះយើងពិនិត្យមើលលេខ និងពាក្យនៅក្នុងសំណួរនេះជាមួយគ្នាដំបូងណា។ 🐰' : '',
    textEng: language === 'en' ? "Great question! Let's look at the numbers and key words in the question together first. 🐰" : ''
  };
}

export const askSayoTutor = askTunsayTutor;

export async function submitStepAnswer(
  problemId: string,
  stepId: string,
  studentAnswer: string,
  language: Language = 'km'
): Promise<{ isCorrect: boolean; feedbackKhmer: string; feedbackEng: string; advanceToStep?: number }> {
  try {
    const response = await fetch('/api/answers', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', ...authHeaders() },
      body: JSON.stringify({
        sessionId,
        problemId,
        stepId,
        studentAnswer,
        language
      })
    });
    if (response.ok) {
      return await response.json();
    }
  } catch (err) {
    console.error('Failed to submit step answer:', err);
  }
  // Fallback if backend is down
  return {
    isCorrect: false,
    feedbackKhmer: language === 'km' ? 'មានបញ្ហាបច្ចេកទេសក្នុងការតភ្ជាប់។ សូមព្យាយាមម្តងទៀត។ 🐰' : '',
    feedbackEng: language === 'en' ? 'Connection issue. Please try again. 🐰' : ''
  };
}

export async function fetchAIHint(
  problemId: string,
  stepId: string,
  hintLevel: number,
  language: Language = 'km'
): Promise<{ hintKhmer: string; hintEng: string; hintLevel: number }> {
  try {
    const response = await fetch('/api/hints', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', ...authHeaders() },
      body: JSON.stringify({
        sessionId,
        problemId,
        stepId,
        hintLevel,
        language
      })
    });
    if (response.ok) {
      return await response.json();
    }
  } catch (err) {
    console.error('Failed to fetch AI hint:', err);
  }
  return {
    hintKhmer: language === 'km' ? 'សូមពិនិត្យមើលសំណួរម្តងទៀតដោយប្រុងប្រយ័ត្ន ឬសួរគ្រូបង្រៀនរបស់អ្នកសម្រាប់ជំនួយបន្ថែម! 🐰' : '',
    hintEng: language === 'en' ? 'Please read the question carefully again or ask your teacher for extra help! 🐰' : '',
    hintLevel
  };
}

export async function fetchStudentProfile(): Promise<{ stars: number; completedProblemsCount: number } | null> {
  try {
    const response = await fetch('/api/profile', {
      headers: authHeaders(),
    });
    if (response.ok) {
      const data = await response.json();
      return {
        stars: data.stars ?? data.stars_earned ?? 0,
        completedProblemsCount: data.completedProblemsCount ?? data.completed_problems_count ?? 0,
      };
    }
  } catch (err) {
    console.error('Failed to fetch profile stats:', err);
  }
  return null;
}

export async function deductHintStars(
  hintLevel: number
): Promise<{ starsRemaining: number }> {
  try {
    const response = await fetch('/api/profile/hints', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', ...authHeaders() },
      body: JSON.stringify({
        rung: hintLevel,
        hint_level: hintLevel,
      }),
    });
    if (response.ok) {
      const data = await response.json();
      return { starsRemaining: data.remaining_stars ?? data.starsRemaining ?? -1 };
    }
  } catch (err) {
    console.error('Failed to deduct hint stars:', err);
  }
  return { starsRemaining: -1 };
}

export async function recordProblemAttempt(
  problemId: string,
  stepId: string,
  isCorrect: boolean,
  studentAnswer: string = ""
): Promise<boolean> {
  try {
    const response = await fetch('/api/profile/attempts', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', ...authHeaders() },
      body: JSON.stringify({
        session_id: sessionId,
        problem_id: problemId,
        step_id: stepId,
        is_correct: isCorrect,
        student_answer: studentAnswer,
      }),
    });
    return response.ok;
  } catch (err) {
    console.error('Failed to record attempt:', err);
    return false;
  }
}

export async function sendVoiceTurn(
  audioBlob: Blob,
  mode: UserMode = 'student',
  problemContext?: HomeworkProblem,
  language: Language = 'km',
  activeStepIndex: number = 0
): Promise<{ textKhmer: string; textEng: string; userTranscript?: string; isSafetyRefusal?: boolean }> {
  try {
    const formData = new FormData();
    formData.append('file', audioBlob, 'voice_query.webm');
    formData.append('session_id', sessionId);
    formData.append('mode', mode);
    formData.append('language', language);
    if (problemContext?.id) formData.append('problem_id', problemContext.id);
    formData.append('active_step_index', String(activeStepIndex));

    const response = await fetch('/api/chat/audio', {
      method: 'POST',
      headers: authHeaders(),
      body: formData,
    });
    if (response.ok) {
      const data = await response.json();
      return {
        textKhmer: data.textKhmer || data.text_khmer || '',
        textEng: data.textEng || data.text_eng || '',
        userTranscript: data.userTranscript || data.user_transcript || '',
        isSafetyRefusal: data.isSafetyRefusal || data.is_safety_refusal || false,
      };
    }
  } catch (err) {
    console.error('Voice chat error:', err);
  }
  return {
    textKhmer: language === 'km' ? 'មិនអីទេ! តោះយើងពិនិត្យសំណួរនេះជាមួយគ្នាណា 🐰' : '',
    textEng: language === 'en' ? "No problem! Let's look at it together. 🐰" : '',
  };
}

export async function sendImageTurn(
  imageBlob: Blob,
  mode: UserMode = 'student',
  language: Language = 'km'
): Promise<{ textKhmer: string; textEng: string; userTranscript?: string; isSafetyRefusal?: boolean }> {
  try {
    const formData = new FormData();
    formData.append('file', imageBlob, 'homework_photo.jpg');
    formData.append('session_id', sessionId);
    formData.append('mode', mode);
    formData.append('language', language);

    const response = await fetch('/api/chat/image', {
      method: 'POST',
      headers: authHeaders(),
      body: formData,
    });
    if (response.ok) {
      const data = await response.json();
      return {
        textKhmer: data.textKhmer || data.text_khmer || '',
        textEng: data.textEng || data.text_eng || '',
        userTranscript: data.userTranscript || data.user_transcript || '',
        isSafetyRefusal: data.isSafetyRefusal || data.is_safety_refusal || false,
      };
    }
  } catch (err) {
    console.error('Image chat error:', err);
  }
  return {
    textKhmer: language === 'km' ? 'ខ្ញុំបានទទួលរូបថតហើយ! តោះយើងចាប់ផ្តើមរៀនជាមួយគ្នា 🐰' : '',
    textEng: language === 'en' ? "I received your photo! Let's solve it together 🐰" : '',
  };
}
