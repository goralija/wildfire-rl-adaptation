"""Small CNN features for MaskablePPO on the 128x128 SimFire cohort maps."""

from __future__ import annotations

import torch as th
from gymnasium import spaces
from stable_baselines3.common.torch_layers import BaseFeaturesExtractor
from torch import nn


class SimFireMapStateExtractor(BaseFeaturesExtractor):
    """Compress map channels spatially before the 16k-action policy head."""

    def __init__(self, observation_space: spaces.Dict, features_dim: int = 2311) -> None:
        map_space = observation_space.spaces["map"]
        state_space = observation_space.spaces["state"]
        self.state_dim = int(state_space.shape[0])
        super().__init__(observation_space, features_dim=features_dim)
        channels = int(map_space.shape[0])
        self.cnn = nn.Sequential(
            nn.Conv2d(channels, 32, kernel_size=8, stride=4),
            nn.ReLU(),
            nn.Conv2d(32, 64, kernel_size=4, stride=2),
            nn.ReLU(),
            nn.Conv2d(64, 64, kernel_size=3, stride=2),
            nn.ReLU(),
            nn.Flatten(),
        )
        with th.no_grad():
            spatial_features = int(self.cnn(th.zeros(1, *map_space.shape)).shape[1])
        self._features_dim = spatial_features + self.state_dim

    def forward(self, observations: dict[str, th.Tensor]) -> th.Tensor:
        spatial = self.cnn(observations["map"])
        state = observations["state"]
        return th.cat((spatial, state), dim=1)


def simfire_policy_kwargs() -> dict:
    """Policy configuration shared by PPO training and evaluation scripts."""
    return {
        "features_extractor_class": SimFireMapStateExtractor,
        "features_extractor_kwargs": {"features_dim": 2311},
        "net_arch": {"pi": [256, 256], "vf": [256, 256]},
    }
