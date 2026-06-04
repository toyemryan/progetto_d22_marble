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
from utils.file_utils import load_from_file
from vpn_utils.vpn import vpn_tunnel

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
PROMPTS_DIR = os.path.join(BASE_DIR, "prompts")
MARBLE_PROMPTS_PATH = os.path.join(DATA_DIR, "marble_prompts.json")
EVAL_REPORT_PATH = os.path.join(DATA_DIR, "evaluation_report.json")
EMOTION_PROMPT_PATH = os.path.join(PROMPTS_DIR, "emotion_alignment_prompt.txt")

REFERENCE_PROMPT_3 = """Imagine yourself standing at the edge of a serene lake, 
surrounded by the gentle rustling of trees and the soft warmth of golden sunlight. 
The air is filled with the sweet scent of blooming flowers as far as the eye can see. 
In the distance, a faint mist rises from the water's surface, carrying the whispers 
of past triumphs. The sound of gentle lapping waves against the shore creates a soothing 
melody that calms the mind and heart. As you walk along the lake's edge, the soft grass 
beneath your feet and the warmth of the sun on your skin evoke feelings of comfort and 
gratitude for life's simple pleasures. A delicate wooden boat glides across the water, 
its gentle rocking motion echoing the rhythm of your heartbeat. In this peaceful sanctuary, 
the weight of disappointment slowly lifts, replaced by a sense of nostalgia and appreciation 
for the beauty that surrounds you."""

REFERENCE_PROMPT_3_REASON = """scores 3 because it evokes a generic emotional warmth 
but completely ignores the visual stimulus (Italy 2006 World Cup stadium) — 
the world is a lake with no connection to football, crowds, or jerseys. 
The cardinal point is absent."""

OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "llama3"

async def evaluate_emotion_alignment(prompt_entry: dict, prompt_3_ex: dict, last_eval: dict) -> dict:
    """
    Valuta se il prompt Marble comunica l'emozione target.
    Restituisce un dizionario con score 1-5 e motivazione.
    """
    if last_eval is None:
        last_eval = prompt_3_ex
    
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
                  .replace("{cardinal_point}", cardinal_point)
                  .replace("{reference_prompt_3}", prompt_3_ex["prompt"])
                  .replace("{reference_prompt_3_reason}", prompt_3_ex["motivation"])
                  .replace("{last_prompt}", last_eval["prompt"])
                  .replace("{last_score}", str(last_eval["score"]))
                  .replace("{last_motivation}", last_eval["motivation"])
        )

        result = call_llama(prompt)

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

async def evaluate_prompt(prompt_entry, last_eval) -> dict:
    """Valuta un singolo prompt su tutti i criteri singolari."""
    example_3 = {"prompt": REFERENCE_PROMPT_3,
                 "score": "3",
                 "motivation": REFERENCE_PROMPT_3_REASON
    }
    metrics = {
        "emotion_alignment": await evaluate_emotion_alignment(prompt_entry, example_3, last_eval),
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
                result = await evaluate_prompt(
                    entry, 
                    last_eval=last_eval,
                )
                last_eval = {
                    "prompt": entry.get("marble_prompt", ""),
                    "score": result["metrics"]["emotion_alignment"]["score"],
                    "motivation": result["metrics"]["emotion_alignment"]["motivation"]
                }
                
                results.append(result)

                # Stampa riepilogo
                pid = result["prompt_id"]
                emo_ali = result["metrics"]["emotion_alignment"]

                print(f"ID: {pid}")
                print(f"emotion alignment: {emo_ali}")

    # Salva report
    with open(EVAL_REPORT_PATH, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"\n✓ Report salvato in {EVAL_REPORT_PATH}")
    return results


if __name__ == "__main__":
    asyncio.run(evaluate_all())
