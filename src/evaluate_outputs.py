"""
evaluate_outputs.py — Valutazione dei prompt Marble generati.

Criteri (dalla sezione 10.1):
- Emotion alignment: il prompt comunica l'emozione target?
- Cardinal alignment: il mondo ridireziona verso il punto cardinale?
- Prompt concreteness: contiene elementi visivi generabili?
- Safety: non menziona sensori/biometria?
"""

import asyncio
import json
import os
from build_marble_prompt import call_llama
from config.emotions import EmotionTarget
from config.evualuate_expr import *
from utils.file_utils import load_from_file
from vpn_utils.vpn import vpn_tunnel
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
PROMPTS_DIR = os.path.join(BASE_DIR, "prompts")
MARBLE_PROMPTS_PATH = os.path.join(DATA_DIR, "marble_prompts.json")
EVAL_REPORT_PATH = os.path.join(DATA_DIR, "evaluation_report.json")
EMOTION_PROMPT_PATH = os.path.join(PROMPTS_DIR, "emotion_alignment_prompt.txt")
CARDINAL_PROMPT_PATH = os.path.join(PROMPTS_DIR, "cardinal_alignment_prompt.txt")

OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "llama3"

async def evaluate_emotion_alignment(prompt_entry: dict, example: dict, last_eval: dict) -> dict:
    """
    Valuta se il prompt Marble comunica l'emozione target.
    Restituisce un dizionario con score 1-5 e motivazione.
    """
    if last_eval is None:
        last_eval = {
            "prompt": example["prompt"],
            "metrics":{
                "emotion_alignment":{
                    "motivation": example["motivation"],
                    "score": 1
                }
            }
        }
    
    emotion_target = None
    marble_prompt = None
    cardinal_point = None

    try:
        marble_prompt = prompt_entry.get("marble_prompt", "")
        emotion_target = prompt_entry.get("runtime_analysis", "").get("emotion_target", "")
        cardinal_point = prompt_entry.get("cardinal_context_hint", "")

        if not emotion_target or emotion_target == "":
            raise ValueError("target emotion not passed")
        prompt = (load_from_file(EMOTION_PROMPT_PATH)
                  .replace('{marble_prompt}', marble_prompt)
                  .replace("{emotion_target}", str(emotion_target))
                  .replace("{reference_prompt_1}", example["prompt"])
                  .replace("{reference_prompt_1_reason}", example["motivation"])
                  .replace("{last_prompt}", last_eval["prompt"])
                  .replace("{last_score}", str(last_eval["metrics"]["emotion_alignment"]["score"]))
                  .replace("{last_motivation}", last_eval["metrics"]["emotion_alignment"]["motivation"])
        )

        result = call_llama(prompt, "Valutazione allineamento all'emozione target")

        if not result:
            raise ValueError("Llama returned None or empty response")

        parsed = json.loads(str(result).strip())
        return {
            "metric": "emotion_alignment",
            "score": int(parsed["score"]),
            "motivation": parsed["motivation"],
            "relative_position": parsed["relative_position"],
            "best_element": parsed["best_element"],
            "weakness": parsed["weakness"],
            "emotion_target": emotion_target,
            "cardinal_point": cardinal_point
        }

    except Exception as e:
        print(f"[evaluate_emotion_alignment] failed: {e}")
        return {
            "metric": "emotion_alignment",
            "score": -1,
            "motivation": f"Evaluation failed: {e}",
            "emotion_target": str(emotion_target),
            "cardinal_point": str(cardinal_point),
        }

async def evaluate_cardinal_alignment(prompt_entry: dict, example: dict, last_eval: dict) -> dict:
    """
    Valuta se il prompt Marble ridireziona il mondo visivo verso il cardinal point,
    ovvero se comunica una transizione emotiva da uno stato di partenza verso uno di arrivo.
    Restituisce un dizionario con score 1-5 e motivazione.
    Skippa i prompt senza una transizione valida nel cardinal_context_hint.
    """
    if last_eval is None:
        last_eval = {
            "prompt": example["prompt_1"],
            "metrics":{
                "cardinal_alignment":{
                    "motivation": example["motivation_1"],
                    "score": 1
                }
            }
        }
                     

    cardinal_point = None
    emotion_target = None
    cardinal_hint = None

    try:
        marble_prompt = prompt_entry.get("marble_prompt", "")
        cardinal_hint = prompt_entry.get("cardinal_context_hint", "")
        cardinal_point = str(cardinal_hint).lower().split("the likely cardinal point is: ")[1] #cardinal hint is:"the likely cardinal point is: {cardinal_point}"
        emotion_target = prompt_entry.get("runtime_analysis", {}).get("emotion_target", "")

        if cardinal_point is None:
            raise ValueError(f"Skipped: cardinal_context_hint does not express a transition — '{cardinal_hint}'")
        if not ("from" in str(cardinal_point).lower() and "toward" in str(cardinal_point).lower()):
            raise ValueError(f"Skipped: cardinal_point has not a correct format")

        prompt = (load_from_file(CARDINAL_PROMPT_PATH)
                  .replace("{marble_prompt}", marble_prompt)
                  .replace("{cardinal_point}", cardinal_point)
                  .replace("{reference_prompt_1}", example["prompt_1"])
                  .replace("{reference_prompt_1_reason}", example["motivation_1"])
                  .replace("{reference_prompt_2}", example["prompt_2"])
                  .replace("{reference_prompt_2_reason}", example["motivation_2"])
                  .replace("{last_prompt}", last_eval["prompt"])
                  .replace("{last_score}", str(last_eval["metrics"]["cardinal_alignment"]["score"]))
                  .replace("{last_motivation}", last_eval["metrics"]["cardinal_alignment"]["motivation"])
        )

        result = call_llama(prompt, "Valutazione allineamento al punto cardinale")

        if not result:
            raise ValueError("Llama returned None or empty response")

        parsed = json.loads(str(result).strip())
        return {
            "metric": "cardinal_alignment",
            "score": int(parsed["score"]),
            "motivation": parsed["motivation"],
            "relative_position": parsed["relative_position"],
            "transition_from": parsed["transition_from"],
            "transition_to": parsed["transition_to"],
            "best_element": parsed["best_element"],
            "weakness": parsed["weakness"],
            "cardinal_point": cardinal_point,
            "emotion_target": str(emotion_target)
        }

    except Exception as e:
        print(f"[evaluate_cardinal_alignment] failed: {e}")
        return {
            "metric": "cardinal_alignment",
            "score": -1,
            "motivation": f"Evaluation failed: {e}",
            "cardinal_point": str(cardinal_point),
            "cardinal_hint": str(cardinal_hint),
            "emotion_target": str(emotion_target)
        }

async def evaluate_prompt(prompt_entry, last_eval) -> dict:
    """Valuta un singolo prompt su tutti i criteri singolari."""
    emotion_example = {"prompt": EMOTION_REFERENCE_PROMPT,
                 "motivation": EMOTION_REFERENCE_PROMPT_REASON
    }
    cardinal_example =  {"prompt_1": CARDINAL_REFERENCE_PROMPT_1,
                 "motivation_1": CARDINAL_REFERENCE_PROMPT_1_REASON,
                 "prompt_2": CARDINAL_REFERENCE_PROMPT_2,
                 "motivation_2": CARDINAL_REFERENCE_PROMPT_2_REASON
    }
    metrics = {
        "emotion_alignment": await evaluate_emotion_alignment(prompt_entry, emotion_example, last_eval),
        "cardinal_alignment": await evaluate_cardinal_alignment(prompt_entry, cardinal_example, last_eval)
    }
    return {
        "prompt_id": prompt_entry.get("prompt_id", ""),
        "metrics": metrics
    }

async def evaluate_all():
    """Valuta tutti i prompt in marble_prompts.json."""
    prompts = load_from_file(MARBLE_PROMPTS_PATH, "json")

    if not prompts:
        print("Nessun prompt da valutare.")
        return []
    
    last_eval = None

    print(f"\n📊 Valutazione di {len(prompts)} prompt...\n")
    results = []
    if os.getenv("CONNECT_TO_REMOTE", "").lower() == "true":
        async with vpn_tunnel():
            for entry in prompts:
                pid = entry.get("prompt_id", "") # type: ignore
                print(f"ID: {pid}")
                result = await evaluate_prompt(
                    entry, 
                    last_eval=last_eval,
                )
                last_eval = {
                    "prompt": entry.get("marble_prompt", ""), # type: ignore
                    "metrics": result["metrics"],
                }
                
                results.append(result)

                # Stampa riepilogo
                emo_ali = result["metrics"]["emotion_alignment"]["score"]
                print(f"emotion alignment: {emo_ali}")
                card_ali = result["metrics"]["cardinal_alignment"]
                print(f"cardinal alignment: {card_ali}")

    # Salva report
    report = {
        "evaluated_at": datetime.now().isoformat(),
        "results": results
    }
    with open(EVAL_REPORT_PATH, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print(f"\n✓ Report salvato in {EVAL_REPORT_PATH}")
    return results


if __name__ == "__main__":
    asyncio.run(evaluate_all())
