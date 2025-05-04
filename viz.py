import streamlit as st
import numpy as np
import plotly.graph_objs as go
from sklearn.decomposition import PCA
import os
from streamlit_autorefresh import st_autorefresh

# === File settings ===
DATA_FILE = "activation_data.npz"

# === UI Setup ===
st.set_page_config(layout="wide")
st.title("📡 PCA of RNN Activations from File (Auto-Refreshing)")

# Auto-refresh every 1000ms
st_autorefresh(interval=1000, limit=None, key="data_autorefresh")

# === Sidebar controls ===
hidden_dim = st.sidebar.slider("Hidden Dimensionality", 10, 200, 50)
display_limit = st.sidebar.slider(
    "Number of Points to Display (-1 = All)", min_value=-1, max_value=100, value=-1
)

# === Label mapping ===
LABEL_CLASSES = 5
label_names = {i: f"Class {chr(65 + i)}" for i in range(LABEL_CLASSES)}
label_colors = {0: "red", 1: "blue", 2: "green", 3: "orange", 4: "purple"}

# === Load data ===
if os.path.exists(DATA_FILE):
    try:
        with np.load(DATA_FILE) as data:
            activations = data["activations"]
            labels = data["labels"]
    except Exception as e:
        st.error(f"Failed to read file: {e}")
        st.stop()

    # === Dimension check ===
    if activations.shape[1] != hidden_dim:
        st.warning(
            f"Mismatch: file has dim {activations.shape[1]}, expected {hidden_dim}"
        )
        st.stop()

    # === Apply display limit ===
    if display_limit != -1:
        activations = activations[-display_limit:]
        labels = labels[-display_limit:]

    if len(activations) < 3:
        st.warning("Not enough data to display (need at least 3 activations).")
        st.stop()

    # === PCA and 3D Plot ===
    pca = PCA(n_components=3)
    reduced = pca.fit_transform(activations)

    fig = go.Figure()
    for label in np.unique(labels):
        idx = labels == label
        fig.add_trace(
            go.Scatter3d(
                x=reduced[idx, 0],
                y=reduced[idx, 1],
                z=reduced[idx, 2],
                mode="markers+lines",
                marker=dict(size=6, color=label_colors[label], opacity=0.9),
                line=dict(color=label_colors[label], width=2),
                name=label_names[label],
                showlegend=True,
            )
        )

    fig.update_layout(
        scene=dict(xaxis_title="PC1", yaxis_title="PC2", zaxis_title="PC3"),
        title="3D PCA of Buffered RNN Activations",
        margin=dict(l=0, r=0, t=50, b=0),
        legend=dict(title="Predicted Labels", itemsizing="constant"),
    )
    st.plotly_chart(fig, use_container_width=True)

else:
    st.warning("Waiting for activation data file...")
