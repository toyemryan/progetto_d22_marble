from dataclasses import dataclass
from enum import Enum


class EmotionLabel(Enum):
    HAPPY      = "Happy"
    SAD        = "Sad"
    ANGRY      = "Angry"
    FEAR       = "Fear"
    SURPRISED  = "Surprised"
    DISGUST    = "Disgust"
    TENDERNESS = "Tenderness"
    NEUTRAL    = "Neutral"


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
        ),
        text_keywords=(
            "arrabbiato", "rabbia", "furioso", "ingiusto", "odio",
            "irritato", "nervoso", "stufo",
        ),
    ),
    Emotion(
        label=EmotionLabel.FEAR,
        normalize_aliases=(
            "fear", "paura", "spaventato",
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
        ),
        text_keywords=(
            "schifo", "disgusto", "orribile", "rivoltante", "ripugnante",
        ),
    ),
    Emotion(
        label=EmotionLabel.TENDERNESS,
        normalize_aliases=(
            "tenderness", "tenerezza", "tenero",
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
        ),
        text_keywords=(),
    ),
]