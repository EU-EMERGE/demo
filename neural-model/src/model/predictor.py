import os
import torch
import numpy as np

from sklearn.preprocessing import StandardScaler

from .ron import RandomizedOscillatorsNetwork

MODEL_INPUT_SIZE = int(os.getenv("MODEL_INPUT_SIZE", 4))


class Predictor:

    def __init__(self, model_path: str):
        n_hid = 100
        dt = 0.2
        gamma = 1
        gamma_range = 0.5
        epsilon = 2
        epsilon_range = 1
        rho = 0.9
        inp_scaling = 1
        device = "cpu"

        gamma = (gamma - gamma_range / 2.0, gamma + gamma_range / 2.0)
        epsilon = (
            epsilon - epsilon_range / 2.0,
            epsilon + epsilon_range / 2.0,
        )
        self.model = RandomizedOscillatorsNetwork(
            n_inp=MODEL_INPUT_SIZE,
            n_hid=n_hid,
            dt=dt,
            gamma=gamma,
            epsilon=epsilon,
            diffusive_gamma=0,
            rho=rho,
            input_scaling=inp_scaling,
            topology="full",
            reservoir_scaler=0,
            sparsity=0.99,
            device=device,
        ).to(device)
        self.model.load_state_dict(
            torch.load(
                os.path.join(model_path, "ron.pt"),
                weights_only=True,
                map_location="cpu",
            )
        )

        self.scaler = StandardScaler()
        m, v = torch.load(os.path.join(model_path, "scaler.pt"), map_location="cpu")
        self.scaler.mean_ = m.numpy()
        self.scaler.var_ = v.numpy()
        self.scaler.scale_ = np.sqrt(self.scaler.var_)

        self.readout = torch.nn.Linear(n_hid, 5)
        self.readout.load_state_dict(
            torch.load(
                os.path.join(model_path, "readout.pt"),
                weights_only=True,
                map_location="cpu",
            )
        )

    @torch.no_grad()
    def __call__(self, x):
        x = torch.from_numpy(x).float().to(self.model.device)
        h = self.model(x).cpu().numpy()
        h_to_pred = np.stack(
            [self.scaler.transform(h[i]) for i in range(h.shape[0])], axis=0
        )
        h_to_pred = torch.from_numpy(h_to_pred).float().to(self.model.device)
        pred = self.readout(h_to_pred[:, -1])
        pred = torch.softmax(pred, dim=-1)
        # Create a random sample the same size as the prediction for testing
        # pred = torch.softmax(torch.randn(*pred.shape), dim=-1)
        return pred.cpu().numpy(), h
