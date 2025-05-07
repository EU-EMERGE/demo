import numpy as np
import time
import json
import os

OUTPUT_FILE = "follow_touch_[0-3].json"
FEATURE_DIM = 10
SAMPLING_FREQ = 10
UPDATE_FREQ = 1000


def generate_sample():
    return [np.random.randn(FEATURE_DIM).tolist() for _ in range(SAMPLING_FREQ)]


def main():
    if os.path.exists(OUTPUT_FILE):
        with open(OUTPUT_FILE, "r") as f:
            data = json.load(f)
    else:
        data = []

    while True:
        data += generate_sample()

        with open(OUTPUT_FILE, "w") as f:
            json.dump(data, f)

        print(f"Wrote sample. Total samples: {len(data)}")
        time.sleep(UPDATE_FREQ / 1000)  # Convert ms to seconds

        if len(data) > 1000:
            print("Reached 1000 samples, stopping.")
            break


if __name__ == "__main__":
    main()
