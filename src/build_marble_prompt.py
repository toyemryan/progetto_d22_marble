"""
build_marble_prompt.py — Assemblaggio del meta-prompt e chiamata a Llama.

Questo modulo:
1. Riceve il caso normalizzato, il profilo di fusione e il contesto cardinale
2. Carica il meta-prompt base
3. Inietta i dati nel meta-prompt
4. Invia tutto a Llama (via Ollama)
5. Parsa la risposta JSON di Llama
6. Salva il risultato in marble_prompts.json
"""

import json
import os
import requests
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROMPTS_DIR = os.path.join(BASE_DIR, "prompts")
DATA_DIR = os.path.join(BASE_DIR, "data")
META_PROMPT_PATH = os.path.join(PROMPTS_DIR, "meta_prompt_base.txt")
MARBLE_PROMPTS_PATH = os.path.join(DATA_DIR, "marble_prompts.json")

# Configurazione Ollama
OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "llama3"  # Cambiare se necessario (llama3:8b, llama3:70b, etc.)


def load_meta_prompt():
    with open(META_PROMPT_PATH, "r", encoding="utf-8") as f:
        return f.read()


def load_marble_prompts():
    if os.path.exists(MARBLE_PROMPTS_PATH):
        with open(MARBLE_PROMPTS_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def save_marble_prompts(prompts):
    with open(MARBLE_PROMPTS_PATH, "w", encoding="utf-8") as f:
        json.dump(prompts, f, indent=2, ensure_ascii=False)


def next_prompt_id(prompts):
    if not prompts:
        return "prompt_001"
    last_id = max(int(p["prompt_id"].split("_")[1]) for p in prompts)
    return f"prompt_{last_id + 1:03d}"


def build_llama_prompt(normalized_case, fusion_profile, cardinal_context):
    """
    Assembla il prompt finale per Llama combinando
    meta-prompt + dati del caso.
    """
    meta = load_meta_prompt()

    # Inietta i dati nel meta-prompt
    filled = meta.format(
        stimulus=normalized_case["stimulus"],
        priming_emotion=json.dumps(normalized_case["priming_emotion"], indent=2),
        realtime_face_emotion=json.dumps(normalized_case["realtime_face_emotion"], indent=2),
        user_message=normalized_case["user_message"],
        fusion_profile=json.dumps(fusion_profile, indent=2),
    )

    # Aggiungi il contesto del punto cardinale come istruzione aggiuntiva
    cardinal_hint = cardinal_context.get("hint", "")
    if cardinal_context.get("pattern_matches"):
        patterns_info = json.dumps(cardinal_context["pattern_matches"], indent=2)
        filled += f"\n\nCARDINAL POINT HINTS:\n{cardinal_hint}\nMatched patterns:\n{patterns_info}"
    else:
        filled += f"\n\nCARDINAL POINT HINTS:\n{cardinal_hint}"

    return filled


def call_llama(prompt):
    """
    Chiama Llama tramite Ollama API.
    Restituisce la risposta come stringa.
    """
    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.7,
            "num_predict": 2048,
        },
    }

    try:
        response = requests.post(OLLAMA_URL, json=payload, timeout=120)
        response.raise_for_status()
        return response.json().get("response", "")
    except requests.ConnectionError:
        print("❌ Errore: Ollama non è in esecuzione.")
        print("   Avvia Ollama con: ollama serve")
        print(f"   Poi scarica il modello con: ollama pull {OLLAMA_MODEL}")
        return None
    except requests.Timeout:
        print("❌ Errore: Timeout nella risposta di Llama.")
        return None
    except Exception as e:
        print(f"❌ Errore nella chiamata a Llama: {e}")
        return None


def parse_llama_response(response_text):
    """
    Parsa la risposta di Llama, cercando il JSON nella risposta.
    Llama potrebbe aggiungere testo prima/dopo il JSON.
    """
    if not response_text:
        return None

    # Cerca un blocco JSON nella risposta
    try:
        # Prova a parsare direttamente
        return json.loads(response_text)
    except json.JSONDecodeError:
        pass

    # Cerca JSON tra parentesi graffe
    start = response_text.find("{")
    end = response_text.rfind("}") + 1
    if start >= 0 and end > start:
        try:
            return json.loads(response_text[start:end])
        except json.JSONDecodeError:
            pass

    print("⚠ Impossibile parsare la risposta JSON di Llama.")
    print("  Risposta grezza salvata come testo.")
    return {"raw_response": response_text}


def generate_marble_prompt(normalized_case, fusion_profile, cardinal_context):
    """
    Funzione principale: assembla, chiama Llama, salva il risultato.

    Input:  caso normalizzato + profilo fusione + contesto cardinale
    Output: dict con runtime_analysis + marble_prompt + metadata
    """
    # 1. Assembla il prompt per Llama
    llama_prompt = build_llama_prompt(normalized_case, fusion_profile, cardinal_context)

    # 2. Chiama Llama
    print(f"\n🔄 Invio a Llama ({OLLAMA_MODEL})...")
    raw_response = call_llama(llama_prompt)

    if raw_response is None:
        return None

    # 3. Parsa la risposta
    parsed = parse_llama_response(raw_response)

    # 4. Costruisci il risultato con metadata
    prompts = load_marble_prompts()
    result = {
        "prompt_id": next_prompt_id(prompts),
        "case_id": normalized_case["case_id"],
        "timestamp": datetime.now().isoformat(),
        "model_used": OLLAMA_MODEL,
        "fusion_profile": fusion_profile,
        "cardinal_context_hint": cardinal_context.get("hint", ""),
        **parsed,
    }

    # 5. Salva nell'array
    prompts.append(result)
    save_marble_prompts(prompts)

    print(f"✓ Prompt {result['prompt_id']} generato e salvato.")
    return result


if __name__ == "__main__":
    from parse_cases import parse_and_normalize
    from emotion_fusion import fuse_emotions
    from cardinal_point import prepare_cardinal_context

    case = parse_and_normalize()
    profile = fuse_emotions(case)
    cardinal = prepare_cardinal_context(case, profile)
    result = generate_marble_prompt(case, profile, cardinal)

    if result:
        print(json.dumps(result, indent=2, ensure_ascii=False))
