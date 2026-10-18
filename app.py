"""Data Center QC AI Toolkit: NCR drafter, photo defect spotter, QC dashboard.
Uses synthetic/public data only. Set ANTHROPIC_API_KEY before running."""
import base64
import json
import os

import anthropic
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import streamlit as st

MODEL = os.getenv("CLAUDE_MODEL", "claude-sonnet-5-5")
client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY from the environment

st.set_page_config(page_title="Data Center QC AI Toolkit", layout="wide")
st.title("Data Center QC AI Toolkit")
st.caption("Prototype tools for a data center QC manager. Demo data only, no confidential material.")


def ask(system, content, max_tokens=1500):
    resp = client.messages.create(
        model=MODEL,
        max_tokens=max_tokens,
        system=system,
        messages=[{"role": "user", "content": content}],
    )
    # Some models may return a leading "thinking" block before the text block.
    # Find the first block that actually has a .text attribute.
    for block in resp.content:
        if getattr(block, "type", None) == "text":
            return block.text
    return ""


tab1, tab2, tab3 = st.tabs(["1. NCR Drafter", "2. Photo Defect Spotter", "3. QC Dashboard"])

# ---------------------------------------------------------------- NCR drafter
NCR_SYSTEM = """You are a senior data center QC manager. Turn rough field notes into a
formal Non-Conformance Report with these sections: NCR Title, Location/Area, Trade/Contractor,
Description of Non-Conformance, Specification or Standard Reference (cite only references you are
confident exist and mark any as 'verify'), Severity (Critical/Major/Minor with one-line
justification), Probable Root Cause, Immediate Containment, Corrective Action,
Preventive Action, Verification/Closeout Method. Be concise and factual. If key details are
missing, list them under 'Info Needed' instead of inventing them."""

with tab1:
    st.subheader("Field notes in, formal NCR out")
    example = ("Row C14, cable tray above cold aisle. Penetration thru fire rated wall at grid 7 "
               "has no firestop, saw daylight thru it. Electrical sub did the tray install last week.")
    notes = st.text_area("Rough field notes", value=example, height=140)
    if st.button("Draft NCR"):
        with st.spinner("Drafting..."):
            st.markdown(ask(NCR_SYSTEM, notes))

# --------------------------------------------------------- Photo defect spotter
PHOTO_SYSTEM = """You are a data center QC inspector reviewing a site photo. Return ONLY JSON:
{"observations":[{"item":str,"category":str,"severity":"Critical|Major|Minor",
"confidence":"High|Medium|Low","recommended_action":str}],"cannot_assess":[str]}
Look for: missing firestopping, uncovered/overfilled cable trays, poor cable management or bend
radius, unlabeled conduit or cable, missing seismic bracing/supports, housekeeping, exposed
conductors, damaged equipment, water intrusion. Only report what is visible. Never guess."""

with tab2:
    st.subheader("Upload a site photo, get a draft punch list")
    img = st.file_uploader("Photo (use stock or public images)", type=["jpg", "jpeg", "png"])
    if img:
        st.image(img, width=500)
        if st.button("Analyze photo"):
            media = "image/png" if img.name.lower().endswith("png") else "image/jpeg"
            data = base64.standard_b64encode(img.getvalue()).decode()
            content = [
                {"type": "image", "source": {"type": "base64", "media_type": media, "data": data}},
                {"type": "text", "text": "Inspect this photo and return the JSON punch list."},
            ]
            with st.spinner("Inspecting..."):
                raw = ask(PHOTO_SYSTEM, content).replace("```json", "").replace("```", "").strip()
            try:
                result = json.loads(raw)
                st.dataframe(pd.DataFrame(result["observations"]), use_container_width=True)
                if result.get("cannot_assess"):
                    st.info("Could not assess: " + "; ".join(result["cannot_assess"]))
            except Exception:
                st.warning("Could not parse JSON; raw output below.")
                st.code(raw)
        st.caption("AI output is a draft for a human inspector to verify, not a final inspection.")

# ------------------------------------------------------------------- Dashboard
@st.cache_data
def make_data(n=400, seed=7):
    rng = np.random.default_rng(seed)
    types = ["Firestop", "Cable mgmt", "Labeling", "Torque/termination", "Documentation",
             "Housekeeping", "Pipe supports", "Grounding"]
    trades = ["Electrical", "Mechanical", "Controls", "Fire protection", "General"]
    return pd.DataFrame({
        "week": rng.integers(1, 13, n),
        "defect_type": rng.choice(types, n, p=[.18, .2, .15, .12, .1, .09, .09, .07]),
        "trade": rng.choice(trades, n, p=[.4, .25, .1, .15, .1]),
        "area": rng.choice(["Hall A", "Hall B", "Electrical room", "Mech yard"], n),
        "first_pass": rng.random(n) > 0.28,
    })


with tab3:
    st.subheader("Defect trends (synthetic data)")
    df = make_data()
    weeks = st.slider("Weeks to include", 1, 12, (1, 12))
    d = df[df.week.between(*weeks)]
    c1, c2, c3 = st.columns(3)
    c1.metric("Total defects", len(d))
    c2.metric("First-pass rate", f"{d.first_pass.mean():.0%}")
    c3.metric("Top defect type", d.defect_type.value_counts().idxmax())

    counts = d.defect_type.value_counts()
    cum = counts.cumsum() / counts.sum() * 100
    fig, ax = plt.subplots(figsize=(7, 3.5))
    ax.bar(counts.index, counts.values)
    ax.set_ylabel("Defects")
    ax.tick_params(axis="x", rotation=40)
    ax2 = ax.twinx()
    ax2.plot(counts.index, cum.values, marker="o", color="tab:red")
    ax2.set_ylim(0, 105)
    ax2.set_ylabel("Cumulative %")
    ax.set_title("Pareto of defect types")
    fig.tight_layout()
    st.pyplot(fig)

    left, right = st.columns(2)
    left.write("Defects by trade")
    left.bar_chart(d.trade.value_counts())
    right.write("Weekly trend")
    right.line_chart(d.groupby("week").size())

    if st.button("Write weekly QC summary"):
        stats = {
            "by_type": counts.to_dict(),
            "by_trade": d.trade.value_counts().to_dict(),
            "by_area": d.area.value_counts().to_dict(),
            "first_pass_rate": round(float(d.first_pass.mean()), 3),
            "weekly_counts": d.groupby("week").size().to_dict(),
        }
        with st.spinner("Summarizing..."):
            st.markdown(ask(
                "You are a QC manager writing a brief weekly report for the project director: "
                "key trends, top 3 recurring issues, which trades/areas need attention, and 3 "
                "specific recommended actions. Use only the numbers given. Under 200 words.",
                json.dumps(stats, default=str)))
