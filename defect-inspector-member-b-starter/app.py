
import io
import json
from pathlib import Path
from datetime import datetime

import pandas as pd
import plotly.express as px
import streamlit as st
from PIL import Image, ImageOps

st.set_page_config(
    page_title="ForgeSight | Defect Inspection",
    page_icon="🔍",
    layout="wide",
)

st.markdown("""
<style>
.stApp {
    background: #111827;
    color: #F9FAFB;
}
[data-testid="stSidebar"] {
    background: #172235;
}
.hero {
    padding: 22px;
    border-radius: 14px;
    background: linear-gradient(110deg, #1E3A50, #26364B);
    border: 1px solid #3A536B;
}
.hero h1 { color: white; }
.hero p { color: #D5E1EC; }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="hero">
<h1>🔍 ForgeSight</h1>
<p>Manufacturing Defect Inspection & Quality Intelligence</p>
</div>
""", unsafe_allow_html=True)

st.warning(
    "DEMO MODE: The real YOLO detector and severity pipeline "
    "are not connected yet. Results must not be treated as real predictions."
)

if "history" not in st.session_state:
    st.session_state.history = []

def read_image(upload):
    image = Image.open(io.BytesIO(upload.getvalue()))
    return ImageOps.exif_transpose(image).convert("RGB")

def demo_result(filename):
    return {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "filename": filename,
        "defect": "Not evaluated",
        "confidence": None,
        "severity": "Not evaluated",
        "disposition": "Awaiting model",
        "mode": "DEMO",
    }

inspect_tab, batch_tab, trends_tab, health_tab = st.tabs([
    "🔬 Inspect",
    "📦 Batch Inspection",
    "📈 Quality Trends",
    "🩺 Model Health",
])

with inspect_tab:
    st.subheader("Inspect a fabric image")
    uploaded = st.file_uploader(
        "Upload an image",
        type=["jpg", "jpeg", "png", "bmp", "webp"],
        key="single_image",
    )

    if uploaded:
        try:
            image = read_image(uploaded)
            left, right = st.columns(2)

            with left:
                st.image(image, caption=uploaded.name,
                         use_container_width=True)
                st.caption(f"Image size: {image.width} × {image.height}")

            with right:
                st.subheader("Inspection result")
                if st.button("Run inspection demo", type="primary"):
                    result = demo_result(uploaded.name)
                    st.session_state.history.append(result)
                    st.session_state.last_result = result

                result = st.session_state.get("last_result")
                if result and result["filename"] == uploaded.name:
                    st.metric("Defect", result["defect"])
                    st.metric("Severity", result["severity"])
                    st.metric("Disposition", result["disposition"])
                    st.info(
                        "Connect the real detector and severity pipeline "
                        "to display actual inspection results."
                    )
                else:
                    st.info("Click the button to test the dashboard workflow.")
        except Exception as exc:
            st.error(f"Unable to read image: {exc}")

with batch_tab:
    st.subheader("Batch inspection")
    uploads = st.file_uploader(
        "Select multiple images",
        type=["jpg", "jpeg", "png", "bmp", "webp"],
        accept_multiple_files=True,
        key="batch_images",
    )

    if uploads and st.button("Process batch demo", type="primary"):
        results = []
        for upload in uploads:
            try:
                read_image(upload)
                result = demo_result(upload.name)
                results.append(result)
                st.session_state.history.append(result)
            except Exception:
                st.warning(f"Skipped invalid image: {upload.name}")

        st.session_state.batch_results = results

    batch_results = st.session_state.get("batch_results", [])
    if batch_results:
        frame = pd.DataFrame(batch_results)
        st.dataframe(frame, use_container_width=True)
        st.download_button(
            "Download batch CSV",
            data=frame.to_csv(index=False).encode("utf-8"),
            file_name="inspection_report.csv",
            mime="text/csv",
        )
        st.caption("These are demo records, not actual model predictions.")

with trends_tab:
    st.subheader("Quality trends")
    if not st.session_state.history:
        st.info("Run an inspection to create session history.")
    else:
        frame = pd.DataFrame(st.session_state.history)
        first, second = st.columns(2)
        first.metric("Total records", len(frame))
        second.metric("Real predictions", 0)

        counts = (
            frame.groupby("mode")
            .size()
            .reset_index(name="records")
        )
        chart = px.bar(
            counts,
            x="mode",
            y="records",
            title="Inspection records by mode",
        )
        st.plotly_chart(chart, use_container_width=True)
        st.dataframe(frame, use_container_width=True)

        st.download_button(
            "Export inspection history",
            data=frame.to_csv(index=False).encode("utf-8"),
            file_name="inspection_history.csv",
            mime="text/csv",
        )

with health_tab:
    st.subheader("Model health")
    metrics_path = Path("models/metrics.json")
    confusion_path = Path("models/confusion_matrix.png")

    if metrics_path.exists():
        try:
            with metrics_path.open("r", encoding="utf-8") as file:
                st.json(json.load(file))
        except (OSError, json.JSONDecodeError) as exc:
            st.error(f"Unable to read model metrics: {exc}")
    else:
        st.info(
            "Model metrics are not available yet. Ask Member A for "
            "the actual evaluation metrics after model testing."
        )

    if confusion_path.exists():
        st.image(
            str(confusion_path),
            caption="Model confusion matrix",
            use_container_width=True,
        )

st.divider()
st.caption("ForgeSight | PS19 | Person C Dashboard")
