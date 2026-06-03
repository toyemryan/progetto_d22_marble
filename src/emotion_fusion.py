"""
emotion_fusion.py — Fusione numerica dei segnali emozionali.
Combina priming (0.35), realtime (0.45) e testo (0.20)
per produrre un profilo emozionale parziale.

L'inferenza dell'emozione complessa è delegata a Llama (build_marble_prompt.py).
"""

from config.emotions import EMOTIONS, HF_TO_EMOTION, Emotion, EmotionLabel
from utils.translator import translate_it_to_en
from dotenv import load_dotenv
import os
from huggingface_hub import InferenceClient

load_dotenv()

# Pesi dal documento tecnico (sezione 9.3)
PRIMING_WEIGHT = 0.35
REALTIME_WEIGHT = 0.45
TEXT_WEIGHT = 0.20

# Conversione labels → valori numerici
INTENSITY_MAP = {"HIGH": 1.0, "MEDIUM": 0.6, "LOW": 0.3}
VALENCE_MAP = {"POSITIVE": 1.0, "NEUTRAL": 0.0, "NEGATIVE": -1.0}
AROUSAL_MAP = {"HIGH": 1.0, "MEDIUM": 0.5, "LOW": 0.2}

def score_priming(priming_emotion):
    """
    Calcola il punteggio per ogni emozione di priming.
    Usa emotion_probability come peso base.
    """
    scores = {}
    for emo, data in priming_emotion.items():
        prob = data.get("emotion_probability", 0.5)
        intensity = INTENSITY_MAP.get(data.get("avg_intensity", "MEDIUM"), 0.6)
        score = prob * intensity
        emotion = next((e for e in EMOTIONS if emo.lower() in e.normalize_aliases), None)
        if emotion is not None:
            scores[emotion.label] = score
    return scores


def score_realtime(realtime_face_emotion):
    """
    Calcola il punteggio per l'emozione realtime.
    Restituisce un dict con una sola emozione (la dominante).
    """
    emo = realtime_face_emotion.get("dominant_emotion", "Neutral")
    prob = realtime_face_emotion.get("probability", 0.5)
    intensity = INTENSITY_MAP.get(
        realtime_face_emotion.get("intensity_label", "MEDIUM"), 0.6
    )
    emotion = next((e for e in EMOTIONS if emo.lower() in e.normalize_aliases), None)
    if emotion is not None:
        return {emotion.label: prob * intensity}
    raise ValueError("wrong value for the emotion")

def score_text(user_message: str) -> dict:
    """
    Traduce il testo ed esegue l'analisi con il classificatore SamLowe/roberta-base-go_emotions
    Restituisce un dizionario emozione -> score normalizzato 0-1.
    """
    if not user_message or not user_message.strip():
        return {"Neutral": 1.0}

    translated = translate_it_to_en(user_message)
    token = os.getenv("HF_TOKEN", "")
    client = InferenceClient(token=os.getenv("HF_TOKEN"))
    results = client.text_classification(translated, model="SamLowe/roberta-base-go_emotions")

    scores: dict[EmotionLabel, float] = {}

    for item in results:
        label = item["label"].lower()
        if label in HF_TO_EMOTION and item["score"] > 0.05:
            emotion = HF_TO_EMOTION[label]
            scores[emotion] = scores.get(emotion, 0.0) + item["score"]

    return scores


def fuse_emotions(normalized_case):
    """
    Fusione dei tre segnali emozionali con i pesi del documento.

    Input:  caso normalizzato (output di parse_cases.py)
    Output: profilo emozionale numerico parziale
    """
    priming_scores = score_priming(normalized_case["priming_emotion"])
    realtime_scores = score_realtime(normalized_case["realtime_face_emotion"])
    text_scores = score_text(normalized_case["user_message"])

    # Raccogli tutte le emozioni menzionate
    all_emotions = set(priming_scores) | set(realtime_scores) | set(text_scores)

    # Calcolo fusione pesata
    fusion = {}
    for emo in all_emotions:
        p = priming_scores.get(emo, 0.0) * PRIMING_WEIGHT
        r = realtime_scores.get(emo, 0.0) * REALTIME_WEIGHT
        t = text_scores.get(emo, 0.0) * TEXT_WEIGHT
        fusion[emo] = round(p + r + t, 4)

    # Emozione dominante = punteggio più alto
    dominant = max(fusion.keys(), key=lambda k: fusion[k])

    # Valence e arousal dalla realtime (segnale più forte)
    rt = normalized_case["realtime_face_emotion"]
    valence = rt.get("valence_label", "NEUTRAL").lower()
    arousal = rt.get("arousal_label", "MEDIUM").lower()

    return {
        "dominant_emotion": dominant,
        "intensity_score": round(fusion[dominant], 2),
        "valence": valence,
        "arousal": arousal,
        "fusion_scores": fusion,
        "signal_detail": {
            "priming_scores": priming_scores,
            "realtime_scores": realtime_scores,
            "text_scores": text_scores,
        },
    }


if __name__ == "__main__":
    import json
    from parse_cases import parse_and_normalize

    case = parse_and_normalize()
    profile = fuse_emotions(case)
    print(json.dumps(profile, indent=2, ensure_ascii=False))
