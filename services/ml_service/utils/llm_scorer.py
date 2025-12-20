import os
import json
import time
from typing import Optional
from openai import OpenAI

# Try to import PromptManager, fallback to default if not available
try:
    from backend.prompt_manager import prompt_manager
except ImportError:
    # If running as a standalone script or in a different context
    try:
        from ....backend.prompt_manager import prompt_manager
    except ImportError:
        prompt_manager = None

def compute_score(resume_text: str, job_description_text: str, model: str, hf_token_env: str = "HF_TOKEN") -> float:
    token = os.environ.get(hf_token_env)
    if not token:
        # Fallback: simple heuristic using length overlap when no token present
        common = len(set(resume_text.lower().split()) & set(job_description_text.lower().split()))
        total = len(set(job_description_text.lower().split())) or 1
        return min(100.0, 100.0 * common / total)

    client = OpenAI(base_url="https://router.huggingface.co/v1", api_key=token, timeout=60.0)
    
    # Get prompt from PromptManager or use fallback
    prompt = None
    if prompt_manager:
        prompt = prompt_manager.get_prompt("Resume and Matching Agent", "scoring")
    
    if prompt:
        formatted_prompt = prompt.format(jd=job_description_text, resume=resume_text)
    else:
        # Hardcoded fallback if PromptManager fails
        formatted_prompt = (
            "You are an expert HR evaluator. Score the candidate's resume against the job description.\n"
            "Return a strict JSON object with keys: score (0-100 float), reasoning (string).\n\n"
            "Job Description:\n{jd}\n\nResume:\n{resume}\n\nJSON:" 
        ).format(jd=job_description_text, resume=resume_text)

    for _ in range(3):
        try:
            res = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "You output JSON only."},
                    {"role": "user", "content": formatted_prompt},
                ],
                response_format={"type": "json_object"},
                temperature=0.0,
                seed=42,
            )
            content = res.choices[0].message.content
            data = json.loads(content)
            score = float(data.get("score", 0.0))
            return max(0.0, min(100.0, score))
        except Exception as e:
            # print(f"DEBUG: Error in compute_score: {e}")
            time.sleep(1.5)
    return 0.0


