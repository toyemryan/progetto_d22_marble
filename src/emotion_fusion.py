"""
emotion_fusion.py — Fusione numerica dei segnali emozionali.
Combina priming (0.35), realtime (0.45) e testo (0.20)
per produrre un profilo emozionale parziale.

L'inferenza dell'emozione complessa è delegata a Llama (build_marble_prompt.py).
"""

from config.emotions import EMOTIONS, HF_TO_EMOTION, Emotion, EmotionLabel
import os
import json

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
    Analisi emozionale del testo tramite Llama.
    Carica il prompt da prompts/emotion_text_analysis_prompt.txt
    Restituisce un dizionario emozione -> score normalizzato 0-1.
    """
    if not user_message or not user_message.strip():
        return {"Neutral": 1.0}

    from build_marble_prompt import call_llama
    from utils.file_utils import load_from_file

    prompt_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "prompts", "emotion_text_analysis_prompt.txt"
    )
    prompt = load_from_file(prompt_path).replace("{user_message}", user_message)

    try:
        result = call_llama(prompt, "Analisi emozionale del testo")
        if result:
            parsed = json.loads(result.strip())
            scores = {k: v for k, v in parsed.items() if isinstance(v, (int, float)) and v > 0.05}
            if scores:
                return scores
    except Exception as e:
        print(f"[score_text] Llama fallita, uso fallback keywords: {e}")

    return base_score_text(user_message)

def base_score_text(user_message: str):
    """
    Analisi basica del testo con keyword matching.
    Conta le occorrenze di keywords per ogni emozione.
    """
    text_lower = user_message.lower()
    scores = {}
    total_hits = 0

    for emotion in EMOTIONS:
        hits = emotion.matches_text(text_lower)
        if hits:
            scores[emotion.label] = len(hits)
            total_hits += len(hits)

    if total_hits > 0:
        scores = {emo: score / total_hits for emo, score in scores.items()}
    else:
        scores = {EmotionLabel.NEUTRAL: 1.0}

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
