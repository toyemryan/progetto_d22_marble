import json
import os
import pandas as pd
import plotly.express as px

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FILE_PATH = os.path.join(BASE_DIR, "data", "evaluation_report.json")

# 1. Caricamento del file JSON delle valutazioni
with open(FILE_PATH, "r") as f:
    data = json.load(f)

# 2. Appiattimento del JSON tramite list comprehension nidificata
df = pd.DataFrame([
    {
        "Scenario": c["results"]["prompt_id"].upper(), # Es: "PROMPT_001", "PROMPT_002"...
        "Metrica": metric_name.replace("_", " ").title(),
        "Punteggio": metric_info["score"]
    }
    for c in data[-6:]
    for metric_name, metric_info in c["results"]["metrics"].items()
])

# 3. Creazione del grafico a barre raggruppate con Plotly Express
fig = px.bar(
    df, 
    x="Scenario", 
    y="Punteggio", 
    color="Metrica",
    barmode="group",  # Mette le barre dei due prompt una di fianco all'altra per confrontarle
    title="Confronto Quantitativo delle Metriche di Valutazione",
    labels={"Punteggio": "Score (Scala 0.0 - 1.0)"},
    text_auto=False   # Mostra automaticamente il valore sopra le barre (es. 0.8)
)

# Ottimizzazioni grafiche per renderlo pulito
fig.update_layout(
    yaxis_range=[0, 1.1],  # Lascia un po' di spazio in alto per i numeri sui tetti delle barre
    xaxis_title="Scenari valutati",
    legend_title="Metriche DeepEval"
)

fig.show()