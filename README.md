# AI Interview Agent - Vibe Code Hackathon

This is an AI-powered Interview Agent built for the ABTalks Vibe Code Hackathon. It conducts realistic, personalized technical interviews based on a 31-day curriculum and specific candidate profiles.

## Features
- **Personalized Interviews**: Tailors questions based on the candidate's historical performance (strengths, struggles, gaps).
- **Curriculum-Driven**: Uses a structured 31-day AI curriculum as the source of technical truth.
- **Adaptive Flow**: Asks intelligent follow-up questions and scenario-based probes.
- **Stateful Sessions**: Maintains interview context using `sessionId`.
- **Structured Feedback**: Generates actionable feedback covering strengths, gaps, and next steps.

## Architecture
- **Backend**: FastAPI (Python)
- **Session Management**: In-memory thread-safe storage.
- **Logic Engine**: Deterministic state machine (Phase 2) transitioning to LLM-powered (Phase 3).
- **Contract**: Strictly adheres to `technical-spec.md`.

## How to Run

### Prerequisites
- Python 3.13+
- Virtual environment (`venv`)

### Setup
1. Clone the repository.
2. Create and activate a virtual environment:
   ```powershell
   python -m venv .venv
   .\.venv\Scripts\activate
   ```
3. Install dependencies:
   ```powershell
   pip install -r requirements.txt
   ```
4. (Optional) Create a `.env` file for Phase 3:
   ```text
   GEMINI_API_KEY=your_key_here
   LLM_PROVIDER=gemini
   ```

### Running the Server
```powershell
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

## API Endpoint

### POST `/api/interview`

#### 1. Start Interview
**Request:**
```json
{
  "sessionId": "abc-123",
  "candidate": { ... candidate data ... }
}
```
**Response:**
```json
{
  "reply": "Welcome. Let's begin your interview.",
  "done": false
}
```

#### 2. Conversation Turn
**Request:**
```json
{
  "sessionId": "abc-123",
  "message": "My answer to the technical question..."
}
```
**Response:**
```json
{
  "reply": "Next follow-up question...",
  "done": false
}
```

#### 3. End Interview
**Response:**
```json
{
  "reply": "Interview completed.",
  "done": true,
  "feedback": {
    "summary": "...",
    "strengths": [],
    "gaps": [],
    "next": []
  }
}
```

## Testing
You can run the provided test script to verify the full interview flow:
```powershell
python test_api.py
```
