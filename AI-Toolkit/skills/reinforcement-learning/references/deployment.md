# RL Deployment Guide

## Overview

Deploying RL models to production requires careful attention to model export, inference optimization, monitoring, and safety. This guide covers best practices for production-ready RL systems.

## Model Export

### ONNX Export

ONNX is the most portable target (ONNX Runtime runs on servers, edge devices, browsers, and from C++). This follows SB3's export guide. Two things matter: wrap the policy so it acts **deterministically** (calling `model.policy` directly samples random actions), and remember observation normalization isn't part of the network.

```python
import torch as th
from stable_baselines3 import PPO

class OnnxableSB3Policy(th.nn.Module):
    def __init__(self, policy):
        super().__init__()
        self.policy = policy

    def forward(self, observation: th.Tensor):
        # Includes SB3's observation preprocessing; returns (actions, values, log_prob) for PPO.
        return self.policy(observation, deterministic=True)

model = PPO.load("models/best.zip", device="cpu")
onnx_policy = OnnxableSB3Policy(model.policy).eval()
dummy = th.randn(1, *model.observation_space.shape)

# torch.distributions validates its arguments with data-dependent checks that
# torch.export can't trace; turn validation off for the export.
th.distributions.Distribution.set_default_validate_args(False)
th.onnx.export(onnx_policy, (dummy,), "policy.onnx", input_names=["observation"])
```

Tested with PyTorch 2.14 and SB3 2.9 (October 2026): the exported PPO policy matched `model.predict(deterministic=True)` on 200 of 200 observations. Notes:
- Recent PyTorch (2.9+) uses the `dynamo` exporter by default (it needs `pip install onnx onnxscript`). Leave `opset_version` unset unless the runtime needs a specific one; `dynamic_axes` is deprecated in favor of `dynamic_shapes`.
- If you plan to quantize with ONNX Runtime (below), export with the legacy exporter instead, `th.onnx.export(..., dynamo=False)`: ONNX Runtime's quantizer rejected the dynamo-exported graph in testing, while the legacy export quantized cleanly.
- For SAC/TD3, export only the actor: `self.actor(observation, deterministic=True)`.
- Continuous actions come out in the policy's normalized range; clip or unscale them to the action space yourself, as SB3's `predict()` does.
- If training used VecNormalize, apply the same normalization before inference: save `obs_rms.mean`, `obs_rms.var` and `epsilon` from the loaded VecNormalize, and compute `clip((obs - mean) / sqrt(var + eps), -clip_obs, clip_obs)`.
- Image policies expect channel-first input.

### ONNX Inference

```python
import numpy as np
import onnxruntime as ort

session = ort.InferenceSession("policy.onnx")
input_name = session.get_inputs()[0].name

def act(observation: np.ndarray) -> np.ndarray:
    obs = np.asarray(observation, dtype=np.float32)[None, ...]   # add batch dimension
    actions, values, log_prob = session.run(None, {input_name: obs})
    return actions[0]
```

Check the exported model against the original before shipping: for a few hundred observations, `act(obs)` should match `model.predict(obs, deterministic=True)[0]`.

### PyTorch-native export (`torch.export`)

TorchScript (`torch.jit.trace` / `torch.jit.script`) is deprecated in current PyTorch, which warns to move to `torch.export`. For a PyTorch-native artifact, export the same wrapper with `torch.export.export(onnx_policy, (dummy,))`, and for C++ deployment compile it with AOTInductor (`torch._inductor.aoti_compile_and_package(exported, package_path="policy.pt2")`), then load the `.pt2` from C++ (see the cpp-reinforcement-learning skill). These APIs are still evolving; check the PyTorch docs for the installed version.

---

## Inference Optimization

### Batched Inference

```python
import time
import numpy as np
import torch
from collections import deque

class BatchedInference:
    """Accumulate observations and run batched inference."""

    def __init__(self, model, batch_size=32, max_wait_ms=10):
        self.model = model
        self.batch_size = batch_size
        self.max_wait_ms = max_wait_ms
        self.pending = deque()
        self.last_batch_time = time.time()

    def add_observation(self, obs, callback):
        """Add observation to batch queue."""
        self.pending.append((obs, callback))

        # Check if should process batch
        if len(self.pending) >= self.batch_size:
            self._process_batch()
        elif (time.time() - self.last_batch_time) * 1000 > self.max_wait_ms:
            self._process_batch()

    def _process_batch(self):
        """Process accumulated observations."""
        if not self.pending:
            return

        # Collect observations
        obs_list = []
        callbacks = []
        while self.pending and len(obs_list) < self.batch_size:
            obs, callback = self.pending.popleft()
            obs_list.append(obs)
            callbacks.append(callback)

        # Batched inference
        obs_batch = np.stack(obs_list)
        with torch.no_grad():
            actions, _, _ = self.model.policy(torch.tensor(obs_batch).float())
            actions = actions.numpy()

        # Return results
        for action, callback in zip(actions, callbacks):
            callback(action)

        self.last_batch_time = time.time()
```

### GPU Optimization

```python
import torch

class GPUPolicy:
    """GPU-optimized policy inference."""

    def __init__(self, model_path, device="cuda"):
        self.device = torch.device(device if torch.cuda.is_available() else "cpu")

        # Load model to GPU
        model = PPO.load(model_path, device=self.device)
        self.policy = model.policy.to(self.device)
        self.policy.eval()

        # Use half precision for faster inference
        if self.device.type == "cuda":
            self.policy = self.policy.half()

    @torch.no_grad()
    def predict(self, observations):
        """Batched prediction on GPU."""
        obs_tensor = torch.tensor(observations, device=self.device)

        if self.device.type == "cuda":
            obs_tensor = obs_tensor.half()

        actions, _, _ = self.policy(obs_tensor)
        return actions.cpu().numpy()

    @torch.no_grad()
    def predict_single(self, observation):
        """Single observation prediction."""
        obs_tensor = torch.tensor(observation, device=self.device).unsqueeze(0)

        if self.device.type == "cuda":
            obs_tensor = obs_tensor.half()

        action, _, _ = self.policy(obs_tensor)
        return action.cpu().numpy()[0]
```

### Quantization

Quantization shrinks a policy and can speed up CPU inference; the networks are small, so measure before assuming it helps. The old `torch.quantization.quantize_dynamic` API is deprecated (PyTorch is moving it to the `torchao` package). Two current options:

```python
# 1) ONNX Runtime dynamic quantization (export with dynamo=False first; see the ONNX notes)
from onnxruntime.quantization import quantize_dynamic, QuantType
from onnxruntime.quantization.shape_inference import quant_pre_process
quant_pre_process("policy.onnx", "policy.pre.onnx", skip_symbolic_shape=True)
quantize_dynamic("policy.pre.onnx", "policy.int8.onnx", weight_type=QuantType.QInt8)

# 2) torchao, for PyTorch-native deployment (pip install torchao)
from torchao.quantization import quantize_, Int8DynamicActivationInt8WeightConfig
quantize_(onnx_policy, Int8DynamicActivationInt8WeightConfig())   # API names as of torchao 0.18; check its docs
```

Re-run the comparison against the original policy after quantizing; small value or action shifts can change behavior in sensitive tasks.
---

## Production Monitoring

### Metrics to Track

```python
from dataclasses import dataclass
from typing import List, Optional
import time
import logging

@dataclass
class InferenceMetrics:
    """Metrics for production monitoring."""
    latency_ms: float
    action: int
    observation_norm: float
    timestamp: float
    episode_id: str

class ProductionPolicy:
    """Policy wrapper with monitoring."""

    def __init__(self, model_path, metrics_logger=None):
        self.model = PPO.load(model_path)
        self.model.policy.eval()
        self.metrics_logger = metrics_logger or logging.getLogger(__name__)

        # Running statistics
        self.inference_count = 0
        self.total_latency = 0
        self.action_distribution = {}
        self.episode_rewards = []
        self.current_episode_reward = 0
        self.current_episode_id = None

    def predict(self, observation, episode_id=None):
        """Predict with monitoring."""
        start_time = time.time()

        # Get action
        action, _ = self.model.predict(observation, deterministic=True)

        # Calculate latency
        latency_ms = (time.time() - start_time) * 1000

        # Track metrics
        self.inference_count += 1
        self.total_latency += latency_ms

        # Track action distribution
        action_key = int(action) if isinstance(action, (int, np.integer)) else tuple(action)
        self.action_distribution[action_key] = self.action_distribution.get(action_key, 0) + 1

        # Log metrics
        metrics = InferenceMetrics(
            latency_ms=latency_ms,
            action=action_key,
            observation_norm=np.linalg.norm(observation),
            timestamp=time.time(),
            episode_id=episode_id or "unknown"
        )

        self._log_metrics(metrics)

        return action

    def record_reward(self, reward, done=False):
        """Track episode rewards."""
        self.current_episode_reward += reward

        if done:
            self.episode_rewards.append(self.current_episode_reward)
            self.current_episode_reward = 0

    def _log_metrics(self, metrics: InferenceMetrics):
        """Log metrics to monitoring system."""
        self.metrics_logger.info(
            f"inference latency_ms={metrics.latency_ms:.2f} "
            f"action={metrics.action} "
            f"obs_norm={metrics.observation_norm:.2f}"
        )

    def get_statistics(self):
        """Get aggregated statistics."""
        return {
            "total_inferences": self.inference_count,
            "avg_latency_ms": self.total_latency / max(1, self.inference_count),
            "action_distribution": self.action_distribution,
            "episodes_completed": len(self.episode_rewards),
            "avg_episode_reward": np.mean(self.episode_rewards) if self.episode_rewards else 0,
        }
```

### Alerting

```python
class PolicyMonitor:
    """Monitor policy for anomalies."""

    def __init__(self, policy, alert_callback):
        self.policy = policy
        self.alert_callback = alert_callback

        # Thresholds
        self.max_latency_ms = 100
        self.min_entropy = 0.1
        self.obs_range = (-10, 10)

        # Baselines (set from training)
        self.baseline_action_dist = None

    def check_latency(self, latency_ms):
        """Alert on high latency."""
        if latency_ms > self.max_latency_ms:
            self.alert_callback(
                "HIGH_LATENCY",
                f"Inference latency {latency_ms:.1f}ms exceeds threshold {self.max_latency_ms}ms"
            )

    def check_observation(self, observation):
        """Alert on out-of-distribution observations."""
        obs_min, obs_max = observation.min(), observation.max()

        if obs_min < self.obs_range[0] or obs_max > self.obs_range[1]:
            self.alert_callback(
                "OOD_OBSERVATION",
                f"Observation out of expected range: [{obs_min:.2f}, {obs_max:.2f}]"
            )

        if np.isnan(observation).any():
            self.alert_callback("NAN_OBSERVATION", "Observation contains NaN values")

    def check_action_distribution(self, recent_actions, window=1000):
        """Alert on distribution shift."""
        if len(recent_actions) < window:
            return

        if self.baseline_action_dist is None:
            return

        # Calculate current distribution
        current_dist = {}
        for a in recent_actions[-window:]:
            current_dist[a] = current_dist.get(a, 0) + 1

        # Chi-squared test for distribution shift
        # ... implementation

    def check_reward_degradation(self, recent_rewards, window=100):
        """Alert on performance degradation."""
        if len(recent_rewards) < window:
            return

        recent_mean = np.mean(recent_rewards[-window:])
        baseline_mean = np.mean(recent_rewards[:-window]) if len(recent_rewards) > window else recent_mean

        # Alert if performance drops significantly
        if recent_mean < baseline_mean * 0.8:  # 20% degradation
            self.alert_callback(
                "PERFORMANCE_DEGRADATION",
                f"Recent reward {recent_mean:.2f} is {(1 - recent_mean/baseline_mean)*100:.1f}% below baseline"
            )
```

### Prometheus/Grafana Integration

```python
from prometheus_client import Counter, Histogram, Gauge, start_http_server

# Define metrics
INFERENCE_COUNTER = Counter('rl_inference_total', 'Total inference calls')
INFERENCE_LATENCY = Histogram('rl_inference_latency_seconds', 'Inference latency')
EPISODE_REWARD = Gauge('rl_episode_reward', 'Latest episode reward')
ACTION_COUNTER = Counter('rl_action_total', 'Actions taken', ['action'])

class PrometheusPolicy:
    """Policy with Prometheus metrics."""

    def __init__(self, model_path, port=8000):
        self.model = PPO.load(model_path)
        start_http_server(port)  # Start metrics endpoint

    def predict(self, observation):
        INFERENCE_COUNTER.inc()

        with INFERENCE_LATENCY.time():
            action, _ = self.model.predict(observation, deterministic=True)

        ACTION_COUNTER.labels(action=str(action)).inc()

        return action

    def record_episode_end(self, reward):
        EPISODE_REWARD.set(reward)
```

---

## Safety Considerations

### Action Constraints

```python
import numpy as np

class SafePolicy:
    """Policy wrapper with safety constraints."""

    def __init__(self, model, action_bounds=None, safety_margin=0.1):
        self.model = model
        self.action_bounds = action_bounds
        self.safety_margin = safety_margin

    def predict(self, observation, state_constraints=None):
        """Predict with safety checks."""

        # Get raw action
        action, _ = self.model.predict(observation, deterministic=True)

        # Apply action bounds
        if self.action_bounds is not None:
            low, high = self.action_bounds
            action = np.clip(action, low, high)

        # Apply safety constraints
        if state_constraints is not None:
            action = self._apply_safety_constraints(observation, action, state_constraints)

        return action

    def _apply_safety_constraints(self, obs, action, constraints):
        """Modify action to satisfy safety constraints."""
        # Example: limit velocity changes
        if 'max_acceleration' in constraints:
            current_velocity = obs[1]  # Assuming velocity is in observation
            max_accel = constraints['max_acceleration']

            # Predict next velocity
            predicted_velocity = current_velocity + action * 0.1  # dt = 0.1

            # Clamp acceleration
            if abs(predicted_velocity - current_velocity) > max_accel:
                action = np.sign(action) * max_accel / 0.1

        return action
```

### Fallback Policies

```python
import logging

import numpy as np
from stable_baselines3 import PPO

class FallbackPolicy:
    """Primary policy with fallback on failure."""

    def __init__(self, primary_model_path, fallback_model_path=None):
        self.primary = PPO.load(primary_model_path)
        self.fallback = PPO.load(fallback_model_path) if fallback_model_path else None
        self.use_fallback = False
        self.error_count = 0
        self.max_errors = 5

    def predict(self, observation):
        """Predict with fallback on error."""
        try:
            if self.use_fallback and self.fallback:
                return self._fallback_predict(observation)

            action, _ = self.primary.predict(observation, deterministic=True)

            # Validate action
            if np.isnan(action).any() or np.isinf(action).any():
                raise ValueError("Invalid action from primary policy")

            # Reset error count on success
            self.error_count = 0
            return action

        except Exception as e:
            self.error_count += 1
            logging.error(f"Primary policy error: {e}")

            if self.error_count >= self.max_errors:
                self.use_fallback = True
                logging.warning("Switching to fallback policy")

            return self._fallback_predict(observation)

    def _fallback_predict(self, observation):
        """Safe fallback action."""
        if self.fallback:
            return self.fallback.predict(observation, deterministic=True)[0]
        else:
            # Return neutral/safe action
            return np.zeros(self.primary.action_space.shape)
```

### Human Override

```python
class HumanOverridablePolicy:
    """Policy that allows human override."""

    def __init__(self, model, override_callback=None):
        self.model = model
        self.override_callback = override_callback
        self.override_active = False
        self.human_action = None

    def predict(self, observation):
        """Get action, allowing human override."""

        # Check for override
        if self.override_callback:
            override = self.override_callback(observation)
            if override is not None:
                return override

        if self.override_active and self.human_action is not None:
            return self.human_action

        return self.model.predict(observation, deterministic=True)[0]

    def set_human_action(self, action):
        """Set human override action."""
        self.human_action = action
        self.override_active = True

    def release_override(self):
        """Return control to AI."""
        self.override_active = False
        self.human_action = None
```

---

## Online Learning Patterns

### Continuous Learning

```python
import logging
from collections import deque

import numpy as np
from stable_baselines3 import PPO

class OnlineLearningPolicy:
    """Policy that continues learning in production."""

    def __init__(self, model_path, buffer_size=10000, update_freq=1000):
        self.model = PPO.load(model_path)
        self.buffer = deque(maxlen=buffer_size)
        self.update_freq = update_freq
        self.step_count = 0

    def predict(self, observation):
        """Predict action."""
        action, _ = self.model.predict(observation, deterministic=False)  # Stochastic for exploration
        return action

    def record_transition(self, obs, action, reward, next_obs, done):
        """Record transition for learning."""
        self.buffer.append((obs, action, reward, next_obs, done))
        self.step_count += 1

        if self.step_count % self.update_freq == 0:
            self._update()

    def _update(self):
        """Update policy from buffer."""
        if len(self.buffer) < self.update_freq:
            return

        # Sample batch
        batch = list(self.buffer)[-self.update_freq:]

        # Convert to training format
        # ... implementation depends on algorithm

        # Fine-tune model
        # self.model.learn(...)

        logging.info(f"Policy updated at step {self.step_count}")
```

### A/B Testing

```python
import random
import hashlib

class ABTestPolicy:
    """A/B testing between policies."""

    def __init__(self, policy_a, policy_b, traffic_split=0.5):
        self.policy_a = policy_a
        self.policy_b = policy_b
        self.traffic_split = traffic_split

        self.metrics_a = {"rewards": [], "count": 0}
        self.metrics_b = {"rewards": [], "count": 0}

    def predict(self, observation, user_id=None):
        """Route to policy based on user_id or random."""

        # Deterministic routing for same user
        if user_id:
            hash_val = int(hashlib.md5(user_id.encode()).hexdigest(), 16)
            use_a = (hash_val % 100) < (self.traffic_split * 100)
        else:
            use_a = random.random() < self.traffic_split

        if use_a:
            self.metrics_a["count"] += 1
            return self.policy_a.predict(observation), "A"
        else:
            self.metrics_b["count"] += 1
            return self.policy_b.predict(observation), "B"

    def record_reward(self, reward, variant):
        """Record reward for variant."""
        if variant == "A":
            self.metrics_a["rewards"].append(reward)
        else:
            self.metrics_b["rewards"].append(reward)

    def get_results(self):
        """Get A/B test results."""
        mean_a = np.mean(self.metrics_a["rewards"]) if self.metrics_a["rewards"] else 0
        mean_b = np.mean(self.metrics_b["rewards"]) if self.metrics_b["rewards"] else 0

        return {
            "policy_a": {
                "count": self.metrics_a["count"],
                "mean_reward": mean_a,
                "total_rewards": len(self.metrics_a["rewards"])
            },
            "policy_b": {
                "count": self.metrics_b["count"],
                "mean_reward": mean_b,
                "total_rewards": len(self.metrics_b["rewards"])
            },
            "winner": "A" if mean_a > mean_b else "B",
            "improvement": abs(mean_a - mean_b) / max(mean_a, mean_b, 1) * 100
        }
```

---

## Deployment Checklist

### Pre-Deployment

- [ ] Model exported to ONNX/TorchScript
- [ ] Inference latency benchmarked
- [ ] Memory usage profiled
- [ ] Input validation implemented
- [ ] Action bounds enforced
- [ ] Fallback policy configured
- [ ] Monitoring metrics defined
- [ ] Alerting thresholds set
- [ ] Logging configured
- [ ] A/B test plan ready

### Post-Deployment

- [ ] Latency within SLA
- [ ] No NaN/Inf in outputs
- [ ] Action distribution stable
- [ ] Reward not degrading
- [ ] Error rate acceptable
- [ ] Resource usage stable
- [ ] Alerts working
- [ ] Rollback tested
