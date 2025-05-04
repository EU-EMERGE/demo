import numpy as np
import time
import os

DATA_FILE = "activation_data.npz"
HIDDEN_DIM = 50
LABEL_CLASSES = 5
BATCH_SIZE = 5
MAX_BUFFER = 200

# Initialize or load
if os.path.exists(DATA_FILE):
    existing = np.load(DATA_FILE)
    activations = existing["activations"]
    labels = existing["labels"]
else:
    activations = np.empty((0, HIDDEN_DIM))
    labels = np.empty((0,), dtype=int)

while True:
    new_acts = np.random.randn(BATCH_SIZE, HIDDEN_DIM)
    new_lbls = np.random.randint(0, LABEL_CLASSES, size=(BATCH_SIZE,))

    activations = np.concatenate([activations, new_acts], axis=0)[-MAX_BUFFER:]
    labels = np.concatenate([labels, new_lbls], axis=0)[-MAX_BUFFER:]

    np.savez(DATA_FILE, activations=activations, labels=labels)
    print(f"Appended batch. Total: {len(activations)}")
    time.sleep(1)
