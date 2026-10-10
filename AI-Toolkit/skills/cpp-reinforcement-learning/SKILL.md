---
name: cpp-reinforcement-learning
description: Reinforcement learning in C++ with LibTorch (the PyTorch C++ frontend) and C++20. Use when the user is implementing DQN, PPO or SAC in C++, building a replay buffer or rollout buffer in C++, fixing libtorch memory growth or GPU issues in a C++ agent, running environments in parallel threads, or loading a policy trained in Python into a C++ program (games, robotics, simulators). Not for Python RL with Gymnasium or Stable-Baselines3, including exporting a Python policy to ONNX (use reinforcement-learning), or for general deep learning (use deep-learning).
---

# C++ reinforcement learning

Help the user build RL in C++ that is correct first and fast second. The C++ frontend mirrors PyTorch's Python API closely, so a good approach is often to get the algorithm right against a Python reference (Stable-Baselines3 or CleanRL) and then translate it, checking the outputs match.

LibTorch changes between releases, and current versions require C++20. Check the version the user builds against (it's in `<libtorch>/build-version`) before relying on an API, and if a docs or web tool is available, look up anything you're unsure of.

## Core Libraries

### Primary: LibTorch (PyTorch C++ Frontend)

LibTorch provides the same tensor operations and autograd capabilities as PyTorch in C++.

**Installation**: Download from https://pytorch.org/get-started/locally (select C++/LibTorch)

**CMake Integration**:
```cmake
cmake_minimum_required(VERSION 3.18)
project(rl_project)

set(CMAKE_CXX_STANDARD 20)   # current libtorch requires C++20
find_package(Torch REQUIRED)

add_executable(train_agent src/main.cpp)
target_link_libraries(train_agent "${TORCH_LIBRARIES}")
```

### Other pieces

- **ONNX Runtime**: cross-platform inference for policies exported from Python
- **AOTInductor (`.pt2` packages)**: the current way to run a Python-exported PyTorch model from C++; TorchScript is deprecated (see `references/libtorch.md`)
- **Environments**: there's no standard C++ Gymnasium; most projects wrap their own simulator behind a small `reset()`/`step()` interface

## Quick Start: DQN Agent

```cpp
#include <torch/torch.h>

struct DQNNet : torch::nn::Module {
    torch::nn::Linear fc1{nullptr}, fc2{nullptr}, fc3{nullptr};

    DQNNet(int64_t state_dim, int64_t action_dim) {
        fc1 = register_module("fc1", torch::nn::Linear(state_dim, 128));
        fc2 = register_module("fc2", torch::nn::Linear(128, 128));
        fc3 = register_module("fc3", torch::nn::Linear(128, action_dim));
    }

    torch::Tensor forward(torch::Tensor x) {
        x = torch::relu(fc1->forward(x));
        x = torch::relu(fc2->forward(x));
        return fc3->forward(x);
    }
};

// Training loop
auto policy_net = std::make_shared<DQNNet>(state_dim, action_dim);
auto target_net = std::make_shared<DQNNet>(state_dim, action_dim);
torch::optim::Adam optimizer(policy_net->parameters(), lr);

// Compute loss
auto q_values = policy_net->forward(states).gather(1, actions);
// Tensor::max(dim) returns std::tuple<values, indices> in C++
auto next_q = std::get<0>(target_net->forward(next_states).max(1)).detach();
auto target = rewards + gamma * next_q * (1 - dones);
auto loss = torch::mse_loss(q_values.squeeze(), target);

// Backward pass
optimizer.zero_grad();
loss.backward();
optimizer.step();
```

## Essential Patterns

### Replay Buffer (Ring Buffer)

```cpp
class ReplayBuffer {
public:
    explicit ReplayBuffer(size_t capacity)
        : capacity_(capacity), position_(0), size_(0) {
        buffer_.reserve(capacity);
    }

    void push(Experience exp) {
        if (buffer_.size() < capacity_) {
            buffer_.push_back(std::move(exp));
        } else {
            buffer_[position_] = std::move(exp);
        }
        position_ = (position_ + 1) % capacity_;
        size_ = std::min(size_ + 1, capacity_);
    }

    std::vector<Experience> sample(size_t batch_size);

private:
    std::vector<Experience> buffer_;
    size_t capacity_, position_, size_;
    std::mt19937 rng_{std::random_device{}()};
};
```

### GPU Device Management

```cpp
torch::Device device = torch::cuda::is_available() ? torch::kCUDA : torch::kCPU;
model->to(device);

// Create tensors on device
auto tensor = torch::zeros({batch_size, state_dim},
    torch::TensorOptions().device(device).dtype(torch::kFloat32));
```

### Inference Mode

```cpp
{
    torch::NoGradGuard no_grad;
    auto action_values = model->forward(state);
    auto action = action_values.argmax(1);
}
```

## Common Pitfalls

1. **Forgetting train/eval mode** - Call `model->train()` or `model->eval()`
2. **Missing NoGradGuard** - Use for inference to save memory
3. **Tensor accumulation** - Use `.detach()` for stored tensors
4. **Thread safety** - Clone models for parallel threads
5. **Device mismatch** - Verify all tensors on same device

## Reference Files

- [references/libtorch.md](references/libtorch.md) - LibTorch setup and API guide
- [references/algorithms.md](references/algorithms.md) - DQN, PPO, SAC implementations
- [references/memory-management.md](references/memory-management.md) - Replay buffers, smart pointers, RAII
- [references/performance.md](references/performance.md) - Optimization, parallelization, GPU
- [references/testing.md](references/testing.md) - Testing and debugging strategies
