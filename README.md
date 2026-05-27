# Progetto D:22 — Emotion-Aware Meta-Prompting for Marble 3D World Generation

## Descrizione

Pipeline Python che trasforma dati emozionali (priming + realtime + messaggio utente) in prompt dettagliati per la generazione di mondi 3D in Marble. Il sistema utilizza Llama (via Ollama) per l'inferenza dell'emozione complessa, del punto cardinale e la generazione del prompt finale.

## Architettura

```
[Input interattivo IT] → parse_cases → emotion_fusion → cardinal_point → build_marble_prompt + Llama → marble_prompts.json → [Marble manuale]
```

## Prerequisiti

- Python 3.10+
- [Ollama](https://ollama.ai/) installato e in esecuzione
- Modello Llama scaricato: `ollama pull llama3`

## Installazione

```bash
git clone https://github.com/VOSTRO_REPO/progetto_d22_marble.git
cd progetto_d22_marble
pip install -r requirements.txt
```

## Avvio rapido

```bash
# Avvia Ollama (in un terminale separato)
ollama serve

# Nuovo caso interattivo (in italiano)
python src/pipeline.py --new

# Processa l'ultimo caso inserito
python src/pipeline.py --last

# Processa tutti i casi
python src/pipeline.py --all

# Valuta i prompt generati
python src/pipeline.py --evaluate

# Processa un caso specifico
python src/pipeline.py --case case_001
```

## Struttura del progetto

```
progetto_d22_marble/
├── data/
│   ├── raw_cases.json          ← Casi emozionali (input)
│   ├── marble_prompts.json     ← Prompt generati (output)
│   ├── evaluation_report.json  ← Report di valutazione
│   └── translations.json       ← Dizionario IT→EN
├── src/
│   ├── pipeline.py             ← Orchestratore principale
│   ├── input_case.py           ← Raccolta interattiva (italiano)
│   ├── parse_cases.py          ← Parsing e normalizzazione
│   ├── emotion_fusion.py       ← Fusione emozionale numerica
│   ├── cardinal_point.py       ← Preparazione punto cardinale
│   ├── build_marble_prompt.py  ← Assemblaggio + chiamata Llama
│   └── evaluate_outputs.py     ← Valutazione dei prompt
├── prompts/
│   └── meta_prompt_base.txt    ← Meta-prompt per Llama
├── outputs/
│   └── screenshots/            ← Screenshot da Marble
├── docs/                       ← Documentazione aggiuntiva
├── requirements.txt
├── .gitignore
└── README.md
```

## Moduli

| Modulo | Input | Output |
|--------|-------|--------|
| `input_case.py` | Risposte utente (IT) | Caso aggiunto a `raw_cases.json` |
| `parse_cases.py` | `raw_cases.json` | Caso normalizzato (dict) |
| `emotion_fusion.py` | Caso normalizzato | Profilo emozionale numerico |
| `cardinal_point.py` | Caso + profilo | Contesto cardinale per Llama |
| `build_marble_prompt.py` | Tutto + meta-prompt | Prompt Marble via Llama |
| `evaluate_outputs.py` | `marble_prompts.json` | `evaluation_report.json` |

## Pesi di fusione emozionale

- Priming: **0.35**
- Realtime: **0.45**
- Testo: **0.20**

## Autori

Progetto D:22 — Università di Urbino
