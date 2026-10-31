
import sys
from pathlib import Path

import cv2
import numpy as np
import pandas as pd
import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parent
SRC_DIR = PROJECT_ROOT / "src"

sys.path.insert(0, str(SRC_DIR))

from specifications import show_specifications
from pipeline import inspect


st.set_page_config(
    page_title="DefectIQ AI",
    page_icon="🔍",
    layout="wide",
)

st.title("DefectIQ AI — Steel Surface Inspection")
st.write("Detect steel surface defects and view their dimensions.")

# Steel specimen specifications
steel_specs = show_specifications()

st.divider()

st.subheader("Inspect a steel surface image")

uploaded_file = st.file_uploader(
    "Upload a steel image",
    type=["jpg", "jpeg", "png"],
)

# Optional physical calibration
pixels_per_mm = st.number_input(
    "Calibrated pixels per millimetre (optional)",
    min_value=0.0,
    value=0.0,
    step=0.1,
    help="Enter only a calibration value established using a known reference.",
)

if uploaded_file is not None:
    image_bytes = np.frombuffer(
        uploaded_file.getvalue(), dtype=np.uint8
    )
    image_bgr = cv2.imdecode(image_bytes, cv2.IMREAD_COLOR)

    if image_bgr is None:
        st.error("Unable to read this image.")
    else:
        height, width = image_bgr.shape[:2]
        st.caption(
            f"Image resolution: {width} × {height} pixels. "
            "This is not the physical steel sheet size."
        )

        if st.button("Inspect Image", type="primary"):
            try:
                with st.spinner("Detecting defects..."):
                    result = inspect(
                        image_bgr=image_bgr,
                        image_name=uploaded_file.name,
                        profile="Standard",
                        pixels_per_mm=(
                            pixels_per_mm
                            if pixels_per_mm > 0
                            else None
                        ),
                        specimen=steel_specs,
                    )

                left, right = st.columns(2)

                with left:
                    st.subheader("Annotated image")
                    annotated_rgb = cv2.cvtColor(
                        result["annotated"], cv2.COLOR_BGR2RGB
                    )
                    st.image(
                        annotated_rgb,
                        use_container_width=True,
                    )

                with right:
                    st.subheader("Inspection decision")
                    st.metric("Decision", result["decision"])
                    st.metric(
                        "Maximum severity",
                        f'{result.get("max_score", 0):.1f}/100',
                    )
                    st.write(result.get("reason", ""))

                st.subheader("Detected defect dimensions")

                defects = result.get("defects", [])

                if defects:
                    rows = []
                    for defect in defects:
                        rows.append({
                            "Defect": defect.get("type", "Unknown"),
                            "Confidence": defect.get("confidence"),
                            "Width (px)": defect.get("width_px"),
                            "Height (px)": defect.get("height_px"),
                            "Width (mm)": defect.get("width_mm"),
                            "Height (mm)": defect.get("height_mm"),
                            "Severity": defect.get("score"),
                            "Decision": defect.get("decision"),
                        })

                    st.dataframe(
                        pd.DataFrame(rows),
                        use_container_width=True,
                        hide_index=True,
                    )

                    if pixels_per_mm <= 0:
                        st.info(
                            "Millimetre measurements are unavailable "
                            "because no calibration was provided."
                        )
                else:
                    st.info(
                        "No defects passed the configured confidence threshold."
                    )

                st.subheader("Steel specimen specifications")
                st.json(steel_specs)

                st.caption(
                    f'Inference time: {result.get("inference_ms", 0):.1f} ms'
                )

            except Exception as error:
                st.error(f"Inspection failed: {error}")
                st.info(
                    "Check that models/best.pt exists and that the "
                    "detector, pipeline, severity, and storage modules "
                    "are installed and configured correctly."
                )
