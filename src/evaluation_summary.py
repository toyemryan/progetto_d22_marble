"""
evaluation_summary.py — Calcola media e deviazione standard
per ogni metrica di valutazione, leggendo tutti i report esistenti.
Salva il risultato in data/evaluation_summary.json.
"""

import json
import os
import numpy as np
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
EVAL_REPORT_PATH = os.path.join(DATA_DIR, "evaluation_report.json")
SUMMARY_PATH = os.path.join(DATA_DIR, "evaluation_summary.json")


def load_evaluation_reports():
    if os.path.exists(EVAL_REPORT_PATH):
        with open(EVAL_REPORT_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def compute_and_save_summary():
    """
    Legge tutti i report da evaluation_report.json,
    calcola media e deviazione standard per ogni metrica,
    e salva in evaluation_summary.json.
    """
    reports = load_evaluation_reports()

    all_scores: dict[str, list[float]] = {}

    for report in reports:
        results = report.get("results", [])
        # results può essere un dict (evaluate_single) o una lista (evaluate_all)
        if isinstance(results, dict):
            results = [results]
        for entry in results:
            # Filtra: solo prompt_020 in poi (i precedenti sono test di sviluppo)
            prompt_id = entry.get("prompt_id", "")
            try:
                num = int(prompt_id.split("_")[1])
                if num < 20:
                    continue
            except (IndexError, ValueError):
                continue

            for metric_name, metric_data in entry.get("metrics", {}).items():
                score = metric_data.get("score", -1)
                if score >= 0:
                    all_scores.setdefault(metric_name, []).append(score)

    summary = {}
    for metric_name, scores in all_scores.items():
        summary[metric_name] = {
            "media": round(float(np.mean(scores)), 3),
            "deviazione_standard": round(float(np.std(scores)), 3),
            "n_campioni": len(scores),
            "min": round(float(np.min(scores)), 3),
            "max": round(float(np.max(scores)), 3),
        }

    # Conta solo i prompt validi (>= 020)
    n_valid = 0
    for report in reports:
        results = report.get("results", [])
        if isinstance(results, dict):
            results = [results]
        for entry in results:
            try:
                num = int(entry.get("prompt_id", "").split("_")[1])
                if num >= 20:
                    n_valid += 1
            except (IndexError, ValueError):
                pass

    output = {
        "computed_at": datetime.now().isoformat(),
        "n_prompt_totali": n_valid,
        "summary": summary,
    }

    with open(SUMMARY_PATH, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    # Stampa riepilogo nel terminale
    print(f"\n{'='*55}")
    print(f"  SUMMARY VALUTAZIONE ({output['n_prompt_totali']} prompt)")
    print(f"{'='*55}")
    print(f"  {'Metrica':<25} {'Media':>7} {'Std':>7} {'Min':>7} {'Max':>7}")
    print(f"  {'-'*48}")
    for name, data in summary.items():
        print(f"  {name:<25} {data['media']:>7.3f} {data['deviazione_standard']:>7.3f} {data['min']:>7.3f} {data['max']:>7.3f}")
    print(f"{'='*55}\n")
    print(f"Summary salvato in {SUMMARY_PATH}")

    return summary


if __name__ == "__main__":
    compute_and_save_summary()
