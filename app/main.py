from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from .models import InterviewRequest, InterviewResponse
from .session import session_manager
from .interviewer import handle_interview_turn

app = FastAPI(
    title="AI Interview Agent API",
    description="Backend API for conducting realistic, personalized technical interviews.",
    version="1.0.0"
)

# Enable CORS for local testing/frontends
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {
        "status": "healthy",
        "message": "AI Interview Agent API is active!",
        "engine": "Deterministic Mock / Sandbox Mode"
    }

@app.post("/api/interview", response_model=InterviewResponse)
def interview_endpoint(req: InterviewRequest):
    session_id = req.sessionId
    
    # 1. Start Interview
    if req.candidate is not None:
        session = session_manager.create_session(session_id, req.candidate)
        
        # Exact expected response contract
        reply = "Welcome. Let's begin your interview."
        session.history.append({"role": "assistant", "content": reply})
        
        return InterviewResponse(
            reply=reply,
            done=False
        )
        
    # 2. Conversation Turn
    if req.message is not None:
        session = session_manager.get_session(session_id)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Session with ID '{session_id}' not found. Please start the interview first."
            )
            
        turn_result = handle_interview_turn(session, req.message)
        return InterviewResponse(**turn_result)
        
    # 3. Bad Request
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Invalid payload. Provide 'candidate' to start or 'message' to continue."
    )
