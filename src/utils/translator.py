from deep_translator import GoogleTranslator

def translate_it_to_en(text: str) -> str:
    return GoogleTranslator(source="it", target="en").translate(text)