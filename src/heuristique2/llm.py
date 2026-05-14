import os
import re
import time

from google import genai

MODEL = 'gemini-2.5-flash-lite'
MAX_RETRIES = 3

def init_gemini():
    api_key = os.environ.get('GEMINI_API_KEY')
    if not api_key or api_key == 'your_api_key_here':
        raise EnvironmentError("GEMINI_API_KEY manquante dans .env")
    return genai.Client(api_key=api_key)

def extract_function(text):
    """Extrait le bloc de code Python (def heuristic_score...) de la réponse du LLM."""
    match = re.search(r'```python\s*(def\s+heuristic_score.*?)\s*```', text, re.DOTALL)
    if match:
        return match.group(1).strip()
    # Fallback for when the LLM doesn't use markdown
    match = re.search(r'(def\s+heuristic_score.*)', text, re.DOTALL)
    if match:
        return match.group(1).strip()
    return None

def _parse_retry_delay(error_message):
    match = re.search(r'retry in (\d+)', str(error_message))
    return int(match.group(1)) + 15 if match else 75

def generate_score_function(client, prompt):
    """Appelle Gemini avec retry automatique sur quota 429."""
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = client.models.generate_content(
                model=MODEL,
                contents=prompt,
            )
            return extract_function(response.text)
        except Exception as e:
            error_str = str(e)
            if '429' in error_str or 'quota' in error_str.lower():
                delay = _parse_retry_delay(error_str)
                print(f"[LLM] Quota atteint, attente {delay}s avant retry ({attempt}/{MAX_RETRIES})...")
                time.sleep(delay)
            else:
                print(f"[LLM] Erreur : {e}")
                return None
    print(f"[LLM] Échec après {MAX_RETRIES} tentatives.")
    return None
