import os
import json
import time
from openai import OpenAI, RateLimitError
from dotenv import load_dotenv
from typing import Optional, Dict

load_dotenv()

# We simplify this to just use a hardcoded default prompt to avoid complex dependency on 'backend.prompt_manager' 
# in this isolated microservice context, OR we can try to read the file if present.
# For robustness, we will use a fallback prompt here.

LLM_MODEL = "openai/gpt-oss-20b:fireworks-ai"

DEFAULT_PARSING_PROMPT = """
You are an expert HR assistant. Your task is to extract structured information from a job description.
Output a JSON object with the following fields:
- job_title: str
- company: str
- location: str
- employment_type: str (e.g. Full-time, Contract)
- experience_level: str
- educational_requirements: str
- summary: str (2-3 sentences)
- responsibilities: list[str]
- requirements: list[str]
- skills: list[str]
- salary_range: str (optional) or null

Ensure the JSON is valid. Do not output any markdown code blocks.
"""

def _get_openai_client() -> OpenAI:
    hf_token = os.environ.get("HF_TOKEN")
    if not hf_token:
        print("Warning: HF_TOKEN environment variable not set. LLM parsing will fail.")
        return None
    return OpenAI(
        base_url="https://router.huggingface.co/v1",
        api_key=hf_token,
        timeout=60.0,
    )

def _parse_with_llm(text: str, prompt: str, retries: int = 3) -> Optional[Dict]:
    if not text or not prompt:
        return None
    
    client = _get_openai_client()
    if not client:
        return None
        
    full_prompt = f"{prompt}\n\n---\nJob Description:\n{text}\n---\nJSON Output:"
    
    delay_seconds = 1
    for _ in range(retries):
        try:
            res = client.chat.completions.create(
                model=LLM_MODEL,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant designed to output JSON."},
                    {"role": "user", "content": full_prompt},
                ],
                response_format={"type": "json_object"},
            )
            content = res.choices[0].message.content
            # Clean up markdown if present
            if content.startswith("```json"):
                content = content[7:]
            if content.endswith("```"):
                content = content[:-3]
            return json.loads(content)
        except Exception as exc:
            print(f"Error parsing LLM: {exc}")
            time.sleep(delay_seconds)
            delay_seconds *= 2
    return None

def parse_job_description_from_text(job_description_text: str) -> Dict:
    """Return parsed job profile as dict from text input."""
    if not job_description_text or not job_description_text.strip():
        raise ValueError("Job description text cannot be empty")

    structured_profile = _parse_with_llm(job_description_text.strip(), DEFAULT_PARSING_PROMPT)
    
    if not structured_profile:
        # Fallback if LLM fails
        return {
            "job_title": "Unknown Title",
            "summary": job_description_text[:200] + "...",
            "description": job_description_text
        }

    return structured_profile
