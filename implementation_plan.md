# Implementation Plan — Local LLM Integration (Ollama / Llama 3.2)

We want to allow the Tunsay backend to run **fully locally** using Ollama (specifically with the `llama3.2:3b` model that is already downloaded on the host machine), while reserving space for the Gemini API key so users can easily toggle between local and remote LLM providers.

---

## User Review Required

> [!NOTE]
> We will add three new environment variables in `.env` to support this toggling:
> * `LLM_PROVIDER`: Can be `"ollama"` or `"gemini"`. Defaults to `"gemini"`.
> * `OLLAMA_URL`: Points to your local Ollama instance (defaults to `http://localhost:11434`).
> * `OLLAMA_MODEL`: The local model to query (defaults to `llama3.2:3b`).

---

## Proposed Changes

### Component: Shared Data Access Layer (`dal`)

#### [MODIFY] [llm_client.py](file:///e:/TunSay-AI/dal/llm_client.py)

1. **Import & Settings**:
   - Add new default variables:
     ```python
     DEFAULT_PROVIDER_ENV = "LLM_PROVIDER"
     DEFAULT_PROVIDER = "gemini"
     DEFAULT_OLLAMA_URL = "http://localhost:11434"
     DEFAULT_OLLAMA_MODEL = "llama3.2:3b"
     ```

2. **Refactor `_effective_api_key` and fallback check**:
   - If `LLM_PROVIDER` is `"ollama"`, do not require `GEMINI_API_KEY` to be present.

3. **Implement Ollama Client Call**:
   - Create an internal async function `_ollama_call` that makes a POST request to `{OLLAMA_URL}/v1/chat/completions` using the OpenAI-compatible chat format.
   - We reuse the already-imported `httpx` module. No new packages are needed.

4. **Update `_result_from_response`**:
   - Detect if the response is a dictionary (OpenAI/Ollama API JSON) or a Google GenAI response object, and parse the text content and token usage counts accordingly.

---

## Verification Plan

### Automated Tests
- Run `pytest dal/tests/` to ensure no existing logic is broken.
- Add unit tests verifying:
  - Switching `LLM_PROVIDER` to `ollama` changes target resolution.
  - The request payload matches the OpenAI/Ollama schema correctly.

### Manual Verification
1. Set `LLM_PROVIDER=ollama` in `.env`.
2. Start your local Ollama server: `ollama run llama3.2:3b` (if not already running in background).
3. Query the pedagogy service `/explain` endpoint locally and confirm that `llama3.2:3b` generates the Socratic feedback.
