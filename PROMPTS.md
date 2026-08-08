# Vibe Coding Development Log - Prompts & Conversations

This file documents the iterative prompts and design specifications used to build the AI Interview Agent for the ABTalks Vibe Code Hackathon.

---

## 1. Initial Planning & Spec Alignment (Phase 1)

**Prompt:**
> We are building this project for the ABTalks Vibe Code Hackathon.
> 
> I want you to be the primary coding agent. I will guide you through prompts, and you should write and modify the code yourself. Do not ask me to manually implement code unless absolutely necessary.
> 
> You have already read:
> - technical-spec.md
> - curriculum.json
> - candidates.json
> 
> First, fully understand these files and the problem statement before writing code.
> 
> Our selected problem statement is:
> "Build the interviewer, not the interview."
> 
> We need an AI Interview Agent that:
> - conducts a realistic multi-turn technical interview
> - personalizes the interview using the candidate profile
> - uses the 31-day curriculum as the source of technical topics
> - asks at least 8 questions
> - covers at least 4 different curriculum days
> - asks intelligent follow-up questions based on the candidate's previous answers
> - maintains conversation context using sessionId
> - generates structured feedback at the end
> - implements the exact POST /api/interview contract from technical-spec.md
> 
> Important:
> - Do NOT use a database unless you later determine it is genuinely necessary.
> - Do NOT add unnecessary architecture or over-engineer the project.
> - Keep the implementation suitable for a hackathon and easy to understand.
> - The API contract in technical-spec.md is the source of truth.
> - The supplied curriculum.json and candidates.json are the source of truth for curriculum and candidate data.
> - Do not invent fields or change the required API contract.
> 
> For now, DO NOT build the entire application.
> 
> First:
> 1. Analyze the existing workspace.
> 2. Propose a simple implementation plan.
> 3. Propose the project/file structure.
> 4. Explain how you will handle session state, curriculum selection, adaptive follow-ups, question counting, and final feedback.
> 5. Identify any risks or ambiguities you found in the supplied files.
> 6. Then wait for my approval before creating the implementation.
> 
> Do not write code yet.

**Design Highlights / Approved Adjustments:**
- **Incremental Implementation:** Genuine vibe coding, making sure the project remains runnable after each phase.
- **State Machine Routing:** Guarantees at least 8 questions across at least 4 distinct days, allowing expansion/adaptive questions.
- **Configurable LLM:** Externalizable using environment variables; no secrets in the repo.
- **Local Sandbox / Mock Mode:** Phase 1 uses deterministic selection logic and a structured mockup conversation flow allowing developer/client testing without any active LLM API keys.

---

## 2. Base API & Session Management (Phase 2)

**Work Performed:**
- **Project Structure:** Created `app/` directory with `main.py`, `models.py`, `config.py`, `session.py`, and `interviewer.py`.
- **API Implementation:** Built `POST /api/interview` following `technical-spec.md`.
- **Session Management:** Implemented thread-safe in-memory `SessionManager` and `SessionState`.
- **Deterministic Logic:** 
    - Personalizes curriculum selection (Strength, Struggle, Gap, Role-specific days).
    - Guarantees 8 questions across 4 distinct days.
    - Implements adaptive follow-up behavior (Main Question -> Follow-up).
- **Verification:** 
    - Created `test_api.py` using `httpx`.
    - Successfully simulated a full 9-turn interview with Sarah Johnson's profile.
    - Verified final structured feedback generation.

**Test Commands:**
```powershell
# Start server
uvicorn app.main:app --host 127.0.0.1 --port 8000

# Run full simulation
python test_api.py
```

---

## 3. Gemini LLM Integration (Phase 3)

**Prompt:**
> Implement Phase 3: Gemini LLM integration for the existing AI Interview Agent.
> 
> Requirements:
> - Keep the existing FastAPI API contract unchanged.
> - Keep session management and the existing deterministic flow as fallback.
> - Use GEMINI_API_KEY from .env.
> - Make the LLM integration configurable through LLM_PROVIDER.
> - If Gemini is unavailable or the API key is missing, automatically fall back to the existing deterministic/mock interviewer.
> - Do not expose or hardcode the API key.
> - Keep the implementation simple and hackathon-friendly.

**Work Performed:**
- **Gemini Integration:** Implemented `call_gemini_api` in `app/interviewer.py` using `httpx`.
- **LLM_PROVIDER Configuration:** Added `GEMINI_API_KEY` and `LLM_PROVIDER` to `app/config.py` and `.env` (template).
- **Fallback Mechanism:** Implemented robust logic to automatically switch between `gemini` and `mock` providers.
- **Adaptive Interaction:** Updated `handle_interview_turn` to use Gemini for question generation and final feedback, while maintaining conversation history context.
- **Verification:** Verified entire interview flow, fallback mechanism, and feedback generation using `test_api.py`.

**Test Commands:**
```powershell
# Set LLM_PROVIDER="gemini" or "mock" in .env
# Run simulation
python test_api.py
```
