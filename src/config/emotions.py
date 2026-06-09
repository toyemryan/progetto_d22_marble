from dataclasses import dataclass
from enum import StrEnum


class EmotionLabel(StrEnum):
    """Emozioni rilevabili dal testo e dal volto"""
    HAPPY      = "Happy"
    SAD        = "Sad"
    ANGRY      = "Angry"
    FEAR       = "Fear"
    SURPRISED  = "Surprised"
    DISGUST    = "Disgust"
    TENDERNESS = "Tenderness"
    NEUTRAL    = "Neutral"
    FEARFUL = "Fearful"


class EmotionTarget(StrEnum):
    """Direzioni emotive verso cui portare l'utente"""
    HOPE        = "Hope"
    GRATITUDE   = "Gratitude"
    PRIDE       = "Pride"
    ACCEPTANCE  = "Acceptance"
    SAFETY      = "Safety"
    CONNECTION  = "Connection"
    JOY         = "Joy"
    TENDERNESS  = "Tenderness"
    NOSTALGIA   = "Nostalgia"
    WONDER      = "Wonder"
    NEUTRAL = "Neutral"

EMOTION_TO_TARGET: dict[EmotionLabel, EmotionTarget] = {
    EmotionLabel.SAD:        EmotionTarget.HOPE,
    EmotionLabel.FEAR:       EmotionTarget.SAFETY,
    EmotionLabel.ANGRY:      EmotionTarget.ACCEPTANCE,
    EmotionLabel.DISGUST:    EmotionTarget.WONDER,
    EmotionLabel.SURPRISED:  EmotionTarget.JOY,
    EmotionLabel.HAPPY:      EmotionTarget.GRATITUDE,
    EmotionLabel.TENDERNESS: EmotionTarget.CONNECTION,
    EmotionLabel.NEUTRAL:    EmotionTarget.WONDER,
}

@dataclass(frozen=True)
class Emotion:
    label: EmotionLabel
    normalize_aliases: tuple[str, ...]
    text_keywords: tuple[str, ...]

    def matches_alias(self, name: str) -> bool:
        return name.strip().lower() in self.normalize_aliases

    def matches_text(self, text: str) -> list[str]:
        text_lower = text.lower()
        return [kw for kw in self.text_keywords if kw in text_lower]

    def normalize(self, name: str) -> str:
        key = name.strip().lower()
        if self.matches_alias(key):
            return self.label.value
        return name.strip().title()


EMOTIONS: list[Emotion] = [
    Emotion(
        label=EmotionLabel.HAPPY,
        normalize_aliases=(
            "happy", "felice", "felicità", "gioia",
            "joy", "joyful", "cheerful", "glad", "pleased", "content",
            "gioioso", "allegro", "contento", "entusiasta", "euforico",
            "soddisfatto", "raggiante", "sereno", "positivo", "eccitato",
        ),
        text_keywords=(
            "felice", "gioia", "contento", "bello", "voglio bene",
            "amore", "sorriso", "ridere", "allegro", "fantastico", "meraviglioso",
        ),
    ),
    Emotion(
        label=EmotionLabel.SAD,
        normalize_aliases=(
            "sad", "triste", "tristezza",
            "sadness", "unhappy", "sorrowful", "melancholic", "depressed", "gloomy",
            "malinconico", "abbattuto", "affranto", "dispiaciuto", "addolorato",
            "rattristato", "melanconico", "cupo", "desolato", "avvilito",
        ),
        text_keywords=(
            "triste", "tristezza", "piangere", "lacrime", "dolore",
            "perdita", "mancare", "manca", "solo", "solitudine", "vuoto",
        ),
    ),
    Emotion(
        label=EmotionLabel.ANGRY,
        normalize_aliases=(
            "angry", "arrabbiato", "rabbia",
            "anger", "mad", "furious", "rage", "irritated", "outraged",
            "furibondo", "incazzato", "irato", "indignato", "esasperato",
            "risentito", "alterato", "fumante", "infuriato", "esasperato",
        ),
        text_keywords=(
            "arrabbiato", "rabbia", "furioso", "ingiusto", "odio",
            "irritato", "nervoso", "stufo",
        ),
    ),
    Emotion(
        label=EmotionLabel.FEAR,
        normalize_aliases=(
            "fear", "paura", "spaventato", "fearful",
            "scared", "afraid", "terrified", "anxious", "frightened", "horrified",
            "timoroso", "impaurito", "terrorizzato", "angosciato", "agitato",
            "ansioso", "preoccupato", "inquieto", "ansia", "apprensivo",
            "tensione", "angoscia", "timore"
        ),
        text_keywords=(
            "paura", "spaventato", "terrore", "ansia", "agitazione",
            "preoccupato", "timore", "angoscia",
        ),
    ),
    Emotion(
        label=EmotionLabel.SURPRISED,
        normalize_aliases=(
            "surprised", "sorpreso", "sorpresa",
            "surprise", "astonished", "amazed", "shocked", "stunned", "startled",
            "stupito", "meravigliato", "sbigottito", "incredulo", "sbalordito",
            "colpito", "scioccato", "esterrefatto", "allibito", "senza parole",
        ),
        text_keywords=(
            "sorpreso", "sorpresa", "incredibile", "assurdo", "wow",
            "inaspettato", "shock",
        ),
    ),
    Emotion(
        label=EmotionLabel.DISGUST,
        normalize_aliases=(
            "disgust", "disgusto",
            "disgusted", "revolted", "repulsed", "nauseated", "appalled",
            "disgustato", "schifato", "nauseato", "rivoltato", "ripugnato",
            "stomacato", "indignato", "orripilato", "inorridito",
        ),
        text_keywords=(
            "schifo", "disgusto", "orribile", "rivoltante", "ripugnante",
        ),
    ),
    Emotion(
        label=EmotionLabel.TENDERNESS,
        normalize_aliases=(
            "tenderness", "tenerezza", "tenero",
            "tender", "affectionate", "loving", "warm", "caring", "gentle",
            "affettuoso", "amorevole", "dolce", "premuroso", "affezionato",
            "protettivo", "caldo", "empatico", "compassionevole", "benevolo",
        ),
        text_keywords=(
            "tenero", "tenerezza", "dolce", "amorevole", "affetto",
            "carino", "delicato", "gentile", "abbraccio",
        ),
    ),
    Emotion(
        label=EmotionLabel.NEUTRAL,
        normalize_aliases=(
            "neutral", "neutro", "neutrale",
            "indifferent", "calm", "composed", "detached", "impassive",
            "indifferente", "calmo", "distaccato", "impassibile", "tranquillo",
            "sereno", "equilibrato", "pacato", "apatico", "inespressivo",
        ),
        text_keywords=(),
    ),
]

#mapping from classifier emotion to my Emotions
HF_TO_EMOTION: dict[str, EmotionLabel] = {
    # HAPPY
    "joy":          EmotionLabel.HAPPY,
    "amusement":    EmotionLabel.HAPPY,
    "excitement":   EmotionLabel.HAPPY,
    "optimism":     EmotionLabel.HAPPY,
    "pride":        EmotionLabel.HAPPY,
    "relief":       EmotionLabel.HAPPY,
    "gratitude":    EmotionLabel.HAPPY,

    # SAD
    "sadness":      EmotionLabel.SAD,
    "grief":        EmotionLabel.SAD,
    "disappointment": EmotionLabel.SAD,
    "remorse":      EmotionLabel.SAD,

    # ANGRY
    "anger":        EmotionLabel.ANGRY,
    "annoyance":    EmotionLabel.ANGRY,
    "disapproval":  EmotionLabel.ANGRY,

    # FEAR
    "fear":         EmotionLabel.FEAR,
    "nervousness":  EmotionLabel.FEAR,

    # SURPRISED
    "surprise":     EmotionLabel.SURPRISED,
    "realization":  EmotionLabel.SURPRISED,
    "confusion":    EmotionLabel.SURPRISED,

    # DISGUST
    "disgust":      EmotionLabel.DISGUST,

    # TENDERNESS
    "love":         EmotionLabel.TENDERNESS,
    "caring":       EmotionLabel.TENDERNESS,
    "admiration":   EmotionLabel.TENDERNESS,

    # NEUTRAL
    "neutral":      EmotionLabel.NEUTRAL,
    "curiosity":    EmotionLabel.NEUTRAL,
    "desire":       EmotionLabel.NEUTRAL,
    "approval":     EmotionLabel.NEUTRAL,
    "embarrassment": EmotionLabel.NEUTRAL,
}