from __future__ import annotations
from typing import TYPE_CHECKING
import streamlit as st
import numpy as np
import plotly.graph_objs as go
from sklearn.decomposition import PCA
from streamlit_autorefresh import st_autorefresh
import os
import json
from pathlib import Path
from .model import Predictor

if TYPE_CHECKING:
    import os

FOLLOW_TOUCH_ID = int(os.getenv("FOLLOW_TOUCH_ID", "0"))
LABEL_CLASSES = 5
LABEL_NAMES = {
    0: "Center",
    1: "Lower Left",
    2: "Lower Right",
    3: "Upper Right",
    4: "Upper Left",
}
LABEL_COLORS = {0: "red", 1: "blue", 2: "green", 3: "orange", 4: "purple"}


def streamlit_run(storage_path) -> None:
    """
    Run the Streamlit app to visualize predictions.
    Args:
        data_path (os.PathLike): Path to the data file containing activations and labels.
        model_path (os.PathLike): Path to the model file (not used in this function).
    """
    configure_streamlit()
    storage_path = Path(storage_path)
    # Find the latest file matching the pattern "follow_touch_[0-3]_date.json"
    files = list(storage_path.glob(f"follow_touch_{FOLLOW_TOUCH_ID}_*.json"))
    if not files:
        st.warning(
            f"No matching data files found. Waiting for data to be generated in {storage_path}"
        )
        st.stop()

    # Sort files by date in descending order and pick the latest one
    latest_file = max(files, key=lambda f: f.stat().st_mtime)
    data_path = latest_file
    model_path = storage_path / "params"

    # Constants
    PRED_FREQ = int(os.environ.get("PRED_FREQ", 10000))  # in ms
    N_PRED_SAMPLES = int(os.environ.get("N_PRED_SAMPLES", 50))

    # Auto-refresh
    st_autorefresh(interval=PRED_FREQ, limit=None, key="data_autorefresh")

    # File validation
    data_file = Path(storage_path)
    if not data_file.exists():
        st.warning(f"Data file not found at {data_path}")
        st.stop()

    # Load and buffer data
    samples = load_data(data_path)

    if "predictions" not in st.session_state:
        st.session_state.predictions = []
        st.session_state.pca_buffer = []
        st.session_state.last_pred_index = 0

    if len(samples) - st.session_state.last_pred_index >= N_PRED_SAMPLES:
        model = Predictor(model_path=model_path)
        missing_data = samples[st.session_state.last_pred_index :]
        num_batches = len(missing_data) // N_PRED_SAMPLES

        if num_batches > 0:
            # Stack the data for parallel processing
            stacked_batches = [
                missing_data[i * N_PRED_SAMPLES : (i + 1) * N_PRED_SAMPLES]
                for i in range(num_batches)
            ]
            stacked_batches = np.stack(stacked_batches, axis=0)
            print(
                f"Processing {stacked_batches.shape} batches of {N_PRED_SAMPLES} samples each."
            )
            # Run predictions in parallel
            preds, reduced_activations = run_prediction(stacked_batches, model)

            # Flatten and store results
            st.session_state.predictions += preds
            st.session_state.pca_buffer += reduced_activations

            st.session_state.last_pred_index += num_batches * N_PRED_SAMPLES
    display_visualization(
        samples, st.session_state.predictions, st.session_state.pca_buffer
    )


def configure_streamlit():
    """Configure Streamlit settings."""
    st.set_page_config(layout="wide")
    st.title("Predictions Visualization")


def load_data(data_path: os.PathLike) -> list:
    """Load data from the specified JSON file."""
    try:
        with open(data_path, "r") as f:
            return json.load(f)
    except Exception as e:
        st.error(f"Error loading data: {e}")
        st.stop()


def run_prediction(buffer: list, model: Predictor) -> tuple:
    """Run predictions and PCA on the latest data in the buffer."""
    window = np.array(buffer)
    pred, activations = model(window)
    pca = PCA(n_components=3)
    reduced_activations = [
        pca.fit_transform(activations[i]) for i in range(activations.shape[0])
    ]
    return pred.tolist(), reduced_activations


def display_visualization(samples, predictions, pca_data):
    """Display the PCA visualization with sidebar controls."""
    st.sidebar.write(f"Buffer size: {len(samples)}")
    DISPLAY_LIMIT = st.sidebar.slider(
        "Number of Points to Display", min_value=1, max_value=100, value=1
    )
    max_time_index = max(len(st.session_state.pca_buffer) - DISPLAY_LIMIT, 0)
    TIME_SLIDER = st.sidebar.slider(
        "Time Window (index)",
        min_value=0,
        max_value=max_time_index if max_time_index > 0 else 1,
        value=max_time_index,
    )
    if "pca_buffer" not in st.session_state or len(st.session_state.pca_buffer) < 3:
        # Display an empty plot if there is not enough data
        empty_fig = go.Figure()
        empty_fig.update_layout(
            scene=dict(xaxis_title="PC1", yaxis_title="PC2", zaxis_title="PC3"),
            title="3D PCA of RNN Activations (No Data)",
            margin=dict(l=0, r=0, t=50, b=0),
        )
        st.plotly_chart(empty_fig, use_container_width=True)
    else:
        fig = go.Figure()
        added_labels = set()  # Track labels already added to the legend
        for idx, distr in enumerate(
            predictions[TIME_SLIDER : TIME_SLIDER + DISPLAY_LIMIT], start=TIME_SLIDER
        ):
            label = np.argmax(distr)
            show_legend = label not in added_labels
            if show_legend:
                added_labels.add(label)
            fig.add_trace(
                go.Scatter3d(
                    x=pca_data[idx][0],
                    y=pca_data[idx][1],
                    z=pca_data[idx][2],
                    mode="markers+lines",
                    marker=dict(size=6, color=LABEL_COLORS[label], opacity=0.9),
                    line=dict(color=LABEL_COLORS[label], width=2),
                    name=LABEL_NAMES[label],
                    showlegend=show_legend,
                )
            )
        fig.update_layout(
            scene=dict(xaxis_title="PC1", yaxis_title="PC2", zaxis_title="PC3"),
            title="3D PCA of RNN Activations",
            margin=dict(l=0, r=0, t=50, b=0),
            legend=dict(title="Predicted Labels", itemsizing="constant"),
        )

        LABEL_POSITIONS = {
            0: (0.5, 0.5),  # Center
            1: (0.0, 0.0),  # Lower Left
            2: (1.0, 0.0),  # Lower Right
            3: (1.0, 1.0),  # Upper Right
            4: (0.0, 1.0),  # Upper Left
        }

        fig2 = go.Figure()
        for idx, prob_dist in enumerate(
            predictions[TIME_SLIDER : TIME_SLIDER + DISPLAY_LIMIT]
        ):
            x = sum(prob_dist[i] * LABEL_POSITIONS[i][0] for i in range(5))
            y = sum(prob_dist[i] * LABEL_POSITIONS[i][1] for i in range(5))
            uncertainty = 1 - np.max(prob_dist)
            color = LABEL_COLORS[np.argmax(prob_dist)]

            fig2.add_trace(
                go.Scatter(
                    x=[x],
                    y=[y],
                    mode="markers",
                    marker=dict(
                        size=20,
                        color=color,
                        opacity=0.3 + 0.7 * (1 - uncertainty),
                        line=dict(width=1, color="black"),
                    ),
                    showlegend=False,
                )
            )

            # Add shaded circle to indicate uncertainty
            theta = np.linspace(0, 2 * np.pi, 100)
            radius = 0.1 + 0.2 * uncertainty  # Base radius scaled by uncertainty
            circle_x = x + radius * np.cos(theta)
            circle_y = y + radius * np.sin(theta)

            fig2.add_trace(
                go.Scatter(
                    x=circle_x,
                    y=circle_y,
                    fill="toself",
                    fillcolor=color,
                    line=dict(color=color),
                    opacity=0.2,
                    mode="lines",
                    showlegend=False,
                )
            )

        fig2.update_layout(
            title="2D Pressure Point Visualization with Uncertainty",
            xaxis=dict(
                range=[-0.1, 1.1],
                title="X",
                showgrid=True,
                zeroline=False,
            ),
            yaxis=dict(
                range=[-0.1, 1.1],
                title="Y",
                showgrid=True,
                zeroline=False,
            ),
            width=600,
            height=600,
        )

        col1, col2 = st.columns(2)

        with col1:
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            st.plotly_chart(fig2, use_container_width=True)
