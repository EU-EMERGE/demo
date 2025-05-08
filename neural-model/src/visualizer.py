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

STORAGE_PATH = os.getenv("STORAGE_PATH", "storage")
DEBUG = int(os.getenv("DEBUG", "1"))
FOLLOW_TOUCH_ID = int(os.getenv("FOLLOW_TOUCH_ID", "0"))
MODEL_INPUT_SIZE = int(os.getenv("MODEL_INPUT_SIZE", "4"))
TRAJECTORY_LENGTH = int(os.getenv("TRAJECTORY_LENGTH", "10"))
LABEL_CLASSES = 5
LABEL_NAMES = {
    0: "Center",
    1: "Lower Left",
    2: "Lower Right",
    3: "Upper Right",
    4: "Upper Left",
}
LABEL_COLORS = {0: "red", 1: "blue", 2: "green", 3: "orange", 4: "purple"}

MIN_VALUES = {
    0: 2267.266666666667,
    1: 2036.2666666666667,
    2: 2747.266666666667,
    3: 2826.766666666667,
    4: -14.563874340057373,
    5: 16.056903235117595,
    6: 28.741963958740236,
    7: 0.1536218995849291,
    8: 0.2225757986307144,
    9: 0.14313021103541054,
}
MAX_VALUES = {
    0: 2355.366666666667,
    1: 2112.3,
    2: 2841.733333333333,
    3: 2934.8333333333335,
    4: -13.832102203369141,
    5: 16.904297892252604,
    6: 30.707981554667153,
    7: 0.18265110005935034,
    8: 0.24830841223398845,
    9: 0.14518664876619972,
}


def streamlit_run():
    """
    Run the Streamlit app to visualize predictions.
    Args:
        data_path (os.PathLike): Path to the data file containing activations and labels.
        model_path (os.PathLike): Path to the model file (not used in this function).
    """
    # Constants
    PRED_FREQ = int(os.environ.get("PRED_FREQ", 10000))  # in ms

    configure_streamlit()
    # Auto-refresh
    st_autorefresh(interval=PRED_FREQ, limit=None, key="data_autorefresh")

    storage_path = Path(STORAGE_PATH)

    # Find all files matching the pattern "follow_touch_[FOLLOW_TOUCH_ID]_*.json" sorted by filename
    files = sorted(
        list(storage_path.glob(f"follow_touch_{FOLLOW_TOUCH_ID}_*.json")),
        key=lambda f: f.name,
    )
    if not files:
        st.warning(
            f"No matching data files found. Waiting for data to be generated in {storage_path}"
        )
        st.stop()

    if "processed_files" not in st.session_state:
        st.session_state.processed_files = set()
        st.session_state.predictions = []
        st.session_state.activations = []
        st.session_state.pca_buffer = []
        st.session_state.class_proto = {i: None for i in range(LABEL_CLASSES)}

    unprocessed_files = [
        f for f in files if str(f) not in st.session_state.processed_files
    ]

    if unprocessed_files:
        model_path = storage_path / f"params_{MODEL_INPUT_SIZE}"
        model = Predictor(model_path=model_path)
        for data_path in unprocessed_files:
            samples = load_data(data_path)
            print(f"Loaded {len(samples)} samples from {data_path}")
            samples = np.array([samples])
            # Apply min max normalization through min e max over the 0th axis
            samples = (samples - np.amin(samples, axis=0, keepdims=True)) / (
                np.amax(samples, axis=0, keepdims=True)
                - np.amin(samples, axis=0, keepdims=True)
            )
            pred, activations = model()
            st.session_state.predictions.extend(pred)
            st.session_state.activations.extend(activations)
            st.session_state.processed_files.add(str(data_path))

        # Update the PCA on all the activations
        pca = PCA(n_components=3)
        if len(st.session_state.predictions) == 1:
            pca = pca.fit(st.session_state.activations[0][-TRAJECTORY_LENGTH:])
        else:
            pca = pca.fit(
                np.concatenate(
                    [act[-TRAJECTORY_LENGTH:] for act in st.session_state.activations],
                    axis=0,
                )
            )
        st.session_state.pca_buffer = [
            pca.transform(act[-TRAJECTORY_LENGTH:])
            for act in st.session_state.activations
        ]

        # Update the prototypes of the PCA for each class
        class_labels = np.argmax(np.array(st.session_state.predictions), axis=-1)
        # Group all the PCA values by class
        for i in range(LABEL_CLASSES):
            pca_values = [
                st.session_state.pca_buffer[j][-1]
                for j in range(len(st.session_state.predictions))
                if class_labels[j] == i
            ]
            if len(pca_values) > 0:
                if len(pca_values) > 1:
                    # Stack the PCA values for each class
                    pca_values = np.stack(pca_values, axis=0)
                    # Calculate the mean and std of the PCA values for each class
                    st.session_state.class_proto[i] = (
                        np.mean(pca_values, axis=0),
                        np.random.random(3),  # np.std(pca_values, axis=0),
                    )
                else:
                    st.session_state.class_proto[i] = pca_values[0], np.zeros(3)
        print(
            f"Processed {st.session_state.processed_files}\n",
            f"Predictions: {st.session_state.predictions}\n",
            f"PCA Buffer: {st.session_state.pca_buffer}\n",
            f"Class prototypes:{st.session_state.class_proto}",
        )

    display_visualization(
        st.session_state.predictions,
        st.session_state.pca_buffer,
        st.session_state.class_proto,
    )


def configure_streamlit():
    """Configure Streamlit settings."""
    st.set_page_config(layout="wide")
    st.title("Predictions Visualization")


def process_fn(json_sample):
    json_sample = json_sample["t"]  # Getting a dict
    json_sample = json_sample[list(json_sample.keys())[0]]  # Getting a list
    json_sample = [
        (float(s["i"]) - float(s["b"])) for s in json_sample
    ]  # Removing bias
    return json_sample


def load_data(data_path: os.PathLike) -> list:
    """Load data from the specified JSON file."""
    if DEBUG == 1:
        try:
            with open(data_path, "r") as f:
                return json.load(f)
        except Exception as e:
            st.error(f"Error loading data: {e}")
            st.stop()
    else:

        try:

            with open(data_path, "r") as f:
                data = json.load(f)
            data = data[f"follow_touch_{FOLLOW_TOUCH_ID}"]
            data = map(process_fn, data)
            return list(data)

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


def display_visualization(predictions, pca_data, class_proto):
    """Display the PCA visualization with sidebar controls."""
    st.sidebar.write(
        f"Number of sequences (Touches): {len(st.session_state.processed_files)}"
    )
    DISPLAY_LIMIT = st.sidebar.slider(
        "Number of Sequences", min_value=1, max_value=100, value=5
    )
    max_time_index = max(len(st.session_state.pca_buffer) - DISPLAY_LIMIT, 0)
    TIME_SLIDER = st.sidebar.slider(
        "Index of the first sequence to show",
        min_value=0,
        max_value=max_time_index if max_time_index > 0 else 1,
        value=max_time_index,
    )
    if "pca_buffer" not in st.session_state or len(st.session_state.pca_buffer) == 0:
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
                    x=pca_data[idx][:, 0],
                    y=pca_data[idx][:, 1],
                    z=pca_data[idx][:, 2],
                    mode="markers+lines",
                    marker=dict(
                        size=[6] * (len(pca_data[idx]) - 1) + [8],
                        symbol=["circle"] * (len(pca_data[idx]) - 1) + ["cross"],
                        color=[LABEL_COLORS[label]] * len(pca_data[idx]),
                        opacity=0.9,
                    ),
                    line=dict(color=LABEL_COLORS[label], width=2),
                    name=LABEL_NAMES[label],
                    showlegend=show_legend,
                )
            )
        # Add class prototype points
        for class_id, proto in class_proto.items():
            if proto is not None and class_id in added_labels:
                mean, std = proto
                fig.add_trace(
                    go.Scatter3d(
                        x=[mean[0]],
                        y=[mean[1]],
                        z=[mean[2]],
                        mode="markers",
                        marker=dict(
                            size=8,
                            symbol="diamond",
                            color=LABEL_COLORS[class_id],
                            opacity=1.0,
                        ),
                        name=f"{LABEL_NAMES[class_id]} Proto",
                        showlegend=True,
                    )
                )

                # Generate a sphere to represent the std deviation, centered at the mean
                u, v = np.mgrid[0 : 2 * np.pi : 20j, 0 : np.pi : 10j]
                x = std[0] * np.sin(v) * np.cos(u) + mean[0]
                y = std[1] * np.sin(v) * np.sin(u) + mean[1]
                z = std[2] * np.cos(v) + mean[2]

                fig.add_trace(
                    go.Surface(
                        x=x,
                        y=y,
                        z=z,
                        showscale=False,
                        opacity=0.2,
                        surfacecolor=np.full_like(x, class_id),
                        colorscale=[
                            [0, LABEL_COLORS[class_id]],
                            [1, LABEL_COLORS[class_id]],
                        ],
                        name=f"{LABEL_NAMES[class_id]} Std",
                        showlegend=False,
                    )
                )
        fig.update_layout(
            scene=dict(xaxis_title="PC1", yaxis_title="PC2", zaxis_title="PC3"),
            title="3D PCA of RON Activations",
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
