"""
evaluate_outputs.py — Valutazione dei prompt Marble generati.

Criteri (dalla sezione 10.1):
- Emotion alignment: il prompt comunica l'emozione target?
- Cardinal alignment: il mondo ridireziona verso il punto cardinale?
- Prompt concreteness: contiene elementi visivi generabili?
- Safety: non menziona sensori/biometria?
"""

import json
import os
import requests

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
MARBLE_PROMPTS_PATH = os.path.join(DATA_DIR, "marble_prompts.json")
EVAL_REPORT_PATH = os.path.join(DATA_DIR, "evaluation_report.json")

OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "llama3"

# Checklist concreteness (sezione 10.1)
CONCRETENESS_KEYWORDS = [
    "environment", "landscape", "space", "room", "world",
    "light", "lighting", "glow", "shadow", "sun",
    "color", "colour", "palette", "hue", "tone",
    "material", "texture", "surface", "stone", "glass", "wood",
    "object", "element", "tree", "water", "path", "door",
    "atmosphere", "mood", "feeling",
]

# Parole vietate (sezione Appendice C)
FORBIDDEN_WORDS = [
    "facereader", "noldus", "sensor", "biometric", "webcam",
    "facial data", "face detection", "camera", "tracking",
]


def load_marble_prompts():
    with open(MARBLE_PROMPTS_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def check_concreteness(prompt_text):
    """
    Verifica se il prompt contiene elementi visivi concreti.
    Restituisce un punteggio 0-1 e la lista di elementi trovati.
    """
    if not prompt_text:
        return 0.0, []

    text_lower = prompt_text.lower()
    found = [kw for kw in CONCRETENESS_KEYWORDS if kw in text_lower]
    score = min(len(found) / 8.0, 1.0)  # 8+ keywords = punteggio pieno
    return round(score, 2), found


def check_safety(prompt_text):
    """
    Verifica che il prompt non menzioni sensori o dati biometrici.
    """
    if not prompt_text:
        return True, []

    text_lower = prompt_text.lower()
    violations = [fw for fw in FORBIDDEN_WORDS if fw in text_lower]
    return len(violations) == 0, violations


def evaluate_with_llama(prompt_entry):
    """
    Usa Llama come LLM-as-a-judge per valutare
    emotion alignment e cardinal alignment.
    """
    marble_prompt = prompt_entry.get("marble_prompt", "")
    runtime = prompt_entry.get("runtime_analysis", {})
    fusion = prompt_entry.get("fusion_profile", {})

    eval_prompt = f"""You are an evaluator for emotion-aware 3D world prompts.

Evaluate the following Marble prompt on two criteria, scoring each 1-5:

1. EMOTION ALIGNMENT: Does the prompt effectively communicate the target emotion?
   Target emotion: {fusion.get('dominant_emotion', 'unknown')}
   
2. CARDINAL ALIGNMENT: Does the world redirect toward the identified cardinal point?
   Cardinal point: {runtime.get('cardinal_point', 'unknown')}

MARBLE PROMPT:
{marble_prompt}

Respond ONLY in JSON format:
{{
  "emotion_alignment_score": <1-5>,
  "emotion_alignment_reason": "<brief explanation>",
  "cardinal_alignment_score": <1-5>,
  "cardinal_alignment_reason": "<brief explanation>"
}}"""

    try:
        response = requests.post(
            OLLAMA_URL,
            json={"model": OLLAMA_MODEL, "prompt": eval_prompt, "stream": False},
            timeout=90,
        )
        text = response.json().get("response", "")
        start = text.find("{")
        end = text.rfind("}") + 1
        if start >= 0 and end > start:
            return json.loads(text[start:end])
    except Exception as e:
        print(f"  ⚠ Valutazione LLM fallita: {e}")

    return None


def evaluate_prompt(prompt_entry):
    """Valuta un singolo prompt su tutti i criteri."""
    marble_prompt = prompt_entry.get("marble_prompt", "")

    # Concreteness
    concrete_score, concrete_elements = check_concreteness(marble_prompt)

    # Safety
    is_safe, violations = check_safety(marble_prompt)

    # LLM evaluation
    print(f"  🔄 Valutazione LLM per {prompt_entry.get('prompt_id', '?')}...")
    llm_eval = evaluate_with_llama(prompt_entry)

    return {
        "prompt_id": prompt_entry.get("prompt_id"),
        "case_id": prompt_entry.get("case_id"),
        "concreteness": {
            "score": concrete_score,
            "elements_found": concrete_elements,
        },
        "safety": {
            "passed": is_safe,
            "violations": violations,
        },
        "llm_evaluation": llm_eval,
    }


def evaluate_all():
    """Valuta tutti i prompt in marble_prompts.json."""
    prompts = load_marble_prompts()

    if not prompts:
        print("Nessun prompt da valutare.")
        return []

    print(f"\n📊 Valutazione di {len(prompts)} prompt...\n")
    results = []

    for entry in prompts:
        result = evaluate_prompt(entry)
        results.append(result)

        # Stampa riepilogo
        pid = result["prompt_id"]
        cs = result["concreteness"]["score"]
        safe = "✓" if result["safety"]["passed"] else "✗"
        llm = result.get("llm_evaluation")
        ea = llm.get("emotion_alignment_score", "?") if llm else "?"
        ca = llm.get("cardinal_alignment_score", "?") if llm else "?"
        print(f"  {pid}: concreteness={cs} safety={safe} emotion={ea}/5 cardinal={ca}/5")

    # Salva report
    with open(EVAL_REPORT_PATH, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"\n✓ Report salvato in {EVAL_REPORT_PATH}")
    return results


if __name__ == "__main__":
    evaluate_all()
