
import json

# Mock data based on the user's screenshot and typical structure
candidate_data = {
    "username": "lavy10",
    "email": "avinash.bhurke23@vit.edu",
    "total_solved": 3,
    "questions": {
        "1_0": {"solved": True, "data": {}},
        "1_1": {"solved": True, "data": {}},
        "1_2": {"solved": True, "data": {}}
    }
}

# Mock test questions (assuming it might be interpreted as flat or sections)
# Case A: Flat list of Codeforces questions
test_questions_flat = [
    {"type": "codeforces", "data": {"contestId": 1234, "index": "A", "rating": 800}},
    {"type": "codeforces", "data": {"contestId": 1234, "index": "B", "rating": 1000}},
    {"type": "codeforces", "data": {"contestId": 1234, "index": "C", "rating": 1200}}
]

# Case B: Section-based structure
test_questions_sections = [
    {
        "id": 1,
        "name": "Section 1",
        "questions": [
            {"type": "codeforces", "data": {"contestId": 1234, "index": "A", "rating": 800}},
            {"type": "codeforces", "data": {"contestId": 1234, "index": "B", "rating": 1000}},
            {"type": "codeforces", "data": {"contestId": 1234, "index": "C", "rating": 1200}}
        ]
    }
]

def analyze_ids(questions, is_flat_case):
    print(f"\n--- Analyzing Case: {'Flat' if is_flat_case else 'Sections'} ---")
    
    # Logic from llm_analyzer.py _analyze_difficulty_performance
    is_flat = True
    if questions and isinstance(questions[0], dict) and 'questions' in questions[0] and isinstance(questions[0]['questions'], list):
        is_flat = False
        
    print(f"Detected as flat: {is_flat}")

    if is_flat:
        sections = [{'id': 'default', 'questions': questions}]
    else:
        sections = questions
        
    for section_idx, section in enumerate(sections):
        section_id = section.get('id', section_idx)
        print(f"Section ID: {section_id}")
        
        for q_idx, question in enumerate(section.get('questions', [])):
            # 1. Primary ID (Codeforces)
            q_data = question.get('data', question)
            cf_id = f"{q_data.get('contestId', '')}{q_data.get('index', '')}"
            
            # 2. Fallback ID (Current Logic)
            s_id = section.get('id')
            if s_id is None: s_id = section_idx
            fallback_id = f"{s_id}_{q_idx}"
            
            # Check matches
            found_cf = cf_id in candidate_data['questions']
            found_fallback = fallback_id in candidate_data['questions']
            
            print(f"  Q{q_idx}: CF_ID='{cf_id}' (Found: {found_cf}), Fallback_ID='{fallback_id}' (Found: {found_fallback})")

print("Checking keys in candidate data:", list(candidate_data['questions'].keys()))

analyze_ids(test_questions_flat, True)
analyze_ids(test_questions_sections, False)
