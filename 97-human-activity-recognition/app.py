"""
Streamlit Web Interface for AI Human Activity Recognition System.
Allows users to upload sensor streams, visualize multi-channel waveforms,
and view deep learning activity classifications.
"""
import io
import os
import csv
import tempfile
import streamlit as st
import numpy as np
import pandas as pd

from dataset import ACTIVITIES, CHANNELS, create_sliding_windows
from model import HAR1DCNN
from trainer import HARTrainer
from visualizer import render_sensor_waveform_image, format_confusion_matrix_ascii
from evaluator import HAREvaluator

st.set_page_config(
    page_title="Human Activity Recognition",
    page_icon="🏃",
    layout="wide"
)

st.title("🏃 AI-Powered Human Activity Recognition System")
st.markdown("Wearable inertial sensor classification (Accelerometer & Gyroscope) using 1D Convolutional Neural Networks.")

# Cache model instance
@st.cache_resource
def get_model():
    m = HAR1DCNN(in_channels=6, window_size=64)
    # Generate quick synthetic calibration data
    from dataset import generate_synthetic_har_dataset, load_subject_data
    with tempfile.TemporaryDirectory() as tmp:
        generate_synthetic_har_dataset(tmp, num_subjects=3, samples_per_activity=100)
        data, labels = load_subject_data(os.path.join(tmp, "subject_01"))
        X_win, y_win = create_sliding_windows(data, labels, window_size=64, step_size=20)
        trainer = HARTrainer(m)
        trainer.train(X_win, y_win, epochs=6)
    return m

model = get_model()

tabs = st.tabs(["📈 Classify Sensor Stream", "📊 Multi-Channel Waveforms", "🧠 Architecture & Anti-Leakage Guide"])

with tabs[0]:
    st.subheader("Upload Inertial Measurement Unit (IMU) CSV")
    uploaded_file = st.file_uploader("Select CSV file with 6 channels (acc_x..z, gyro_x..z):", type=["csv"])

    if uploaded_file is not None:
        try:
            df = pd.read_csv(uploaded_file)
            st.write("#### Uploaded Sensor Data Preview:")
            st.dataframe(df.head(10))

            missing_cols = [c for c in CHANNELS if c not in df.columns]
            if missing_cols:
                st.error(f"Missing required sensor channels: {', '.join(missing_cols)}")
            else:
                data_arr = df[CHANNELS].to_numpy(dtype=np.float32)
                if len(data_arr) < 64:
                    st.warning("Sensor stream contains fewer than 64 timesteps. Minimum 64 timesteps required for window classification.")
                else:
                    # Take first window
                    window = data_arr[:64].T  # (6, 64)
                    win_batch = np.expand_dims(window, axis=0)
                    preds, probs = model.predict(win_batch)

                    pred_act = ACTIVITIES[int(preds[0])]
                    conf = float(probs[0, int(preds[0])]) * 100

                    col1, col2 = st.columns([1, 1])
                    with col1:
                        st.success(f"### Predicted Activity: **{pred_act}**")
                        st.metric("Model Confidence", f"{conf:.1f}%")

                        st.write("#### Class Probability Distribution:")
                        for idx, act in enumerate(ACTIVITIES):
                            p = float(probs[0, idx])
                            st.write(f"- **{act}**: `{p * 100:.1f}%`")
                            st.progress(p)

                    with col2:
                        st.write("#### 6-Channel Waveform Profile:")
                        wf_img = render_sensor_waveform_image(window)
                        st.image(wf_img, caption="Accelerometry & Gyroscopic Trace", use_column_width=True)

        except Exception as e:
            st.error(f"Error parsing sensor data: {e}")

with tabs[1]:
    st.subheader("Explore Activity Profiles")
    selected_act = st.selectbox("Select Activity to Simulate:", ACTIVITIES)
    # Generate dynamic trace
    t = np.linspace(0, 4, 64)
    if "Walking" in selected_act:
        demo_win = np.array([
            0.8 * np.sin(2 * np.pi * 1.8 * t),
            0.3 * np.cos(2 * np.pi * 1.8 * t) - 0.98,
            0.4 * np.sin(4 * np.pi * 1.8 * t),
            1.2 * np.sin(2 * np.pi * 1.8 * t),
            0.8 * np.cos(2 * np.pi * 1.8 * t),
            0.5 * np.sin(2 * np.pi * 1.8 * t)
        ], dtype=np.float32)
    else:
        demo_win = np.array([
            np.zeros(64) + 0.05,
            np.zeros(64) - 0.98,
            np.zeros(64) + 0.1,
            np.zeros(64),
            np.zeros(64),
            np.zeros(64)
        ], dtype=np.float32)

    demo_img = render_sensor_waveform_image(demo_win)
    st.image(demo_img, caption=f"Simulated {selected_act} Waveform", use_column_width=True)

with tabs[2]:
    st.subheader("Data Leakage Prevention & Deep Learning Architecture")
    st.markdown("""
    ### Preventing Cross-Subject Data Leakage
    - **Random Splitting Flaw:** In time-series HAR datasets, randomly shuffling windows into train and test sets leads to massive data leakage, because adjacent 50% overlapping windows from the same subject end up in both sets, resulting in artificially inflated accuracy.
    - **Subject-Wise Cross-Validation:** To accurately measure generalization, dataset splits MUST be partitioned strictly by **Subject ID** (e.g. Subjects 1-7 in Train, Subjects 8-9 in Val, Subject 10 in Test).

    ### 1D-CNN vs. LSTM for Wearable Sensors
    - **1D-CNN:** Applies temporal convolution kernels across time windows to capture local periodic motifs (such as gait steps or gravitational orientation). Fast inference on low-power wearable chips.
    - **LSTM:** Maintains internal memory cells to model long-range sequential transitions between stationary and dynamic postures.
    """)
