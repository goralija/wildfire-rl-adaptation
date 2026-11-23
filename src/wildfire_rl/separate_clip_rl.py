"""Opt-in TASK046 grouping; train method derived from sb3-contrib2.7.1 (MIT).

MIT License

Copyright (c) 2020 Stable-Baselines Team

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

"""
import numpy as np
import torch as th
from torch.nn import functional as F
from gymnasium import spaces
from sb3_contrib import MaskablePPO
from stable_baselines3.common.utils import explained_variance
from .common_control_rl import ShapeOnlyEnv,PPO_SETTINGS

CLIPPING_VERSION='common-separate-actor-critic-clip-v1'


def parameter_groups(named):
    groups={'actor':[],'critic':[]};seen=set()
    for name,p in named:
        if not p.requires_grad:continue
        if id(p) in seen:raise ValueError('shared trainable parameter')
        seen.add(id(p))
        if name.startswith(('mlp_extractor.policy_net.','action_net.')):group='actor'
        elif name.startswith(('mlp_extractor.value_net.','value_net.')):group='critic'
        else:raise ValueError('unexpected trainable parameter: '+name)
        groups[group].append(p)
    if not all(groups.values()):raise ValueError('both nonempty trainable groups required')
    return groups


def norm(tensors):
    return float(np.sqrt(sum(float(x.detach().double().square().sum()) for x in tensors)))


def clip_named_gradients(named,max_norm):
    if not np.isfinite(max_norm) or max_norm<=0:raise ValueError('positive finite maxnorm required')
    groups=parameter_groups(named)
    # Check all groups before mutating either one.
    if any(not th.isfinite(p.grad).all() for ps in groups.values() for p in ps if p.grad is not None):
        raise ValueError('nonfinite gradient')
    result={}
    for group,ps in groups.items():
        before=norm([p.grad for p in ps if p.grad is not None])
        th.nn.utils.clip_grad_norm_(ps,max_norm,error_if_nonfinite=True)
        after=norm([p.grad for p in ps if p.grad is not None])
        if not np.isfinite([before,after]).all() or after>max_norm+1e-6:raise ValueError('group gradient bound failed')
        result[group]=dict(before=before,after=after,retained_fraction=after/before if before else None)
    return result


class SeparateClipPPO(MaskablePPO):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        parameter_groups(self.policy.named_parameters(remove_duplicate=False))
        self.clip_history=[]

    def _clip_gradients(self):
        self.clip_history.append(clip_named_gradients(self.policy.named_parameters(remove_duplicate=False),self.max_grad_norm))

    def train(self) -> None:
        """
        Update policy using the currently gathered rollout buffer.
        """
        # Switch to train mode (this affects batch norm / dropout)
        self.policy.set_training_mode(True)
        # Update optimizer learning rate
        self._update_learning_rate(self.policy.optimizer)
        # Compute current clip range
        clip_range = self.clip_range(self._current_progress_remaining)  # type: ignore[operator]
        # Optional: clip range for the value function
        if self.clip_range_vf is not None:
            clip_range_vf = self.clip_range_vf(self._current_progress_remaining)  # type: ignore[operator]

        entropy_losses = []
        pg_losses, value_losses = [], []
        clip_fractions = []

        continue_training = True

        # train for n_epochs epochs
        for epoch in range(self.n_epochs):
            approx_kl_divs = []
            # Do a complete pass on the rollout buffer
            for rollout_data in self.rollout_buffer.get(self.batch_size):
                actions = rollout_data.actions
                if isinstance(self.action_space, spaces.Discrete):
                    # Convert discrete action from float to long
                    actions = rollout_data.actions.long().flatten()

                values, log_prob, entropy = self.policy.evaluate_actions(
                    rollout_data.observations,
                    actions,
                    action_masks=rollout_data.action_masks,
                )

                values = values.flatten()
                # Normalize advantage
                advantages = rollout_data.advantages
                if self.normalize_advantage:
                    advantages = (advantages - advantages.mean()) / (advantages.std() + 1e-8)

                # ratio between old and new policy, should be one at the first iteration
                ratio = th.exp(log_prob - rollout_data.old_log_prob)

                # clipped surrogate loss
                policy_loss_1 = advantages * ratio
                policy_loss_2 = advantages * th.clamp(ratio, 1 - clip_range, 1 + clip_range)
                policy_loss = -th.min(policy_loss_1, policy_loss_2).mean()

                # Logging
                pg_losses.append(policy_loss.item())
                clip_fraction = th.mean((th.abs(ratio - 1) > clip_range).float()).item()
                clip_fractions.append(clip_fraction)

                if self.clip_range_vf is None:
                    # No clipping
                    values_pred = values
                else:
                    # Clip the different between old and new value
                    # NOTE: this depends on the reward scaling
                    values_pred = rollout_data.old_values + th.clamp(
                        values - rollout_data.old_values, -clip_range_vf, clip_range_vf
                    )
                # Value loss using the TD(gae_lambda) target
                value_loss = F.mse_loss(rollout_data.returns, values_pred)
                value_losses.append(value_loss.item())

                # Entropy loss favor exploration
                if entropy is None:
                    # Approximate entropy when no analytical form
                    entropy_loss = -th.mean(-log_prob)
                else:
                    entropy_loss = -th.mean(entropy)

                entropy_losses.append(entropy_loss.item())

                loss = policy_loss + self.ent_coef * entropy_loss + self.vf_coef * value_loss

                # Calculate approximate form of reverse KL Divergence for early stopping
                # see issue #417: https://github.com/DLR-RM/stable-baselines3/issues/417
                # and discussion in PR #419: https://github.com/DLR-RM/stable-baselines3/pull/419
                # and Schulman blog: http://joschu.net/blog/kl-approx.html
                with th.no_grad():
                    log_ratio = log_prob - rollout_data.old_log_prob
                    approx_kl_div = th.mean((th.exp(log_ratio) - 1) - log_ratio).cpu().numpy()
                    approx_kl_divs.append(approx_kl_div)

                if self.target_kl is not None and approx_kl_div > 1.5 * self.target_kl:
                    continue_training = False
                    if self.verbose >= 1:
                        print(f"Early stopping at step {epoch} due to reaching max kl: {approx_kl_div:.2f}")
                    break

                # Optimization step
                self.policy.optimizer.zero_grad()
                loss.backward()
                # Clip grad norm
                self._clip_gradients()
                self.policy.optimizer.step()

            if not continue_training:
                break

        self._n_updates += self.n_epochs
        explained_var = explained_variance(self.rollout_buffer.values.flatten(), self.rollout_buffer.returns.flatten())

        # Logs
        self.logger.record("train/entropy_loss", np.mean(entropy_losses))
        self.logger.record("train/policy_gradient_loss", np.mean(pg_losses))
        self.logger.record("train/value_loss", np.mean(value_losses))
        self.logger.record("train/approx_kl", np.mean(approx_kl_divs))
        self.logger.record("train/clip_fraction", np.mean(clip_fractions))
        self.logger.record("train/loss", loss.item())
        self.logger.record("train/explained_variance", explained_var)
        self.logger.record("train/n_updates", self._n_updates, exclude="tensorboard")
        self.logger.record("train/clip_range", clip_range)
        if self.clip_range_vf is not None:
            self.logger.record("train/clip_range_vf", clip_range_vf)


def create_model(env=None,seed=0,settings=None):
    return SeparateClipPPO('MlpPolicy',ShapeOnlyEnv() if env is None else env,
        policy_kwargs=dict(net_arch=dict(pi=[64,64],vf=[64,64])),seed=seed,device='cpu',verbose=0,
        **(PPO_SETTINGS if settings is None else settings))
