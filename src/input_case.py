"""
input_case.py — Raccolta interattiva dei dati emozionali (in italiano)
Traduce automaticamente in inglese e aggiunge il caso a raw_cases.json.
"""

import json
import os
from datetime import datetime

# ---------- paths ----------
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
RAW_CASES_PATH = os.path.join(DATA_DIR, "raw_cases.json")
TRANSLATIONS_PATH = os.path.join(DATA_DIR, "translations.json")


def load_translations():
    with open(TRANSLATIONS_PATH, "r", encoding="utf-8") as f: # apre il file translations.json e lo carica come dizionario
        return json.load(f)


def load_raw_cases():
    if os.path.exists(RAW_CASES_PATH):
        with open(RAW_CASES_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def save_raw_cases(cases):
    with open(RAW_CASES_PATH, "w", encoding="utf-8") as f:
        json.dump(cases, f, indent=2, ensure_ascii=False)


def next_case_id(cases):
    """Genera il prossimo case_id auto-incrementale."""
    if not cases:
        return "case_001"
    last_id = max(int(c["case_id"].split("_")[1]) for c in cases)
    return f"case_{last_id + 1:03d}"


def translate_emotion(raw, translations):
    """Traduce un'emozione italiana in inglese."""
    key = raw.strip().lower()
    return translations["emotions"].get(key, raw.strip().title())


def intensity_to_label(value, translations):
    """Converte un valore 1-10 in label HIGH/MEDIUM/LOW."""
    return translations["intensity"].get(str(value), "MEDIUM")


def intensity_to_probability(value):
    """Converte un valore 1-10 in probability 0.0-1.0."""
    return round(value / 10.0, 2)


def arousal_to_label(value, translations):
    """Converte un valore arousal 1-10 in label."""
    return translations["arousal"].get(str(value), "MEDIUM")


def translate_valence(raw, translations):
    """Traduce valenza italiana in label inglese."""
    key = raw.strip().lower()
    return translations["valence"].get(key, "NEUTRAL")


# ---------- input interattivo ----------

def ask_priming_emotions(translations):
    """
    Chiede all'utente le emozioni di priming.
    Può inserire più emozioni (una alla volta).
    """
    priming = {}
    print("\n--- EMOZIONI DI PRIMING (durante lo stimolo) ---")
    print("Emozioni disponibili: felice, triste, arrabbiato, paura, sorpreso, disgusto, neutro, tenerezza")
    print("(scrivi 'fine' quando hai finito)\n")

    while True:
        emo_raw = input("  Emozione: ").strip()
        if emo_raw.lower() == "fine":
            if not priming:
                print("  ⚠ Devi inserire almeno un'emozione di priming.")
                continue
            break

        emo_en = translate_emotion(emo_raw, translations)

        try:
            intensity = int(input(f"  Intensità di '{emo_raw}' (1-10): "))
            intensity = max(1, min(10, intensity))
        except ValueError:
            intensity = 5

        valence_raw = input(f"  Valenza di '{emo_raw}' (positiva/neutra/negativa): ")

        try:
            arousal = int(input(f"  Arousal di '{emo_raw}' (1-10): "))
            arousal = max(1, min(10, arousal))
        except ValueError:
            arousal = 5

        priming[emo_en] = {
            "avg_intensity": intensity_to_label(intensity, translations),
            "avg_arousal": arousal_to_label(arousal, translations),
            "avg_valence": translate_valence(valence_raw, translations),
            "emotion_probability": intensity_to_probability(intensity)
        }

        print(f"  ✓ {emo_raw} → {emo_en} aggiunta.\n")

    return priming


def ask_realtime_emotion(translations):
    """Chiede l'emozione realtime (post-stimolo)."""
    print("\n--- EMOZIONE REALTIME (dopo lo stimolo) ---")

    emo_raw = input("  Emozione dominante: ").strip()
    emo_en = translate_emotion(emo_raw, translations)

    try:
        intensity = int(input(f"  Intensità (1-10): "))
        intensity = max(1, min(10, intensity))
    except ValueError:
        intensity = 5

    valence_raw = input("  Valenza (positiva/neutra/negativa): ")

    try:
        arousal = int(input(f"  Arousal (1-10): "))
        arousal = max(1, min(10, arousal))
    except ValueError:
        arousal = 5

    return {
        "dominant_emotion": emo_en,
        "probability": intensity_to_probability(intensity),
        "intensity_label": intensity_to_label(intensity, translations),
        "valence_label": translate_valence(valence_raw, translations),
        "arousal_label": arousal_to_label(arousal, translations)
    }


def collect_case():
    """Raccoglie un caso completo dall'utente."""
    translations = load_translations()
    cases = load_raw_cases()

    print("=" * 60)
    print("  PROGETTO D_22 — Nuovo caso emozionale")
    print("=" * 60)

    # Stimolo
    stimulus = input("\nQuale stimolo visivo ha visto l'utente?\n  → ")

    # Priming
    priming = ask_priming_emotions(translations)

    # Realtime
    realtime = ask_realtime_emotion(translations)

    # Messaggio
    print("\n--- MESSAGGIO DELL'UTENTE ---")
    user_message = input("  Messaggio (in italiano): ")

    # Costruisci il caso
    case = {
        "case_id": next_case_id(cases),
        "timestamp": datetime.now().isoformat(),
        "stimulus": stimulus,
        "priming_emotion": priming,
        "realtime_face_emotion": realtime,
        "user_message": user_message
    }

    # Salva
    cases.append(case)
    save_raw_cases(cases)

    print(f"\n✓ Caso {case['case_id']} salvato in raw_cases.json")
    print(f"  Totale casi: {len(cases)}")

    return case


if __name__ == "__main__":
    collect_case()
