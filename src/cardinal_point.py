"""
cardinal_point.py — Preparazione del contesto per l'inferenza del punto cardinale.

Questo modulo NON fa l'inferenza da solo: prepara i dati di riferimento
(tabella patterns della sezione 9.4) e li struttura per Llama,
che farà l'inferenza vera in build_marble_prompt.py.
"""

from config.patterns import PATTERN

def find_matching_patterns(user_message):
    """
    Cerca pattern corrispondenti nel messaggio utente.
    Restituisce i pattern trovati (possono essere multipli).
    Non fa l'inferenza finale: fornisce context a Llama.
    """
    text_lower = user_message.lower()
    matches = []

    for pattern in PATTERN:
        hits = [kw for kw in pattern["keywords_it"] if kw in text_lower]
        if hits:
            matches.append({
                "matched_keywords": hits,
                "suggested_cardinal_point": pattern["cardinal_point"],
                "suggested_direction": pattern["direction"],
                "stimulus_context": pattern["stimulus_context"],
            })

    return matches


def prepare_cardinal_context(normalized_case, fusion_profile):
    """
    Prepara il contesto del punto cardinale per Llama.

    Input:  caso normalizzato + profilo di fusione
    Output: dict con pattern trovati + hint per Llama
    """
    matches = find_matching_patterns(normalized_case["user_message"])

    context = {
        "user_message": normalized_case["user_message"],
        "stimulus": normalized_case["stimulus"],
        "dominant_emotion": fusion_profile["dominant_emotion"],
        "valence": fusion_profile["valence"],
        "pattern_matches": matches,
        "reference_table": PATTERN,
    }

    # Se ci sono match, aggiungi un hint
    if matches:
        best = matches[0]  # Il primo match come suggerimento
        context["hint"] = (
            f"Based on keywords {best['matched_keywords']}, "
            f"the likely cardinal point is: {best['suggested_cardinal_point']}"
        )
    else:
        context["hint"] = (
            "No keyword pattern matched. "
            "Llama should infer the cardinal point from the full message and stimulus context."
        )

    return context


if __name__ == "__main__":
    import json
    from parse_cases import parse_and_normalize
    from emotion_fusion import fuse_emotions

    case = parse_and_normalize()
    profile = fuse_emotions(case)
    cardinal = prepare_cardinal_context(case, profile)

    print(json.dumps(cardinal, indent=2, ensure_ascii=False))
