from typing import List, Dict, Any, Optional
from .models import Candidate, Feedback
from .session import SessionState
from .config import CURRICULUM_DATA

def get_day_details(day_num: int) -> Dict[str, Any]:
    """Helper to retrieve curriculum details for a given day."""
    for d in CURRICULUM_DATA.get("days", []):
        if d.get("day") == day_num:
            return d
    return {
        "day": day_num,
        "title": f"Day {day_num} Topic",
        "tools": [],
        "objectives": []
    }

def generate_mock_feedback(session: SessionState) -> Dict[str, Any]:
    """Generates a personalized mock feedback object based on the candidate and selected days."""
    name = session.candidate.member.name
    role = session.candidate.member.jobRole
    days = session.selected_days
    
    # Get titles for reference
    t1 = get_day_details(days[0])["title"]
    t2 = get_day_details(days[1])["title"]
    t3 = get_day_details(days[2])["title"]
    t4 = get_day_details(days[3])["title"]
    
    return {
        "summary": (
            f"Overall, {name} demonstrated solid competencies suitable for a {role} role. "
            f"The candidate showed deep familiarity with core concepts on '{t1}' (Day {days[0]}) and '{t4}' (Day {days[3]}). "
            f"There were minor gaps identified in the skipped/challenging areas: '{t2}' (Day {days[1]}) and '{t3}' (Day {days[2]})."
        ),
        "strengths": [
            f"Strong technical communication and foundational knowledge of '{t1}'.",
            f"Shows high resilience and eventual mastery over challenging topics like '{t2}'."
        ],
        "gaps": [
            f"Lacks practical, hands-on experience in skipped topics like '{t3}'.",
            f"Could improve architecture and trade-off explanations regarding tools in '{t4}'."
        ],
        "next": [
            f"Deepen knowledge in '{t3}' by going through the skipped objectives.",
            f"Review the production setup instructions for '{t4}' to gain architecture level insights."
        ]
    }

def handle_interview_turn(session: SessionState, user_message: str) -> Dict[str, Any]:
    """
    Applies the deterministic interview state machine and returns the next response.
    Returns:
        Dict with "reply", "done", and optionally "feedback"
    """
    # Append the user's response to history
    session.history.append({"role": "user", "content": user_message})
    
    # Check if the interview is ready to end
    # We ask exactly 8 questions (4 days * 2 questions per day).
    # Turn 1: Welcome (questions_asked = 0)
    # Turns 2-9: Questions (questions_asked goes 1 to 8)
    # Turn 10: Candidate response to Q8. This is when we wrap up!
    if session.questions_asked >= 8:
        session.done = True
        session.feedback = generate_mock_feedback(session)
        reply = "Interview completed. Thank you for your time! We have compiled your feedback."
        session.history.append({"role": "assistant", "content": reply})
        return {
            "reply": reply,
            "done": True,
            "feedback": session.feedback
        }
        
    # Get current curriculum day we are assessing
    current_day = session.get_current_day()
    if current_day is None:
        # Fallback if index somehow overflows
        session.done = True
        session.feedback = generate_mock_feedback(session)
        return {
            "reply": "Interview completed. Thank you for your time!",
            "done": True,
            "feedback": session.feedback
        }
        
    day_details = get_day_details(current_day)
    day_title = day_details.get("title", f"Day {current_day}")
    tools = ", ".join(day_details.get("tools", []))
    objectives = day_details.get("objectives", ["No objectives listed"])
    main_obj = objectives[0] if objectives else "its main concepts"
    
    candidate_name = session.candidate.member.name
    job_role = session.candidate.member.jobRole
    
    reply = ""
    
    # Deterministic behavior depending on which of the 4 days we are on (index 0 to 3)
    day_type_index = session.current_day_index
    
    if not session.asked_main_question:
        # First question of this day module (Main Question)
        session.asked_main_question = True
        session.questions_asked += 1
        
        if day_type_index == 0:
            # Strength Day
            reply = (
                f"Let's start our technical discussion. I see in your profile that you passed Day {current_day}: "
                f"'{day_title}' on your first attempt. It covers tools like: {tools}. "
                f"Can you explain your setup and what key learnings you took away from implementing this?"
            )
        elif day_type_index == 1:
            # Struggle Day
            # Find attempts for this day
            attempts = 2
            for m in session.candidate.missions:
                if m.day == current_day:
                    attempts = m.attempts or 2
                    break
            reply = (
                f"Moving on to Day {current_day}: '{day_title}'. The logs indicate this day was quite challenging, "
                f"requiring {attempts} attempts to pass. What was the core roadblock you ran into, and how did you resolve it?"
            )
        elif day_type_index == 2:
            # Gap Day
            reply = (
                f"Next, let's look at Day {current_day}: '{day_title}'. Your profile shows you skipped this day during "
                f"the course. Even though it was skipped, can you describe how you would theoretically approach the objective: "
                f"'{main_obj}'?"
            )
        else:
            # Role-Specific Day
            reply = (
                f"Finally, as a {job_role}, the topic of Day {current_day}: '{day_title}' is highly relevant to your role. "
                f"Can you share how you've designed or worked with tools like {tools} in real-world applications?"
            )
    else:
        # Second question of this day module (Adaptive Follow-up)
        session.asked_main_question = False
        session.current_day_index += 1  # Move to next day index for the next turn
        session.questions_asked += 1
        
        if day_type_index == 0:
            reply = f"Interesting. How would you handle a scenario where one of these tools fails to connect or load in production?"
        elif day_type_index == 1:
            reply = f"That makes total sense. Having learned from that struggle, how would you design a similar system today to avoid that issue altogether?"
        elif day_type_index == 2:
            reply = f"Good theoretical reasoning. If you had to implement and test this model tomorrow, what key metrics or test cases would you focus on to verify success?"
        else:
            reply = f"That's a very solid approach. What is the biggest architectural trade-off or scaling constraint you've noticed with that design?"

    # Append to history and return
    session.history.append({"role": "assistant", "content": reply})
    return {
        "reply": reply,
        "done": False
    }
