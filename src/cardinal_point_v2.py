import os
from huggingface_hub import InferenceClient
from config.emotions import EmotionLabel
from utils.translator import translate_it_to_en

def get_emotion_target(user_message: str, stimulus: str) -> str:
    if not user_message or not user_message.strip():
        return "neutral"

    translated = translate_it_to_en(f"Context: {stimulus}. Message: {user_message}")
    client = InferenceClient(token=os.getenv("HF_TOKEN"))
    TARGET_LABELS = [
        "Hope",
        "Nostalgia and pride",
        "Acceptance",
        "Connection",
        "Gratitude",
        "Joy",
        "Safety",
        "Tenderness"
    ]
    
    result = client.zero_shot_classification(
        translated,
        candidate_labels=TARGET_LABELS,
        hypothesis_template="The best emotional response for this person is {}"
    )

    return result[0]["label"]

def prepare_cardinal_context(normalized_case, fusion_profile):
    target = get_emotion_target(normalized_case["user_message"], normalized_case["stimulus"])
    
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
