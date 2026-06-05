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

import asyncio
import json
import os
import requests
from datetime import datetime
import threading
from utils.file_utils import load_from_file
from utils.spinner import spinner
from vpn_utils.vpn import vpn_tunnel

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROMPTS_DIR = os.path.join(BASE_DIR, "prompts")
DATA_DIR = os.path.join(BASE_DIR, "data")
META_PROMPT_PATH = os.path.join(PROMPTS_DIR, "meta_prompt_v2.txt")
MARBLE_PROMPTS_PATH = os.path.join(DATA_DIR, "marble_prompts.json")

# Configurazione Ollama
OLLAMA_URL = os.getenv("OLLAMA_URL")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL")

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
    meta = load_from_file(META_PROMPT_PATH)

    # Inietta i dati nel meta-prompt (usa replace per evitare conflitti con le {} del JSON)
    filled = (meta
              .replace("{stimulus}", normalized_case["stimulus"])
              .replace("{priming_emotion}", json.dumps(normalized_case["priming_emotion"], indent=2))
              .replace("{realtime_face_emotion}", json.dumps(normalized_case["realtime_face_emotion"], indent=2))
              .replace("{user_message}", normalized_case["user_message"])
              .replace("{fusion_profile}", json.dumps(fusion_profile, indent=2))
              .replace("{emotion_target}", str(cardinal_context.get("emotion_target", "")))
    )

    # Aggiungi il contesto del punto cardinale come istruzione aggiuntiva
    cardinal_hint = cardinal_context.get("hint", "")
    if cardinal_context.get("pattern_matches"):
        patterns_info = json.dumps(cardinal_context["pattern_matches"], indent=2)
        filled += f"\n\nCARDINAL POINT HINTS:\n{cardinal_hint}\nMatched patterns:\n{patterns_info}"
    else:
        filled += f"\n\nCARDINAL POINT HINTS:\n{cardinal_hint}"

    return filled


def call_llama(prompt, label:str = "In attesa di risposta da Llama"):
    """
    Chiama Llama tramite Ollama API.
    Restituisce la risposta come stringa.
    """
    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "format": "json",
        "stream": False,
        "options": {
            "temperature": 0.7,
            "num_predict": 2048,
        },
    }

    stop_event = threading.Event()
    spinner_thread = threading.Thread(target=spinner, args=(stop_event, label))
    try:
        spinner_thread.start()

        response = requests.post(OLLAMA_URL, json=payload, timeout=180)
        response.raise_for_status()
        result = response.json().get("response", "")

        stop_event.set()
        spinner_thread.join()
        return result

    except requests.ConnectionError:
        stop_event.set()
        spinner_thread.join()
        print("❌ Errore: Ollama non è in esecuzione.")
        print("   Avvia Ollama con: ollama serve")
        print(f"   Poi scarica il modello con: ollama pull {OLLAMA_MODEL}")
        return None
    except requests.Timeout:
        stop_event.set()
        spinner_thread.join()
        print("❌ Errore: Timeout nella risposta di Llama.")
        return None
    except Exception as e:
        stop_event.set()
        spinner_thread.join()
        print(f"❌ Errore nella chiamata a Llama: {e}")
        return None


def parse_llama_response(response_text) -> dict|None:
    """
    Parsa la risposta di Llama, cercando il JSON nella risposta.
    Llama spesso aggiunge markdown, commenti, blocchi ``` attorno al JSON.
    Se il JSON non è parsabile, estrae i contenuti manualmente dal testo.
    """
    if not response_text:
        return None

    import re

    # 1. Rimuovi blocchi markdown ```json ... ``` o ``` ... ```
    cleaned = re.sub(r'```json\s*', '', response_text)
    cleaned = re.sub(r'```\s*', '', cleaned)

    # 2. Prova a parsare direttamente
    try:
        return json.loads(cleaned.strip())
    except json.JSONDecodeError:
        pass

    # 3. Cerca il JSON più grande tra parentesi graffe (nidificate)
    depth = 0
    start = -1
    best_json = None
    for i, ch in enumerate(cleaned):
        if ch == '{':
            if depth == 0:
                start = i
            depth += 1
        elif ch == '}':
            depth -= 1
            if depth == 0 and start >= 0:
                candidate = cleaned[start:i+1]
                try:
                    parsed = json.loads(candidate)
                    # Prendi il JSON più completo (con marble_prompt se possibile)
                    if best_json is None or "marble_prompt" in parsed:
                        best_json = parsed
                except json.JSONDecodeError:
                    pass
                start = -1

    if best_json:
        return best_json

    # 4. Fallback: estrai i contenuti dal testo grezzo
    print("⚠ JSON non parsabile. Estrazione manuale dal testo...")
    result = extract_from_raw_text(response_text)
    return result


def extract_from_raw_text(text):
    """
    Estrae marble_prompt, runtime_analysis, negative_constraints e variants
    dal testo grezzo di Llama quando il JSON non è valido.
    """
    import re

    result = {}

    # Estrai marble_prompt: cerca il blocco descrittivo più lungo
    # Di solito è dopo "marble_prompt" o "Marble Prompt" o "Create a/an"
    prompt_match = re.search(
        r'(?:marble_prompt["\s:]*|Marble Prompt[*\s:]*)(Create .+?)(?:\n\n(?:Variant|Negative|\*\*|```)|$)',
        text, re.DOTALL | re.IGNORECASE
    )
    if prompt_match:
        result["marble_prompt"] = prompt_match.group(1).strip().strip('"').strip("'")
    else:
        # Cerca qualsiasi paragrafo che inizia con "Create"
        create_match = re.search(r'(Create (?:a|an|the) .+?)(?:\n\n|\nVariant|\nNegative|$)', text, re.DOTALL)
        if create_match:
            result["marble_prompt"] = create_match.group(1).strip().strip('"')

    # Estrai runtime_analysis dai campi individuali
    runtime = {}
    field_patterns = {
        "dominant_emotion": r'"dominant_emotion"\s*:\s*"([^"]+)"',
        "complex_emotion": r'"complex_emotion"\s*:\s*"([^"]+)"',
        "stimulus": r'"stimulus"\s*:\s*"([^"]+)"',
        "user_reaction": r'"user_reaction"\s*:\s*"([^"]+)"',
        "cardinal_point": r'"cardinal_point"\s*:\s*"([^"]+)"',
        "world_objective": r'"world_objective"\s*:\s*"([^"]+)"',
    }
    for field, pattern in field_patterns.items():
        match = re.search(pattern, text)
        if match:
            runtime[field] = match.group(1)
    if runtime:
        result["runtime_analysis"] = runtime

    # Estrai negative constraints
    neg_matches = re.findall(r'(?:Avoid|Refrain|Do not|No )[^\n*]+', text, re.IGNORECASE)
    if neg_matches:
        result["negative_constraints"] = [n.strip().strip('*').strip() for n in neg_matches]

    # Estrai variants
    variant_matches = re.findall(
        r'\*\*([^*]+)\*\*:\s*([^\n]+(?:\n(?!\*\*|\n)[^\n]+)*)',
        text
    )
    if variant_matches:
        result["variants"] = [
            f"{name.strip()}: {desc.strip()}" for name, desc in variant_matches
        ]

    if not result:
        result["raw_response"] = text

    return result


async def generate_marble_prompt(normalized_case, fusion_profile, cardinal_context, start_vpn = False):
    """
    Funzione principale: assembla, chiama Llama, salva il risultato.

    Input:  caso normalizzato + profilo fusione + contesto cardinale
    Output: dict con runtime_analysis + marble_prompt + metadata
    """

    if start_vpn:
        async with vpn_tunnel():
            result = await generate_marble_prompt(normalized_case, fusion_profile, cardinal_context)
            return result

    # 1. Assembla il prompt per Llama
    llama_prompt = build_llama_prompt(normalized_case, fusion_profile, cardinal_context)

    # 2. Chiama Llama
    print(f"\n🔄 Invio a Llama ({OLLAMA_MODEL})...")
    raw_response = call_llama(llama_prompt)

    if raw_response is None:
        return None

    # 3. Parsa la risposta
    parsed = parse_llama_response(raw_response)
    if not parsed:
        parsed = {}

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
    result = asyncio.run(generate_marble_prompt(case, profile, cardinal))

    if result:
        print(json.dumps(result, indent=2, ensure_ascii=False))
