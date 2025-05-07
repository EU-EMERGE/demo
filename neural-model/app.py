import os
from src import streamlit_run

SENSORS_DATA = os.getenv(
    "SENSORS_DATA",
    "/Users/vdecaro/Desktop/Code/demo/follow-touch/follow_touch_[0-3].json",
)
MODEL_PATH = os.getenv("MODEL_PATH", default="./params")

if __name__ == "__main__":
    streamlit_run(SENSORS_DATA, MODEL_PATH)
