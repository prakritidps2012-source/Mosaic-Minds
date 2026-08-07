import httpx
import json

BASE_URL = "http://127.0.0.1:8000"
SESSION_ID = "test-session-sarah"

CANDIDATE = {
    "member": {
        "id": "CAND-001",
        "name": "Sarah Johnson",
        "jobRole": "Senior Data Engineer",
        "yearsExperience": 9,
        "education": "MS Computer Science",
        "status": "COMPLETED"
    },
    "missions": [
        { "day": 7, "title": "Embeddings Explained", "passed": True, "attempts": 1 },
        { "day": 8, "title": "Vector Databases Overview", "passed": True, "attempts": 1 },
        { "day": 10, "title": "Retrieval & Matching Engine", "passed": True, "attempts": 2 },
        { "day": 12, "title": "Prompt Engineering Fundamentals", "passed": True, "attempts": 4 },
        { "day": 16, "title": "Chatbot Backend & API Integration", "passed": True, "attempts": 1 },
        { "day": 22, "title": "Multi-Agent Orchestration", "passed": True, "attempts": 2 },
        { "day": 23, "title": "Model Context Protocol (MCP)", "passed": True, "attempts": 2 },
        { "day": 28, "title": "Docker & Kubernetes Deployment", "passed": True, "attempts": 3 },
        { "day": 29, "title": "Monitoring, Logging & Observability", "skipped": True },
        { "day": 31, "title": "Capstone Project & Final Demo", "passed": True, "attempts": 1 }
    ],
    "signals": { "commitDays": 28, "missionsCompleted": 30, "missionsFirstTry": 20 }
}

def test_interview():
    with httpx.Client() as client:
        print("--- Starting Interview ---")
        start_payload = {
            "sessionId": SESSION_ID,
            "candidate": CANDIDATE
        }
        r = client.post(f"{BASE_URL}/api/interview", json=start_payload)
        print(f"Status: {r.status_code}")
        print(f"Response: {json.dumps(r.json(), indent=2)}")
        
        for i in range(1, 10):
            print(f"\n--- Turn {i} ---")
            message_payload = {
                "sessionId": SESSION_ID,
                "message": f"This is my response number {i}."
            }
            r = client.post(f"{BASE_URL}/api/interview", json=message_payload)
            print(f"Status: {r.status_code}")
            res = r.json()
            print(f"Reply: {res.get('reply')}")
            print(f"Done: {res.get('done')}")
            if res.get('done'):
                print(f"Feedback: {json.dumps(res.get('feedback'), indent=2)}")
                break

if __name__ == "__main__":
    test_interview()
