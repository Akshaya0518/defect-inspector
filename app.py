
from pathlib import Path
from datetime import datetime
import json

import pandas as pd
import streamlit as st
import plotly.express as px
from PIL import Image

st.set_page_config(
    page_title="ForgeSight AI",
    page_icon="🔎",
    layout="wide",
    initial_sidebar_state="expanded",
)

ROOT = Path(__file__).resolve().parent
HISTORY = ROOT / "inspection_history.csv"
METRICS = ROOT / "models" / "metrics.json"

# ---------- PREMIUM DARK THEME ----------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Manrope:wght@400;500;600;700;800&display=swap');

html, body, [class*="css"] {
    font-family: 'Manrope', sans-serif;
}
.stApp {
    background:
      radial-gradient(ellipse at top left, #18332f 0%, transparent 35%),
      #090e13;
    color: #eaf3f5;
}
[data-testid="stSidebar"] {
    background: #0d151c;
    border-right: 1px solid #263942;
}
h1, h2, h3 { color: #f1fbfa; letter-spacing: -0.04em; }
div[data-testid="stMetric"] {
    background: linear-gradient(140deg, #17252d, #10171e);
    border: 1px solid #2c424b;
    border-radius: 15px;
    padding: 18px;
}
div[data-testid="stMetricLabel"] { color: #9cb3bd; }
div[data-testid="stMetricValue"] { color: #e9fffa; }
.stButton button, .stDownloadButton button {
    background: #16463f;
    color: #e8fffa;
    border: 1px solid #36a58e;
    border-radius: 10px;
    font-weight: 700;
}
.stButton button:hover, .stDownloadButton button:hover {
    border-color: #58f0ce;
    color: white;
}
.fs-hero {
    background: linear-gradient(115deg, #163b37, #121e27 70%);
    border: 1px solid #31534f;
    border-radius: 18px;
    padding: 27px;
    margin-bottom: 20px;
}
.fs-eyebrow {
    color: #63e9ca;
    font-size: 11px;
    font-weight: 800;
    letter-spacing: 3px;
}
.fs-title {
    font-size: 34px;
    font-weight: 800;
    margin-top: 7px;
    color: #f5fffd;
}
.fs-sub { color: #afc5cb; font-size: 14px; }
.fs-card {
    background: linear-gradient(140deg, #17252d, #10171e);
    border: 1px solid #2c424b;
    border-radius: 15px;
    padding: 18px;
    min-height: 110px;
}
.fs-label {
    color: #9cb3bd;
    font-size: 11px;
    font-weight: 800;
    letter-spacing: 1px;
}
.fs-value { color: #f0fffc; font-size: 24px; font-weight: 800; margin-top: 10px; }
.fs-note { color: #91a7b0; font-size: 12px; margin-top: 5px; }
hr { border-color: #263942; }
footer { visibility: hidden; }
</style>
""", unsafe_allow_html=True)


def load_history():
    if HISTORY.exists():
        try:
            return pd.read_csv(HISTORY)
        except Exception:
            pass
    return pd.DataFrame(columns=[
        "timestamp", "filename", "source", "defect_count",
        "defect_types", "severity", "status"
    ])


def save_rows(rows):
    old = load_history()
    updated = pd.concat([old, pd.DataFrame(rows)], ignore_index=True)
    updated.to_csv(HISTORY, index=False)


def header(title, subtitle):
    st.markdown(f"""
    <div class="fs-hero">
      <div class="fs-eyebrow">FORGESIGHT AI / PS19</div>
      <div class="fs-title">{title}</div>
      <div class="fs-sub">{subtitle}</div>
    </div>
    """, unsafe_allow_html=True)


def demo_row(filename):
    return {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "filename": filename,
        "source": "DEMO",
        "defect_count": None,
        "defect_types": "Not evaluated",
        "severity": "Not evaluated",
        "status": "DEMO ONLY",
    }


history = load_history()

# ---------- SIDEBAR ----------
with st.sidebar:
    st.markdown("### 🟢 FORGESIGHT AI")
    st.caption("INDUSTRIAL QUALITY INTELLIGENCE")
    page = st.radio(
        "NAVIGATION",
        [
            "Overview",
            "Inspect Image",
            "Batch Inspection",
            "Quality Analytics",
            "Reports",
            "Model Health",
        ],
    )
    st.divider()
    st.caption("PS19 · Manufacturing Defect Inspection")
    st.caption("Person 3 · Dashboard and Reporting")


# ---------- OVERVIEW ----------
if page == "Overview":
    header(
        "Inspection Command Center",
        "A unified view of manufacturing surface quality and inspection activity."
    )

    real = (
        history[history["source"] == "REAL PIPELINE"]
        if not history.empty else pd.DataFrame()
    )

    total = len(history)
    defects = (
        pd.to_numeric(real["defect_count"], errors="coerce").fillna(0)
        if not real.empty else pd.Series(dtype=float)
    )
    rate = f"{100 * (defects > 0).mean():.1f}%" if len(defects) else "—"

    high = (
        int(real["severity"].astype(str)
            .str.contains("critical|high", case=False).sum())
        if not real.empty else "—"
    )
    passed = (
        int(real["status"].astype(str)
            .str.contains("pass|clear|accept", case=False).sum())
        if not real.empty else "—"
    )

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("TOTAL INSPECTIONS", total)
    c2.metric("DEFECT RATE", rate)
    c3.metric("HIGH / CRITICAL", high)
    c4.metric("PASSED INSPECTIONS", passed)

    st.write("")
    left, right = st.columns([1.4, 1])

    with left:
        st.subheader("Recent inspection activity")
        if history.empty:
            st.info("No records yet. Start in Inspect Image.")
        else:
            st.dataframe(
                history.tail(8).iloc[::-1],
                use_container_width=True,
                hide_index=True,
            )

    with right:
        st.subheader("System status")
        st.markdown("""
        <div class="fs-card">
          <div class="fs-label">AI PIPELINE</div>
          <div class="fs-value">Integration pending</div>
          <div class="fs-note">
            Connect the team's real detection and severity modules.
          </div>
        </div>
        """, unsafe_allow_html=True)

        st.caption("Demo records are excluded from real quality metrics.")


# ---------- SINGLE IMAGE ----------
elif page == "Inspect Image":
    header(
        "AI Inspection Studio",
        "Upload a steel-surface image for the inspection workflow."
    )

    file = st.file_uploader(
        "Upload surface image",
        type=["png", "jpg", "jpeg", "bmp", "webp"],
    )

    if file:
        try:
            image = Image.open(file).convert("RGB")

            left, right = st.columns(2)
            with left:
                st.subheader("01 / Input image")
                st.image(image, use_container_width=True)
                st.caption(f"{image.width} × {image.height} pixels")

            with right:
                st.subheader("02 / Inspection output")
                st.image(image, use_container_width=True)
                st.warning(
                    "DEMO MODE: real YOLO detections are not connected. "
                    "No defect-free conclusion can be made."
                )

            if st.button("Record demo inspection", type="primary"):
                save_rows([demo_row(file.name)])
                st.success("Demo record saved and labelled.")
                st.rerun()

        except Exception as exc:
            st.error(f"Unable to read image: {exc}")
    else:
        st.info("Upload an image to preview the inspection workflow.")


# ---------- BATCH ----------
elif page == "Batch Inspection":
    header(
        "Batch Inspection",
        "Prepare a report for multiple manufacturing images."
    )

    files = st.file_uploader(
        "Choose multiple images",
        type=["png", "jpg", "jpeg", "bmp", "webp"],
        accept_multiple_files=True,
    )

    if files:
        st.write(f"Selected images: **{len(files)}**")

        if st.button("Prepare demo batch report", type="primary"):
            rows = []
            for file in files:
                try:
                    image = Image.open(file)
                    image.verify()
                    rows.append(demo_row(file.name))
                except Exception:
                    rows.append({
                        **demo_row(file.name),
                        "source": "ERROR",
                        "status": "Invalid image",
                    })

            save_rows(rows)
            result = pd.DataFrame(rows)
            st.dataframe(result, use_container_width=True, hide_index=True)
            st.download_button(
                "Download batch CSV",
                result.to_csv(index=False).encode("utf-8"),
                "forgesight_batch_report.csv",
                "text/csv",
            )
            st.warning("Demo report only; no AI inference was run.")


# ---------- ANALYTICS ----------
elif page == "Quality Analytics":
    header(
        "Quality Intelligence",
        "Analyze recorded results from the actual inspection pipeline."
    )

    real = (
        history[history["source"] == "REAL PIPELINE"].copy()
        if not history.empty else pd.DataFrame()
    )

    if real.empty:
        st.info(
            "Real inspection records are not available yet. "
            "Connect the AI pipeline before interpreting quality trends."
        )
    else:
        real["defect_count"] = pd.to_numeric(
            real["defect_count"], errors="coerce"
        ).fillna(0)

        a, b = st.columns(2)

        with a:
            st.subheader("Defect categories")
            categories = (
                real["defect_types"].fillna("Unknown")
                .str.split(", ").explode().value_counts()
                .rename_axis("Category").reset_index(name="Records")
            )
            fig = px.bar(
                categories, x="Category", y="Records",
                template="plotly_dark"
            )
            fig.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
            )
            st.plotly_chart(fig, use_container_width=True)

        with b:
            st.subheader("Severity distribution")
            severity = (
                real["severity"].fillna("Unknown")
                .value_counts().rename_axis("Severity")
                .reset_index(name="Records")
            )
            fig = px.pie(
                severity, names="Severity", values="Records",
                hole=0.55, template="plotly_dark"
            )
            fig.update_layout(paper_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig, use_container_width=True)


# ---------- REPORTS ----------
elif page == "Reports":
    header(
        "Reports & Traceability",
        "Review saved inspection events and export a report."
    )

    if history.empty:
        st.info("No inspection records yet.")
    else:
        mode = st.selectbox(
            "Records",
            ["All records", "Real pipeline only", "Demo only"],
        )

        report = history.copy()
        if mode == "Real pipeline only":
            report = report[report["source"] == "REAL PIPELINE"]
        elif mode == "Demo only":
            report = report[report["source"] == "DEMO"]

        search = st.text_input("Search filename or defect")
        if search:
            matches = report.astype(str).apply(
                lambda col: col.str.contains(
                    search, case=False, na=False
                )
            ).any(axis=1)
            report = report[matches]

        st.dataframe(report, use_container_width=True, hide_index=True)
        st.download_button(
            "Download CSV report",
            report.to_csv(index=False).encode("utf-8"),
            "forgesight_inspection_history.csv",
            "text/csv",
        )


# ---------- MODEL HEALTH ----------
elif page == "Model Health":
    header(
        "Model Health",
        "Display measured model metrics supplied by the detection team."
    )

    if METRICS.exists():
        try:
            metrics = json.loads(METRICS.read_text(encoding="utf-8"))
            cols = st.columns(4)
            for col, label, key in zip(
                cols,
                ["Precision", "Recall", "mAP50", "mAP50-95"],
                ["precision", "recall", "map50", "map50_95"],
            ):
                value = metrics.get(key)
                col.metric(
                    label,
                    f"{value:.3f}"
                    if isinstance(value, (int, float)) else "—",
                )
        except Exception as exc:
            st.error(f"Unable to read model metrics: {exc}")
    else:
        st.warning("Model evaluation metrics are not available yet.")
        st.caption(
            "Ask Person 1 to provide measured evaluation metrics after "
            "testing the trained model."
        )

    st.markdown("---")
    st.subheader("Integration status")
    st.info(
        "The real YOLO detector and severity pipeline must be connected "
        "before this dashboard can display genuine AI predictions."
    )


st.divider()
st.caption(
    "ForgeSight AI · PS19 Manufacturing Defect Inspection · Person 3"
)
