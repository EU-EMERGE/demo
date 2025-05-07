import os

from src import streamlit_run

STORAGE_PATH = os.getenv("STORAGE_PATH")

if __name__ == "__main__":
    if STORAGE_PATH is None:
        raise ValueError(
            "STORAGE_PATH environment variable is not set. Please set it to the path of the data file."
        )
    streamlit_run(STORAGE_PATH)
