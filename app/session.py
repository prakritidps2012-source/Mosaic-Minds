import threading
from typing import List, Dict, Any, Optional
from .models import Candidate

class SessionState:
    def __init__(self, session_id: str, candidate: Candidate, selected_days: List[int]):
        self.session_id: str = session_id
        self.candidate: Candidate = candidate
        self.selected_days: List[int] = selected_days
        
        # State Machine Variables
        self.current_day_index: int = 0
        self.questions_asked: int = 0
        self.asked_main_question: bool = False
        self.pending_followup: bool = False
        self.done: bool = False
        
        # Conversation state
        self.history: List[Dict[str, str]] = []
        self.feedback: Optional[Dict[str, Any]] = None

    def get_current_day(self) -> Optional[int]:
        if self.current_day_index < len(self.selected_days):
            return self.selected_days[self.current_day_index]
        return None

def select_curriculum_days(candidate: Candidate) -> List[int]:
    """
    Personalizes the interview by deterministically selecting exactly 4 distinct curriculum days
    based on the candidate's historical progress in candidates.json.
    """
    selected: List[int] = []
    
    # 1. Strength Day: passed with 1 attempt (or lowest attempts)
    strength_days = [m.day for m in candidate.missions if m.passed and m.attempts == 1]
    if strength_days:
        selected.append(strength_days[0])
        
    # 2. Struggle/Resilience Day: passed with high attempts (>= 2)
    struggle_days = [m.day for m in candidate.missions if m.passed and m.attempts and m.attempts >= 2]
    # Sort by attempts descending to find the hardest day they passed
    struggle_days.sort(key=lambda d: next((m.attempts for m in candidate.missions if m.day == d), 0), reverse=True)
    for d in struggle_days:
        if d not in selected:
            selected.append(d)
            break
            
    # 3. Gap/Skipped Day: skipped is True, or passed is False
    skipped_days = [m.day for m in candidate.missions if m.skipped or m.passed is False]
    for d in skipped_days:
        if d not in selected:
            selected.append(d)
            break
            
    # 4. Role-Specific Day
    role = candidate.member.jobRole.lower()
    role_days: List[int] = []
    if "data" in role:
        role_days = [4, 7, 10]
    elif "ai" in role or "ml" in role:
        role_days = [22, 23, 12]
    elif "devops" in role or "infra" in role or "systems" in role:
        role_days = [28, 29]
    else:
        role_days = [16, 17] # Chatbot backend / frontend
        
    for d in role_days:
        if d not in selected:
            selected.append(d)
            break
            
    # If we still don't have 4 unique days, pad from the general core curriculum days
    fallback_pool = [7, 12, 16, 22, 23, 28, 31]
    for d in fallback_pool:
        if len(selected) >= 4:
            break
        if d not in selected:
            selected.append(d)
            
    # Keep selected days in chronological order
    selected.sort()
    return selected

class SessionManager:
    def __init__(self):
        self._sessions: Dict[str, SessionState] = {}
        self._lock = threading.Lock()

    def create_session(self, session_id: str, candidate: Candidate) -> SessionState:
        selected_days = select_curriculum_days(candidate)
        with self._lock:
            session = SessionState(session_id, candidate, selected_days)
            self._sessions[session_id] = session
            return session

    def get_session(self, session_id: str) -> Optional[SessionState]:
        with self._lock:
            return self._sessions.get(session_id)

    def delete_session(self, session_id: str):
        with self._lock:
            if session_id in self._sessions:
                del self._sessions[session_id]

# Singleton Session Manager instance
session_manager = SessionManager()
