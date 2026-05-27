"""
cardinal_point.py — Preparazione del contesto per l'inferenza del punto cardinale.

Questo modulo NON fa l'inferenza da solo: prepara i dati di riferimento
(tabella patterns della sezione 9.4) e li struttura per Llama,
che farà l'inferenza vera in build_marble_prompt.py.
"""

# Tabella pattern dal documento tecnico (sezione 9.4)
CARDINAL_PATTERNS = [
    {
        "keywords_it": ["mio padre", "vivo", "voglio bene", "presente", "c'è ancora"],
        "stimulus_context": "death, loss, mourning",
        "cardinal_point": "from loss to presence, gratitude, and familial bond",
        "direction": "gratitude",
    },
    {
        "keywords_it": ["tenero", "amorevoli", "simpatico", "dolce", "carino"],
        "stimulus_context": "relationship between characters",
        "cardinal_point": "emotional connection and affective bond",
        "direction": "tenderness",
    },
    {
        "keywords_it": ["buffo", "goffo", "adorasse", "impacciato", "divertente"],
        "stimulus_context": "clumsy or awkward gesture",
        "cardinal_point": "acceptance of imperfections",
        "direction": "acceptance",
    },
    {
        "keywords_it": ["diverse", "assomigliare", "simili", "diversi", "uguali"],
        "stimulus_context": "difference between characters",
        "cardinal_point": "hidden similarity and understanding",
        "direction": "connection",
    },
    {
        "keywords_it": ["ingiusto", "arrabbiare", "rabbia", "furioso", "odio"],
        "stimulus_context": "conflict, injustice",
        "cardinal_point": "from anger to transformation and agency",
        "direction": "transformation",
    },
    {
        "keywords_it": ["agitazione", "succedere", "paura", "ansia", "pericolo"],
        "stimulus_context": "threat, suspense, danger",
        "cardinal_point": "from threat to safety and control",
        "direction": "safety",
    },
    {
        "keywords_it": ["triste", "piangere", "perdita", "manca", "dolore"],
        "stimulus_context": "loss, sadness",
        "cardinal_point": "from loss to memory, care, and hope",
        "direction": "memory",
    },
    {
        "keywords_it": ["incredibile", "sorpreso", "wow", "assurdo", "inaspettato"],
        "stimulus_context": "unexpected event, revelation",
        "cardinal_point": "from surprise to discovery and curiosity",
        "direction": "discovery",
    },
]


def find_matching_patterns(user_message):
    """
    Cerca pattern corrispondenti nel messaggio utente.
    Restituisce i pattern trovati (possono essere multipli).
    Non fa l'inferenza finale: fornisce context a Llama.
    """
    text_lower = user_message.lower()
    matches = []

    for pattern in CARDINAL_PATTERNS:
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
        "reference_table": CARDINAL_PATTERNS,
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
