import numpy as np
import time
import json
import os

OUTPUT_DIR = "/Users/vdecaro/Desktop/Code/demo/storage"
SEQ_LEN = 50
FEATURE_DIM = 10
SAMPLING_FREQ = 10
UPDATE_FREQ = 1000


def generate_sample():
    return [np.random.randn(FEATURE_DIM).tolist() for _ in range(SAMPLING_FREQ)]


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    for i in range(20):
        sample = [np.random.randn(10).tolist() for _ in range(SEQ_LEN)]
        timestamp = int(time.time() * 1000)
        filename = f"{OUTPUT_DIR}/follow_touch_0_{timestamp}.json"
        with open(filename, "w") as f:
            json.dump(sample, f)
        print(f"Wrote file: {filename}")
        time.sleep(UPDATE_FREQ / 1000)


if __name__ == "__main__":
    main()
