"""
parse_cases.py — Lettura e normalizzazione dei casi emozionali.
Legge raw_cases.json, uniforma le etichette e produce casi normalizzati.
"""

import json
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
RAW_CASES_PATH = os.path.join(DATA_DIR, "raw_cases.json")

# Mappatura per uniformare i nomi delle emozioni
EMOTION_NORMALIZE = {
    "happy": "Happy", "felice": "Happy", "felicità": "Happy", "gioia": "Happy",
    "sad": "Sad", "triste": "Sad", "tristezza": "Sad",
    "angry": "Angry", "arrabbiato": "Angry", "rabbia": "Angry",
    "fear": "Fear", "paura": "Fear", "spaventato": "Fear",
    "surprised": "Surprised", "sorpreso": "Surprised", "sorpresa": "Surprised",
    "disgust": "Disgust", "disgusto": "Disgust",
    "neutral": "Neutral", "neutro": "Neutral", "neutrale": "Neutral",
    "tenderness": "Tenderness", "tenerezza": "Tenderness", "tenero": "Tenderness",
}

VALID_INTENSITY = {"HIGH", "MEDIUM", "LOW"}
VALID_VALENCE = {"POSITIVE", "NEUTRAL", "NEGATIVE"}
VALID_AROUSAL = {"HIGH", "MEDIUM", "LOW"}


def load_raw_cases():
    with open(RAW_CASES_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def normalize_emotion_name(name):
    """Uniforma il nome dell'emozione (IT/EN) al formato standard EN."""
    return EMOTION_NORMALIZE.get(name.strip().lower(), name.strip().title())


def normalize_label(value, valid_set, default="MEDIUM"):
    """Uniforma un'etichetta (intensity, valence, arousal)."""
    if isinstance(value, str):
        upper = value.strip().upper()
        # Gestisci labels italiane
        mapping = {
            "ALTA": "HIGH", "MEDIA": "MEDIUM", "BASSA": "LOW",
            "POSITIVA": "POSITIVE", "NEUTRA": "NEUTRAL", "NEGATIVA": "NEGATIVE",
        }
        upper = mapping.get(upper, upper)
        if upper in valid_set:
            return upper
    return default


def normalize_priming(priming_raw):
    """Normalizza le emozioni di priming."""
    normalized = {}
    for emo_name, data in priming_raw.items():
        std_name = normalize_emotion_name(emo_name)
        normalized[std_name] = {
            "avg_intensity": normalize_label(data.get("avg_intensity", "MEDIUM"), VALID_INTENSITY),
            "avg_arousal": normalize_label(data.get("avg_arousal", "MEDIUM"), VALID_AROUSAL),
            "avg_valence": normalize_label(data.get("avg_valence", "NEUTRAL"), VALID_VALENCE),
            "emotion_probability": float(data.get("emotion_probability", 0.5)),
        }
    return normalized


def normalize_realtime(realtime_raw):
    """Normalizza l'emozione realtime."""
    return {
        "dominant_emotion": normalize_emotion_name(realtime_raw.get("dominant_emotion", "Neutral")),
        "probability": float(realtime_raw.get("probability", 0.5)),
        "intensity_label": normalize_label(realtime_raw.get("intensity_label", "MEDIUM"), VALID_INTENSITY),
        "valence_label": normalize_label(realtime_raw.get("valence_label", "NEUTRAL"), VALID_VALENCE),
        "arousal_label": normalize_label(realtime_raw.get("arousal_label", "MEDIUM"), VALID_AROUSAL),
    }


def normalize_case(case):
    """Normalizza un singolo caso."""
    return {
        "case_id": case["case_id"],
        "timestamp": case.get("timestamp", ""),
        "stimulus": case.get("stimulus", "Unknown stimulus"),
        "priming_emotion": normalize_priming(case.get("priming_emotion", {})),
        "realtime_face_emotion": normalize_realtime(case.get("realtime_face_emotion", {})),
        "user_message": case.get("user_message", ""),
    }


def parse_and_normalize(case_id=None):
    """
    Legge raw_cases.json e normalizza.
    Se case_id è None, normalizza l'ultimo caso aggiunto.
    Se case_id è specificato, normalizza quel caso.
    """
    cases = load_raw_cases()

    if not cases:
        raise ValueError("Nessun caso trovato in raw_cases.json")

    if case_id:
        target = next((c for c in cases if c["case_id"] == case_id), None)
        if not target:
            raise ValueError(f"Caso {case_id} non trovato")
        return normalize_case(target)

    # Default: ultimo caso
    return normalize_case(cases[-1])


def parse_all():
    """Normalizza tutti i casi."""
    cases = load_raw_cases()
    return [normalize_case(c) for c in cases]


if __name__ == "__main__":
    result = parse_and_normalize()
    print(json.dumps(result, indent=2, ensure_ascii=False))
