---
name: cpp-reinforcement-learning
description: |
  C++ Reinforcement Learning best practices using libtorch (PyTorch C++ frontend) and modern C++17/20.
  Use when:
  - Implementing RL algorithms in C++ for performance-critical applications
  - Building production RL systems with libtorch
  - Creating replay buffers and experience storage
  - Optimizing RL training with GPU acceleration
  - Deploying RL models with ONNX Runtime
---

# C++ Reinforcement Learning

## Overview

This skill covers implementing reinforcement learning algorithms in C++ using LibTorch (PyTorch C++ frontend) and modern C++17/20 features. It provides patterns for building high-performance RL systems suitable for production deployment, robotics, game AI, and real-time applications.

## When to Use

- Implementing DQN, PPO, SAC, or other RL algorithms in C++
- Building performance-critical RL training pipelines
- Creating efficient replay buffers with proper memory management
- Deploying trained models with ONNX Runtime
- Parallelizing environment rollouts across threads
- Integrating RL with existing C++ codebases (games, robotics, simulations)

## Core Libraries

### Primary: LibTorch (PyTorch C++ Frontend)

LibTorch provides the same tensor operations and autograd capabilities as PyTorch in C++.

**Installation**: Download from https://pytorch.org/get-started/locally (select C++/LibTorch)

**CMake Integration**:
```cmake
cmake_minimum_required(VERSION 3.18)
project(rl_project)

set(CMAKE_CXX_STANDARD 17)
find_package(Torch REQUIRED)

add_executable(train_agent src/main.cpp)
target_link_libraries(train_agent "${TORCH_LIBRARIES}")
```

### Secondary Libraries

- **ONNX Runtime** - Cross-platform inference deployment
- **cpprl** (mhubii/cpprl) - Reference PPO implementation
- **Gymnasium C++ bindings** - Environment interfaces

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
auto next_q = target_net->forward(next_states).max(1).values.detach();
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
