import express from 'express';
import path from 'path';
import { GoogleGenAI } from '@google/genai';
import { createServer as createViteServer } from 'vite';

async function startServer() {
  const app = express();
  const PORT = 3000;

  app.use(express.json());

  // Sayo AI Tutor API Endpoint
  app.post('/api/tutor', async (req, res) => {
    try {
      const { prompt, mode, problemContext, language = 'km' } = req.body;
      const apiKey = process.env.GEMINI_API_KEY;

      if (!apiKey || apiKey === 'MY_GEMINI_API_KEY') {
        // Return default Sayo structured response
        if (language === 'km') {
          return res.json({
            textKhmer: 'តោះយើងពិនិត្យមើលសំណួរនេះជាមួយគ្នានា! តើអ្នកឃើញលេខអ្វីខ្លះ? 🐰',
            textEng: '',
            isSafetyRefusal: false
          });
        } else {
          return res.json({
            textKhmer: '',
            textEng: "Let's look at the question together! What numbers do you see? 🐰",
            isSafetyRefusal: false
          });
        }
      }

      const ai = new GoogleGenAI({
        apiKey,
        httpOptions: {
          headers: {
            'User-Agent': 'aistudio-build',
          },
        },
      });
      const languageInstruction = language === 'km'
        ? 'Always reply exclusively in clear, warm, encouraging Khmer language for primary students (Grades 1–6). Do not include any English translation in the response.'
        : 'Always reply exclusively in clear, warm, simple English language for primary students (Grades 1–6). Do not include any Khmer translation in the response.';

      const systemInstruction = `You are Tunsay (ទន្សាយ), a friendly cartoon rabbit tutor for Westline Education Group (WEG) in Cambodia.
Your goal is to help Grade 1–6 students understand Math and Science homework step-by-step without giving direct answers immediately.
Mode: ${mode || 'student'}.
${languageInstruction}
Never be judgmental. Encourage the student with "Let's solve it together".`;

      const response = await ai.models.generateContent({
        model: 'gemini-3.7-flash',
        contents: [
          { role: 'user', parts: [{ text: `${systemInstruction}\n\nUser Question: ${prompt}\nContext: ${JSON.stringify(problemContext || {})}` }] }
        ]
      });

      const responseText = response.text || '';
      if (language === 'km') {
        return res.json({
          textKhmer: responseText,
          textEng: '',
          isSafetyRefusal: false
        });
      } else {
        return res.json({
          textKhmer: '',
          textEng: responseText,
          isSafetyRefusal: false
        });
      }
    } catch (error) {
      console.error('Gemini API Error:', error);
      const language = req.body?.language || 'km';
      return res.json({
        textKhmer: language === 'km' ? 'មិនអីទេ! តោះយើងពិនិត្យមើលសំណួរនេះជាមួយគ្នាណា។ 🐰' : '',
        textEng: language === 'en' ? "No problem! Let's look at this step together. 🐰" : '',
        isSafetyRefusal: false
      });
    }
  });

  // Vite middleware for development
  if (process.env.NODE_ENV !== 'production') {
    const vite = await createViteServer({
      server: { middlewareMode: true },
      appType: 'spa',
    });
    app.use(vite.middlewares);
  } else {
    const distPath = path.join(process.cwd(), 'dist');
    app.use(express.static(distPath));
    app.get('*', (req, res) => {
      res.sendFile(path.join(distPath, 'index.html'));
    });
  }

  app.listen(PORT, '0.0.0.0', () => {
    console.log(`Sayo WEG AI Tutor Server running on http://localhost:${PORT}`);
  });
}

startServer();
