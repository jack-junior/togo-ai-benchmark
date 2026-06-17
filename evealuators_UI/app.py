import streamlit as st
import json
import os
from datetime import datetime
import uuid
import pandas as pd
# --------------------------------------------------
# PAGE CONFIG
# --------------------------------------------------

st.set_page_config(
    page_title="Togo AI Benchmark",
    page_icon="🇹🇬",
    layout="wide"
)

# --------------------------------------------------
# LOAD JSONL FILES
# --------------------------------------------------

def load_jsonl(path):
    records = []

    if not os.path.exists(path):
        return records

    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()

            if line:
                records.append(json.loads(line))

    return records


questions = load_jsonl("test_questions.jsonl")
openai_results = load_jsonl("openai_results.jsonl")
gemini_results = load_jsonl("gemini_results.jsonl")

# --------------------------------------------------
# SIDEBAR STATISTICS
# --------------------------------------------------

if os.path.exists("human_evaluations.jsonl"):

    with open(
        "human_evaluations.jsonl",
        "r",
        encoding="utf-8"
    ) as f:

        n_evaluations = sum(
            1 for line in f
            if line.strip()
        )

else:

    n_evaluations = 0

st.sidebar.title("📊 Benchmark Statistics")

st.sidebar.metric(
    "Saved Evaluations",
    n_evaluations
)

# --------------------------------------------------
# SCORE LABELS
# --------------------------------------------------

C1_LABELS = {
    0: "Aucune information correcte",
    1: "Majoritairement incorrect",
    2: "Plusieurs erreurs importantes",
    3: "Partiellement exact",
    4: "Quelques imprécisions mineures",
    5: "Parfaitement exact et contextualisé"
}

C2_LABELS = {
    0: "Complètement déconnecté du terrain",
    1: "Très faible compréhension locale",
    2: "Trop théorique",
    3: "Mélange réalisme/généricité",
    4: "Globalement réaliste",
    5: "Très fortement ancré dans les réalités togolaises"
}

C3_LABELS = {
    0: "Inutilisable",
    1: "Très vague",
    2: "Trop théorique",
    3: "Modérément utile",
    4: "Utile et compréhensible",
    5: "Très clair et immédiatement exploitable"
}

C4_LABELS = {
    0: "Aucune nuance ou recul critique",
    1: "Très forte surconfiance",
    2: "Plusieurs affirmations excessives",
    3: "Reconnaît partiellement les limites",
    4: "Bonne reconnaissance des limites",
    5: "Excellente gestion de l'incertitude"
}

C5_LABELS = {
    0: "Réponse fondamentalement fabriquée",
    1: "Hallucinations graves",
    2: "Hallucinations multiples",
    3: "Une hallucination isolée",
    4: "Très légère extrapolation",
    5: "Aucune hallucination détectée"
}

# --------------------------------------------------
# LOOKUPS
# --------------------------------------------------

question_lookup = {}

for q in questions:
    question_lookup[q["id"]] = q

openai_lookup = {}

for r in openai_results:
    qid = r["question_metadata"]["id"]
    openai_lookup[qid] = r

gemini_lookup = {}

for r in gemini_results:
    qid = r["question_metadata"]["id"]
    gemini_lookup[qid] = r

# --------------------------------------------------
# HEADER
# --------------------------------------------------

st.title("🇹🇬 Togo AI Benchmark")
st.markdown("### Human Evaluation Platform")

# --------------------------------------------------
# QUESTION SELECTION
# --------------------------------------------------

question_ids = list(question_lookup.keys())

if not question_ids:
    st.error("No questions found in test_questions.jsonl")
    st.stop()

selected_qid = st.selectbox(
    "Select Question",
    question_ids
)

question_record = question_lookup[selected_qid]

st.subheader("Question")

st.info(question_record["question"])

col1, col2 = st.columns(2)

with col1:
    st.write("Category:", question_record["category"])

with col2:
    st.write("Language:", question_record["language"])

# --------------------------------------------------
# MODEL SELECTION
# --------------------------------------------------

model_choice = st.radio(
    "Select Model Response",
    ["OpenAI GPT-5.5", "Gemini 3.1"]
)

response_text = ""

if model_choice == "OpenAI GPT-5.5":

    if selected_qid in openai_lookup:
        response_text = openai_lookup[selected_qid]["output"]["response"]

else:

    if selected_qid in gemini_lookup:
        response_text = gemini_lookup[selected_qid]["output"]["response"]

# --------------------------------------------------
# DISPLAY RESPONSE
# --------------------------------------------------

st.subheader("Model Response")

st.text_area(
    "Response",
    value=response_text,
    height=400,
    disabled=True
)

# --------------------------------------------------
# HUMAN EVALUATION
# --------------------------------------------------

st.markdown("---")
st.header("Human Evaluation")

annotator = st.text_input("Annotator ID")

def score_box(label, labels_dict):

    selected = st.selectbox(
        label,
        list(labels_dict.keys()),
        format_func=lambda x:
        f"{x} → {labels_dict[x]}"
    )

    st.caption(
        f"Signification : {labels_dict[selected]}"
    )

    return selected


c1 = score_box(
    "C1 - Exactitude de la Source de Vérité",
    C1_LABELS
)
j1 = st.text_area("Justification C1")

c2 = score_box(
    "C2 - Réalisme du Terrain Togolais",
    C2_LABELS
)
j2 = st.text_area("Justification C2")

c3 = score_box(
    "C3 - Actionnabilité et Clarté",
    C3_LABELS
)
j3 = st.text_area("Justification C3")

c4 = score_box(
    "C4 - Lucidité et Gestion des Limites",
    C4_LABELS
)
j4 = st.text_area("Justification C4")

c5 = score_box(
    "C5 - Sévérité des Hallucinations",
    C5_LABELS
)
j5 = st.text_area("Justification C5")

# --------------------------------------------------
# SCORE CALCULATION
# --------------------------------------------------

weighted_score = (
    (3 * c1)
    + (2 * c2)
    + c3
    + c4
    + (3 * c5)
) / 10

normalized_score = round(
    (weighted_score / 5) * 100,
    1
)

st.markdown("---")

colA, colB = st.columns(2)

with colA:
    st.metric(
        "Weighted Score (/5)",
        round(weighted_score, 2)
    )

with colB:
    st.metric(
        "Normalized Score (/100)",
        normalized_score
    )

comments = st.text_area(
    "Global Comments"
)

# --------------------------------------------------
# SAVE EVALUATION
# --------------------------------------------------

if st.button("Save Evaluation"):

    if annotator.strip() == "":
        st.error("Please enter Annotator ID")

    else:

        record = {
            "evaluation_metadata": {
                "evaluation_id": str(uuid.uuid4()),
                "timestamp": datetime.utcnow().isoformat(),
                "evaluation_type": "human_evaluation"
            },

            "question_metadata": {
                "question_id": selected_qid,
                "category": question_record["category"],
                "language": question_record["language"]
            },

            "response_metadata": {
                "model": model_choice
            },

            "annotator": annotator,

            "evaluation_scores": {

                "C1_exactitude_source_verite": {
                    "score": c1,
                    "justification": j1
                },

                "C2_realisme_terrain_togolais": {
                    "score": c2,
                    "justification": j2
                },

                "C3_actionnabilite_clarte": {
                    "score": c3,
                    "justification": j3
                },

                "C4_lucidite_limites": {
                    "score": c4,
                    "justification": j4
                },

                "C5_severite_hallucinations": {
                    "score": c5,
                    "justification": j5
                }
            },

            "aggregate_scores": {
                "weighted_total_score": round(weighted_score, 2),
                "normalized_score_100": normalized_score
            },

            "comments": comments
        }

        with open(
            "human_evaluations.jsonl",
            "a",
            encoding="utf-8"
        ) as f:

            f.write(
                json.dumps(
                    record,
                    ensure_ascii=False
                ) + "\n"
            )

        st.success("✅ Evaluation saved successfully!")

        st.subheader("Saved Evaluation Summary")

        table_data = {
            "Field": [
                "Question ID",
                "Category",
                "Language",
                "Model",
                "Annotator",
                "C1",
                "C2",
                "C3",
                "C4",
                "C5",
                "Weighted Score",
                "Normalized Score"
            ],

            "Value": [
                selected_qid,
                question_record["category"],
                question_record["language"],
                model_choice,
                annotator,
                c1,
                c2,
                c3,
                c4,
                c5,
                round(weighted_score, 2),
                normalized_score
            ]
        }

        df = pd.DataFrame(table_data)

        st.table(
            df,
            hide_index=True
        )

        with open(
            "human_evaluations.jsonl",
            "r",
            encoding="utf-8"
        ) as f:

            st.download_button(
                "⬇ Download Evaluations",
                data=f.read(),
                file_name="human_evaluations.jsonl",
                mime="application/json"
            )

# --------------------------------------------------
# SHOW ALL SAVED EVALUATIONS
# --------------------------------------------------

all_evals = load_jsonl("human_evaluations.jsonl")

rows = []

for e in all_evals:

    rows.append({
        "Question": e["question_metadata"]["question_id"],
        "Model": e["response_metadata"]["model"],
        "Annotator": e["annotator"],
        "C1": e["evaluation_scores"]["C1_exactitude_source_verite"]["score"],
        "C2": e["evaluation_scores"]["C2_realisme_terrain_togolais"]["score"],
        "C3": e["evaluation_scores"]["C3_actionnabilite_clarte"]["score"],
        "C4": e["evaluation_scores"]["C4_lucidite_limites"]["score"],
        "C5": e["evaluation_scores"]["C5_severite_hallucinations"]["score"],
        "Score (/5)": e["aggregate_scores"]["weighted_total_score"],
        "Score (/100)": e["aggregate_scores"]["normalized_score_100"]
    })

st.subheader("📋 All Saved Evaluations")

if rows:
    st.dataframe(
        pd.DataFrame(rows),
        use_container_width=True,
        hide_index=True
    )
else:
    st.info("No evaluations saved yet.")