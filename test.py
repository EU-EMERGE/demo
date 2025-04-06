import json
import random
import time

config = {
    "layers": [
        [10],
        [8],
        [5],
    ]
}


def generate_activation(layer_size):
    return [random.uniform(0, 1) for _ in range(layer_size)]


def update_activations():
    activations = []
    for layer in config["layers"]:
        activations.append(generate_activation(layer[0]))

    with open("activations.json", "w") as f:
        json.dump(activations, f, indent=4)

    print("Activations updated!")


if __name__ == "__main__":
    while True:
        update_activations()
        time.sleep(1)
