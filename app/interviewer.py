import json
from typing import List, Dict, Any, Optional
import httpx
from .models import Candidate, Feedback
from .session import SessionState
from .config import CURRICULUM_DATA, GEMINI_API_KEY, LLM_PROVIDER

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

def is_gemini_available() -> bool:
    """Checks if LLM provider is Gemini and an API key is provided."""
    return LLM_PROVIDER == "gemini" and bool(GEMINI_API_KEY)

def call_gemini_api(contents: list, system_instruction: str = None, response_json: bool = False) -> str:
    """Calls the Gemini API using httpx."""
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
    
    payload = {
        "contents": contents
    }
    
    if system_instruction:
        payload["systemInstruction"] = {
            "parts": [{"text": system_instruction}]
        }
        
    if response_json:
        payload["generationConfig"] = {
            "responseMimeType": "application/json"
        }
        
    headers = {
        "Content-Type": "application/json"
    }
    
    with httpx.Client() as client:
        response = client.post(url, json=payload, headers=headers, timeout=15.0)
        response.raise_for_status()
        res_data = response.json()
        
        candidates = res_data.get("candidates", [])
        if candidates:
            parts = candidates[0].get("content", {}).get("parts", [])
            if parts:
                return parts[0].get("text", "")
                
        raise ValueError("Invalid response structure from Gemini API")

def handle_interview_turn(session: SessionState, user_message: str) -> Dict[str, Any]:
    """
    Applies the interview state machine and returns the next response.
    Integrates Gemini LLM with automatic deterministic fallback.
    Returns:
        Dict with "reply", "done", and optionally "feedback"
    """
    # Append the user's response to history
    session.history.append({"role": "user", "content": user_message})
    
    # Check if the interview is ready to end
    if session.questions_asked >= 8:
        session.done = True
        
        # Try to use Gemini for feedback if available
        if is_gemini_available():
            try:
                # Compile conversation history
                contents = []
                for msg in session.history:
                    role = "model" if msg["role"] == "assistant" else "user"
                    contents.append({
                        "role": role,
                        "parts": [{"text": msg["content"]}]
                    })
                contents.append({
                    "role": "user",
                    "parts": [{"text": "Please analyze our entire technical interview conversation and generate the final structured feedback now in the requested JSON format."}]
                })
                
                feedback_system_prompt = (
                    "You are an expert AI Technical Interviewer. You have completed the technical interview with the candidate. "
                    "Analyze the conversation history and candidate profile to generate detailed, structured, and personalized feedback in JSON format.\n\n"
                    "The JSON response must strictly follow this schema:\n"
                    "{\n"
                    "  \"summary\": \"Overall summary of performance, strengths, and areas of growth...\",\n"
                    "  \"strengths\": [\"Strength 1\", \"Strength 2\"],\n"
                    "  \"gaps\": [\"Gap 1\", \"Gap 2\"],\n"
                    "  \"next\": [\"Actionable step 1\", \"Actionable step 2\"]\n"
                    "}\n\n"
                    "Ensure each point in the lists is concise, highly professional, realistic, and specific to the candidate's actual responses in this conversation."
                )
                
                gemini_feedback_str = call_gemini_api(
                    contents=contents,
                    system_instruction=feedback_system_prompt,
                    response_json=True
                )
                
                # Parse feedback JSON
                feedback_json = json.loads(gemini_feedback_str)
                required_keys = ["summary", "strengths", "gaps", "next"]
                if all(k in feedback_json for k in required_keys):
                    session.feedback = feedback_json
                else:
                    raise ValueError("Missing required keys in Gemini feedback JSON")
            except Exception as e:
                print(f"Failed to generate feedback via Gemini, falling back to mock: {e}")
                session.feedback = generate_mock_feedback(session)
        else:
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
        # Fallback if index overflows
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
    years_exp = session.candidate.member.yearsExperience
    education = session.candidate.member.education
    
    # Decide which of the 4 days we are on (index 0 to 3)
    day_type_index = session.current_day_index
    is_main_question = not session.asked_main_question
    
    # Update state variables for the turn
    if is_main_question:
        session.asked_main_question = True
    else:
        session.asked_main_question = False
        session.current_day_index += 1
    session.questions_asked += 1
    
    # Prepare status info
    if day_type_index == 0:
        status_info = "The candidate passed this curriculum day on their very first attempt, showing it's a strength."
    elif day_type_index == 1:
        attempts = 2
        for m in session.candidate.missions:
            if m.day == current_day:
                attempts = m.attempts or 2
                break
        status_info = f"The candidate struggled with this curriculum day, requiring {attempts} attempts to pass, showing resilience."
    elif day_type_index == 2:
        status_info = "The candidate skipped this curriculum day during their course, representing a potential knowledge gap."
    else:
        status_info = f"This topic is highly relevant to their role as a {job_role}."
        
    # Check if Gemini is available for question generation
    if is_gemini_available():
        try:
            # Prepare conversation history
            contents = []
            for msg in session.history:
                role = "model" if msg["role"] == "assistant" else "user"
                contents.append({
                    "role": role,
                    "parts": [{"text": msg["content"]}]
                })
                
            system_prompt = (
                "You are an expert AI Technical Interviewer conducting a professional, realistic, and friendly technical interview.\n\n"
                "Context about the Candidate:\n"
                f"- Name: {candidate_name}\n"
                f"- Applying for Role: {job_role}\n"
                f"- Years of Experience: {years_exp}\n"
                f"- Education: {education}\n\n"
                "We are conducting an 8-question structured interview covering 4 selected curriculum days. "
                f"We are currently assessing Day {current_day}: '{day_title}', which covers tools: {tools} and objectives: {objectives}.\n"
                f"Candidate's status for this topic: {status_info}\n\n"
            )
            
            if is_main_question:
                system_prompt += (
                    "This is the FIRST question (Main Question) for this day topic. "
                    "Your task: Ask a natural, professional, and personalized question about their experience with this topic, "
                    "referencing their status (e.g., that they passed first try, struggled, or skipped it) and ask them to explain their implementation, "
                    "setup, or theoretical understanding. Do not ask multiple questions at once. Keep it to one clear, direct question.\n"
                )
            else:
                system_prompt += (
                    "This is the SECOND question (Adaptive Follow-up) for this day topic. "
                    "Your task: Analyze the candidate's last answer and ask an intelligent, realistic, and adaptive technical follow-up question. "
                    "Do not just repeat yourself or ask generic questions. Dive deeper into their specific explanation, or present a challenging production scenario/trade-off based on what they said. "
                    "Keep your follow-up concise, direct, and conversational.\n"
                )
                
            system_prompt += (
                "\nGuidelines:\n"
                "- Maintain a friendly but professional, expert interviewer persona. Never break character.\n"
                "- Do not output anything other than your response as the interviewer. No conversational preamble/metadata.\n"
                "- Keep your response brief, clear, and focused (around 2-3 sentences)."
            )
            
            reply = call_gemini_api(
                contents=contents,
                system_instruction=system_prompt
            )
            
            # Clean up response quotes
            reply = reply.strip()
            if reply.startswith('"') and reply.endswith('"'):
                reply = reply[1:-1].strip()
                
            session.history.append({"role": "assistant", "content": reply})
            return {
                "reply": reply,
                "done": False
            }
        except Exception as e:
            print(f"Failed to generate question via Gemini, falling back to deterministic: {e}")
            
    # Deterministic Mock Fallback
    reply = ""
    if is_main_question:
        if day_type_index == 0:
            reply = (
                f"Let's start our technical discussion. I see in your profile that you passed Day {current_day}: "
                f"'{day_title}' on your first attempt. It covers tools like: {tools}. "
                f"Can you explain your setup and what key learnings you took away from implementing this?"
            )
        elif day_type_index == 1:
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
            reply = (
                f"Next, let's look at Day {current_day}: '{day_title}'. Your profile shows you skipped this day during "
                f"the course. Even though it was skipped, can you describe how you would theoretically approach the objective: "
                f"'{main_obj}'?"
            )
        else:
            reply = (
                f"Finally, as a {job_role}, the topic of Day {current_day}: '{day_title}' is highly relevant to your role. "
                f"Can you share how you've designed or worked with tools like {tools} in real-world applications?"
            )
    else:
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
