import asyncio
from datetime import datetime
import json
import os
from utils.async_utils import call_with_spinner
from vpn_utils.vpn import vpn_tunnel
from deepeval.test_case import LLMTestCase
from OllamaEvaluator import OllamaJudgeMetric, EVALUATION_MODEL
from utils.file_utils import load_from_file
from typing import Callable
from itertools import combinations

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
PROMPTS_DIR = os.path.join(BASE_DIR, "prompts")
MARBLE_PROMPTS_PATH = os.path.join(DATA_DIR, "marble_prompts.json")
EVAL_REPORT_PATH = os.path.join(DATA_DIR, "evaluation_report.json")
CRITERIAS_PATH = os.path.join(PROMPTS_DIR, "evaluation_criterias.json")

async def evaluate_prompt(prompt, criterias: dict[str, dict] = {}) -> dict:
    id = prompt.get("prompt_id", "")
    emotion_target = prompt.get("runtime_analysis", {}).get("emotion_target", "")
    marble_prompt = prompt.get("marble_prompt", None)
    metrics = {}

    for criteria_name, criteria_config in criterias.items():
        try:
            if not marble_prompt:
                raise ValueError("marble_prompt not passed")
            if not emotion_target:
                raise ValueError("target emotion not passed")
            
            # Estrarre l'input in modo sicuro
            try:
                input_text = criteria_config["input_fn"](prompt)
            except Exception as e:
                input_text = f"Error generating input: {str(e)}"

            evaluator = OllamaJudgeMetric(
                name=criteria_name,
                criteria=criteria_config.get("criteria", ""),
                evaluation_steps=criteria_config.get("evaluation_steps", ""),
                threshold=0.6,
            )

            test_case = LLMTestCase(
                input=input_text,
                actual_output=marble_prompt
            )

            # Esegui la misurazione
            call_with_spinner(
                evaluator.measure,
                test_case,
                label=f"{EVALUATION_MODEL} sta valutando {id} su {criteria_name}..."
            )

            final_score = evaluator.score if evaluator.score is not None else None

            metrics[criteria_name] = {
                "metric": criteria_name,
                "score": final_score,
                "motivation": evaluator.reason,
                "emotion_target": emotion_target,
                "cardinal_point": get_cardinal_point(prompt)
            }
            print(f"{criteria_name}: {final_score}")
            
            #aspetta per evitare errori di sincronizzazione con ollama
            await asyncio.sleep(1)

        except Exception as e:
            metrics[criteria_name] = {
                "metric": criteria_name,
                "score": -1,
                "motivation": f"Evaluation failed: {e}",
                "emotion_target": emotion_target,
                "cardinal_point": get_cardinal_point(prompt)
            }
            print(f"Prompt {id}: Evaluation failed per {criteria_name}: {e}")

    return {
        "prompt_id": id,
        "marble_prompt": marble_prompt,
        "metrics": metrics
    }

# Funzione helper per estrarre il punto cardinale in modo sicuro
def get_cardinal_point(p):
    hint = str(p.get('cardinal_context_hint', '')).lower()
    target_phrase = "the likely cardinal point is: ".lower()
    if target_phrase in hint.lower():
        return hint.lower().split(target_phrase)[1].strip()
    return hint

def get_representatives(prompts: list | dict) -> dict[str, dict]:
    """
    Per ogni EmotionTarget restituisce il prompt con marble_prompt più lungo.
    """
    by_emotion: dict[str, list[dict]] = {}
    for p in prompts:
        emotion = p.get("runtime_analysis", {}).get("emotion_target", "")
        marble = p.get("marble_prompt", "")
        if emotion and marble:
            by_emotion.setdefault(emotion, []).append(p)

    return {
        emotion: max(group, key=lambda p: len(p.get("marble_prompt", "")))
        for emotion, group in by_emotion.items()
    }


def build_diversity_input(prompt: dict, representatives: dict[str, dict]) -> str:
    """
    Costruisce una stringa con il prompt corrente confrontato
    con tutti i rappresentativi di EmotionTarget diverse.
    """
    current_emotion = prompt.get("runtime_analysis", {}).get("emotion_target", "")
    current_marble = prompt.get("marble_prompt", "")

    comparisons = []
    for emotion, rep in representatives.items():
        if emotion == current_emotion:
            continue
        rep_marble = rep.get("marble_prompt", "")
        comparisons.append(
            f"Emotion A: {current_emotion}\nWorld A: {current_marble}\n\n"
            f"Emotion B: {emotion}\nWorld B: {rep_marble}"
        )

    return "\n\n---\n\n".join(comparisons)

async def evaluate_all():
    prompts = load_from_file(MARBLE_PROMPTS_PATH, "json")
    representatives = get_representatives(prompts)
    
    INPUT_FNS: dict[str, Callable[[dict], str]] = {
        "emotion_alignment": lambda p: f"Emotion target: {p['runtime_analysis']['emotion_target']}\n\nPrompt: {p['marble_prompt']}",
        "cardinal_alignment": lambda p: (
            f"Emotional cardinal point: {get_cardinal_point(p)}\n"
            f"Emotion target: {p['runtime_analysis'].get('emotion_target', 'N/A')}\n\n"
            f"Prompt to evaluate: {p['marble_prompt']}"
        ),
        "prompt_concreteness": lambda p: "Evaluate the visual concreteness of the following 3D world description.",
        "safety_and_ethics": lambda p: p['marble_prompt'],
        "prompt_diversity": lambda p: build_diversity_input(p, representatives)
    }

    #Caricamento dei criteri di valutazione
    criterias_raw = load_from_file(CRITERIAS_PATH, "json")
    criterias = {
        c["name"]: {
            "criteria": c["criteria"],
            "input_fn": INPUT_FNS[c["name"]],
            "evaluation_steps": c.get("evaluation_steps", None)
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
            for prompt in prompts[-5:]:
                results.append(await evaluate_prompt(prompt, criterias))
    else:
        for prompt in prompts[-5:]:
            results.append(await evaluate_prompt(prompt, criterias))

    report = {
        "evaluated_at": datetime.now().isoformat(),
        "results": results,
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