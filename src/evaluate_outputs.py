"""
evaluate_outputs.py — Valutazione dei prompt Marble generati.

Criteri (dalla sezione 10.1):
- Emotion alignment: il prompt comunica l'emozione target?
- Cardinal alignment: il mondo ridireziona verso il punto cardinale?
- Prompt concreteness: contiene elementi visivi generabili?
- Safety: non menziona sensori/biometria?
"""
import asyncio
from datetime import datetime
import json
import os
from time import sleep
from utils.async_utils import call_with_spinner
from vpn_utils.vpn import vpn_tunnel
from deepeval.metrics import GEval
from deepeval.test_case import LLMTestCase, SingleTurnParams
from deepeval.models import OllamaModel
from utils.file_utils import load_from_file
from typing import Callable, cast

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
PROMPTS_DIR = os.path.join(BASE_DIR, "prompts")
MARBLE_PROMPTS_PATH = os.path.join(DATA_DIR, "marble_prompts.json")
EVAL_REPORT_PATH = os.path.join(DATA_DIR, "evaluation_report.json")
CRITERIAS_PATH = os.path.join(PROMPTS_DIR, "evaluation_criterias.json")

EVALUATION_MODEL = os.getenv("OLLAMA_MODEL", "qwen3")

async def evaluate_prompt(prompt, criterias: dict[str, dict[str, str | Callable]] = {}) -> dict:
    id = None
    metrics = {}

    try:
        id = prompt.get("prompt_id", "")
        emotion_target = prompt.get("runtime_analysis", {}).get("emotion_target", "")
        marble_prompt = prompt.get("marble_prompt", "")

        if not emotion_target:
            raise ValueError("target emotion not passed")

        judge = OllamaModel(model=EVALUATION_MODEL)

        for criteria_name, criteria_config in criterias.items():
            try:
                evaluator = GEval(
                    name=criteria_name,
                    criteria=str(criteria_config["criteria"]),
                    evaluation_params=[
                        SingleTurnParams.INPUT,
                        SingleTurnParams.ACTUAL_OUTPUT
                    ],
                    model=judge,
                    threshold=0.6,
                )

                test_case = LLMTestCase(
                    input=criteria_config["input_fn"](prompt), # type: ignore
                    actual_output=marble_prompt
                )

                call_with_spinner(
                    evaluator.measure,
                    test_case,
                    _show_indicator=False,
                    label=f"{EVALUATION_MODEL} sta valutando {id} su {criteria_name}..."
                )

                metrics[criteria_name] = {
                    "metric": criteria_name,
                    "score": evaluator.score * 5 if evaluator.score is not None else None,
                    "motivation": evaluator.reason,
                    "emotion_target": emotion_target
                }
                print(f"{criteria_name}: {evaluator.score * 5 if evaluator.score is not None else None}")

            except Exception as e:
                metrics[criteria_name] = {
                    "metric": criteria_name,
                    "score": -1,
                    "motivation": f"Evaluation failed: {e}",
                    "emotion_target": emotion_target
                }
                print(f"Evaluation failed: {e}")

            

    except Exception as e:
        return {
            "prompt_id": id,
            "metrics": {
                name: {
                    "metric": name,
                    "score": -1,
                    "motivation": f"Evaluation failed: {e}",
                    "emotion_target": ""
                } for name in criterias.keys()
            }
        }

    return {
        "prompt_id": id,
        "metrics": metrics
    }

async def evaluate_all():
    prompts = load_from_file(MARBLE_PROMPTS_PATH, "json")
    
    INPUT_FNS: dict[str, Callable[[dict], str]] = {
        "emotion_alignment": lambda p: f"Emotion target: {p['runtime_analysis']['emotion_target']}\n\nPrompt: {p['marble_prompt']}",
        "cardinal_alignment": lambda p: f"Cardinal point: {str(p['cardinal_context_hint']).lower().split("the likely cardinal point is: ")[1]}\n\nPrompt: {p['marble_prompt']}",
        "prompt_concreteness": lambda p: "Evaluate the visual concreteness of the following 3D world description.",
        "safety_and_ethics": lambda p: p['marble_prompt'],
        "marble_usability": lambda p: p['marble_prompt'],
    }

    # Carica il JSON contenenti i criteri e crea i dizionari dei criteri
    criterias_raw = load_from_file(CRITERIAS_PATH, "json")
    criterias = {
        c["name"]: {
            "criteria": c["criteria"],
            "input_fn": INPUT_FNS[c["name"]]
        }
        for c in criterias_raw
        if c["name"] in INPUT_FNS
    }

    if not prompts:
        print("Nessun prompt da valutare.")
        return []
    
    results = []
    if os.getenv("CONNECT_TO_REMOTE", "").lower() == "true":
        async with vpn_tunnel():
            for prompt in prompts[-1:]:
                results.append(await evaluate_prompt(prompt, criterias))
    else:
        for prompt in prompts[-1:]:
            results.append(await evaluate_prompt(prompt, criterias))
    
    # Salva report
    report = {
        "evaluated_at": datetime.now().isoformat(),
        "results": results
    }
    with open(EVAL_REPORT_PATH, "w", encoding="utf-8") as f:
        print("Saving the report...")
        json.dump(report, f, indent=2, ensure_ascii=False)

    print("Report saved")
                    

if __name__ == "__main__":
    try:
        asyncio.run(evaluate_all())
    finally:
        os._exit(0)
