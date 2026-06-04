import asyncio
import os
import json
from build_marble_prompt import call_llama
from config.emotions import EMOTION_TO_TARGET, EmotionLabel, EmotionTarget
from vpn_utils.vpn import vpn_tunnel
from utils.file_utils import load_from_file

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
META_PROMPT_PATH = os.path.join(BASE_DIR, "prompts", "cardinal_point_meta_prompt.txt")

async def get_emotion_target(user_message: str, dominant_emotion: EmotionLabel) -> tuple[EmotionTarget, str]:
    try:
        array = [e.value for e in EmotionTarget]
        meta_prompt = load_from_file(META_PROMPT_PATH)
        prompt = meta_prompt.format(
            array=array,
            user_message=user_message,
            dominant_emotion=dominant_emotion
        )
            
        if os.getenv("CONNECT_TO_REMOTE", "").lower() == "true":
            async with vpn_tunnel():
                result = call_llama(prompt)
        else:
            result = call_llama(prompt)
        
        if not result:
            raise ValueError("Llama returned None or empty response")

        parsed = json.loads(str(result).strip())

        valid_labels = [e.value for e in EmotionTarget]
        found = next((label for label in valid_labels if label.lower() in parsed["emotion"].lower()), None)

        if not found:
            raise ValueError(f"No valid EmotionTarget found in: {parsed['emotion']}")

        return EmotionTarget(found), parsed["cardinal_point"]
    except Exception as e:
        print(e)
        target = EMOTION_TO_TARGET.get(dominant_emotion, EmotionTarget.NEUTRAL)
        return target, f"from {dominant_emotion.value.lower()} toward {target.value.lower()}"

def prepare_cardinal_context(normalized_case, fusion_profile):
    target, cardinal_point = asyncio.run(
        get_emotion_target(
            normalized_case["user_message"], 
            fusion_profile["dominant_emotion"]
        )
    )
    
    return {
        "user_message": normalized_case["user_message"],
        "stimulus": normalized_case["stimulus"],
        "dominant_emotion": fusion_profile["dominant_emotion"],
        "valence": fusion_profile["valence"],
        "emotion_target": target,
        "hint": f"the likely cardinal point is: {cardinal_point}",
    }

if __name__ == "__main__":
    import json
    from parse_cases import parse_and_normalize
    from emotion_fusion import fuse_emotions

    case = parse_and_normalize()
    profile = fuse_emotions(case)
    cardinal = prepare_cardinal_context(case, profile)

    print(json.dumps(cardinal, indent=2, ensure_ascii=False))
