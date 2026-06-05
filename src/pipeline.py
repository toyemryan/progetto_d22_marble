"""
pipeline.py — Orchestra l'intera pipeline D:22.

Modalità:
  --new       Raccoglie un nuovo caso interattivo, poi genera il prompt
  --last      Genera il prompt per l'ultimo caso in raw_cases.json
  --all       Genera i prompt per tutti i casi
  --evaluate  Valuta tutti i prompt generati
  --case ID   Genera il prompt per un caso specifico (es. --case case_001)
"""

import argparse
import asyncio
import sys
import os

# Aggiungi src al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from input_case import collect_case
from parse_cases import parse_and_normalize, parse_all
from emotion_fusion import fuse_emotions
from cardinal_point import prepare_cardinal_context
from build_marble_prompt import generate_marble_prompt
from evaluate_outputs import evaluate_all
from dotenv import load_dotenv

load_dotenv()

def process_case(normalized_case):
    """Processa un singolo caso attraverso tutta la pipeline."""
    case_id = normalized_case["case_id"]
    print(f"\n{'='*60}")
    print(f"  Elaborazione {case_id}")
    print(f"{'='*60}")

    # Fase 2 — Fusione emozionale
    print("\n📊 Fase 2: Fusione emozionale...")
    fusion = fuse_emotions(normalized_case)
    print(f"  Emozione dominante: {fusion['dominant_emotion']}")
    print(f"  Score: {fusion['intensity_score']}")
    print(f"  Valence: {fusion['valence']} | Arousal: {fusion['arousal']}")

    # Fase 3 — Contesto punto cardinale
    print("\n🧭 Fase 3: Analisi punto cardinale...")
    cardinal = prepare_cardinal_context(normalized_case, fusion)
    print(f"  Hint: {cardinal['hint']}")

    # Fase 4 — Generazione prompt Marble (Llama)
    print("\n🎨 Fase 4: Generazione prompt Marble...")
    start_vpn = os.getenv("CONNECT_TO_REMOTE", "false").lower() == "true"
    result = asyncio.run(generate_marble_prompt(normalized_case, fusion, cardinal, start_vpn=start_vpn))

    if result:
        marble_prompt = result.get("marble_prompt", "")
        if marble_prompt:
            print(f"\n{'─'*60}")
            print("PROMPT MARBLE GENERATO:")
            print(f"{'─'*60}")
            print(marble_prompt[:500] + "..." if len(marble_prompt) > 500 else marble_prompt)
            print(f"{'─'*60}")
    else:
        print("  ❌ Generazione fallita.")

    return result


def run_new():
    """Raccoglie un nuovo caso e lo processa."""
    case_data = collect_case()
    normalized = parse_and_normalize(case_data["case_id"])
    return process_case(normalized)


def run_last():
    """Processa l'ultimo caso in raw_cases.json."""
    normalized = parse_and_normalize()  # Default: ultimo
    return process_case(normalized)


def run_case(case_id):
    """Processa un caso specifico."""
    normalized = parse_and_normalize(case_id)
    return process_case(normalized)


def run_all():
    """Processa tutti i casi."""
    cases = parse_all()
    print(f"\n🔄 Elaborazione di {len(cases)} casi...\n")
    results = []
    for case in cases:
        result = process_case(case)
        results.append(result)
    return results


def main():
    parser = argparse.ArgumentParser(
        description="Pipeline D_22 — Emotion-Aware Marble Prompt Generation"
    )
    parser.add_argument("--new", action="store_true",
                        help="Raccogli un nuovo caso interattivo")
    parser.add_argument("--last", action="store_true",
                        help="Genera prompt per l'ultimo caso")
    parser.add_argument("--all", action="store_true",
                        help="Genera prompt per tutti i casi")
    parser.add_argument("--evaluate", action="store_true",
                        help="Valuta tutti i prompt generati")
    parser.add_argument("--case", type=str,
                        help="Genera prompt per un caso specifico (es. case_001)")

    args = parser.parse_args()

    print("""
    ╔══════════════════════════════════════════════╗
    ║  PROGETTO D_22                               ║
    ║  Emotion-Aware Marble Prompt Generation      ║
    ╚══════════════════════════════════════════════╝
    """)

    if args.new:
        run_new()
    elif args.last:
        run_last()
    elif args.all:
        run_all()
    elif args.evaluate:
        try:
            asyncio.run(evaluate_all())
        finally:
            os._exit(0) #forza la chiusura dei thread rimasti
    elif args.case:
        run_case(args.case)
    else:
        # Default: mostra le opzioni
        print("Uso:")
        print("  python pipeline.py --new        Nuovo caso interattivo")
        print("  python pipeline.py --last       Processa ultimo caso")
        print("  python pipeline.py --all        Processa tutti i casi")
        print("  python pipeline.py --evaluate   Valuta i prompt generati")
        print("  python pipeline.py --case ID    Processa caso specifico")
        print()
        parser.print_help()


if __name__ == "__main__":
    main()
