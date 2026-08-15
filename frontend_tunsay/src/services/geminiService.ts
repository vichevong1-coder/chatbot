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
  language: Language = 'km'
): Promise<{ textKhmer: string; textEng: string; isSafetyRefusal?: boolean }> {
  try {
    // P1.10: the request now carries the .claude/contracts.md §4 chat contract
    // (camelCase on the browser wire; the gateway translates). problemContext
    // is no longer shipped whole — the orchestrator loads the problem by id
    // from content_service rather than trusting a client blob. studentId is
    // omitted on purpose: the gateway injects it from the verified JWT.
    const response = await fetch('/api/tutor', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', ...authHeaders() },
      body: JSON.stringify({
        sessionId,
        prompt: userPrompt,
        mode,
        language,
        problemId: problemContext?.id,
        activeStepIndex: 0,
      }),
    });

    if (response.ok) {
      const data = await response.json();
      return {
        textKhmer: data.textKhmer || '',
        textEng: data.textEng || '',
        isSafetyRefusal: data.isSafetyRefusal || false
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
