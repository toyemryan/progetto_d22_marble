import os
from huggingface_hub import InferenceClient
from config.emotions import EMOTION_TO_TARGET, EmotionLabel, EmotionTarget
from utils.translator import translate_it_to_en

def get_emotion_target(dominant_emotion: EmotionLabel) -> EmotionTarget:
    return EMOTION_TO_TARGET.get(dominant_emotion, EmotionTarget.NEUTRAL)

def prepare_cardinal_context(normalized_case, fusion_profile):
    target = get_emotion_target(fusion_profile["dominant_emotion"])
    
    return {
        "user_message": normalized_case["user_message"],
        "stimulus": normalized_case["stimulus"],
        "dominant_emotion": fusion_profile["dominant_emotion"],
        "valence": fusion_profile["valence"],
        "hint": f"the likely cardinal point is: {target}"
    }

if __name__ == "__main__":
    import json
    from parse_cases import parse_and_normalize
    from emotion_fusion import fuse_emotions

    case = parse_and_normalize()
    profile = fuse_emotions(case)
    cardinal = prepare_cardinal_context(case, profile)

    print(json.dumps(cardinal, indent=2, ensure_ascii=False))
