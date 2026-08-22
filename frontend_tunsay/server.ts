import express from 'express';
import path from 'path';
import { createServer as createViteServer } from 'vite';

// P1.10 (.claude/plan.md): this server no longer talks to Gemini. It serves the
// SPA and proxies /api/* to the gateway, which owns auth, rate limiting and the
// camelCase boundary. The Gemini call and the system prompt live in
// pedagogy_service now. The browser keeps a single origin (:3000), so no CORS
// gymnastics are needed in dev.
const GATEWAY_URL = process.env.GATEWAY_URL || 'http://localhost:9000';

async function proxyJson(
  req: express.Request,
  res: express.Response,
  target: string,
) {
  try {
    const upstream = await fetch(`${GATEWAY_URL}${target}`, {
      method: req.method,
      headers: {
        'Content-Type': 'application/json',
        ...(req.headers.authorization
          ? { Authorization: req.headers.authorization }
          : {}),
      },
      body: ['GET', 'HEAD'].includes(req.method)
        ? undefined
        : JSON.stringify(req.body),
    });
    const text = await upstream.text();
    res
      .status(upstream.status)
      .type(upstream.headers.get('content-type') || 'application/json')
      .send(text);
  } catch (err) {
    // Gateway unreachable. 502 lets geminiService.ts fall back to the local
    // Tunsay engine, so the app still answers offline.
    console.error('Gateway proxy error:', (err as Error).message);
    res.status(502).json({
      error: 'gateway_unreachable',
      messageKhmer: 'មិនអីទេ! តោះយើងពិនិត្យមើលសំណួរនេះជាមួយគ្នាណា។ 🐰',
      messageEng: "No problem! Let's look at this step together. 🐰",
    });
  }
}

async function proxyRaw(req: express.Request, res: express.Response, targetPath: string) {
  try {
    const upstream = await fetch(`${GATEWAY_URL}${targetPath}`, {
      method: req.method,
      headers: {
        ...(req.headers.authorization ? { Authorization: req.headers.authorization } : {}),
        ...(req.headers['content-type'] ? { 'Content-Type': req.headers['content-type'] } : {}),
      },
      body: req as any,
      // @ts-ignore
      duplex: 'half',
    });
    const text = await upstream.text();
    res
      .status(upstream.status)
      .type(upstream.headers.get('content-type') || 'application/json')
      .send(text);
  } catch (err) {
    console.error('Gateway proxy error:', (err as Error).message);
    res.status(502).json({
      error: 'gateway_unreachable',
      messageKhmer: 'មិនអីទេ! តោះយើងពិនិត្យមើលសំណួរនេះជាមួយគ្នាណា។ 🐰',
      messageEng: "No problem! Let's look at this step together. 🐰",
    });
  }
}

async function startServer() {
  const app = express();
  
  let PORT = parseInt(process.env.PORT || '3000', 10);
  const args = process.argv.slice(2);
  const portIdx = args.findIndex(arg => arg === '-p' || arg === '--port');
  if (portIdx !== -1 && args[portIdx + 1]) {
    const parsed = parseInt(args[portIdx + 1], 10);
    if (!isNaN(parsed)) {
      PORT = parsed;
    }
  }

  // Audio and Image multipart uploads proxy before express.json()
  app.post('/api/chat/audio', (req, res) => proxyRaw(req, res, '/chat/audio'));
  app.post('/api/chat/image', (req, res) => proxyRaw(req, res, '/chat/image'));

  app.use(express.json());

  // Tutor turn → gateway /chat → orchestrator graph → pedagogy → Gemini.
  app.post('/api/tutor', (req, res) => proxyJson(req, res, '/chat'));

  // Answer checking → gateway /answers → orchestrator graph → grading.
  app.post('/api/answers', (req, res) => proxyJson(req, res, '/answers'));

  // Hints → gateway /hints → orchestrator graph → pedagogy → Gemini.
  app.post('/api/hints', (req, res) => proxyJson(req, res, '/hints'));

  // Auth → gateway /auth/* → auth_service (school code + PIN, no passwords).
  app.post('/api/auth/register', (req, res) => proxyJson(req, res, '/auth/register'));
  app.post('/api/auth/login', (req, res) => proxyJson(req, res, '/auth/login'));
  app.get('/api/auth/me', (req, res) => proxyJson(req, res, '/auth/me'));

  // Profile → gateway /profile/* → student_profile_service (stars, attempts, mastery).
  app.get('/api/profile', (req, res) => proxyJson(req, res, '/profile'));
  app.get('/api/profile/:id', (req, res) =>
    proxyJson(req, res, `/profile/${encodeURIComponent(req.params.id)}`),
  );
  app.post('/api/profile/attempts', (req, res) => proxyJson(req, res, '/profile/attempts'));
  app.post('/api/profile/hints', (req, res) => proxyJson(req, res, '/profile/hints'));

  // Problem catalog (public shape — correct_answer is stripped server-side).
  app.get('/api/problems', (req, res) => {
    const qs = new URLSearchParams(req.query as Record<string, string>).toString();
    return proxyJson(req, res, `/problems${qs ? `?${qs}` : ''}`);
  });
  app.get('/api/problems/:id', (req, res) =>
    proxyJson(req, res, `/problems/${encodeURIComponent(req.params.id)}`),
  );

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
    console.log(`Tunsay frontend on http://localhost:${PORT} (gateway: ${GATEWAY_URL})`);
  });
}

startServer();
