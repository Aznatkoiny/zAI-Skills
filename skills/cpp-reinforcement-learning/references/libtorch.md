# LibTorch (PyTorch C++ Frontend) Guide

## Overview

LibTorch is the C++ distribution of PyTorch, providing the same tensor operations, autograd, and neural network modules available in Python. It is the recommended library for implementing RL algorithms in C++ due to its maturity, documentation, and seamless model interoperability with Python PyTorch.

## Installation

### Download Pre-built LibTorch

1. Visit https://pytorch.org/get-started/locally
2. Select:
   - PyTorch Build: Stable (2.x)
   - OS: Linux/Mac/Windows
   - Package: LibTorch
   - Language: C++/Java
   - CUDA: Select appropriate version (or CPU)
3. Download and extract to a known location (e.g., `/opt/libtorch`)

### Build from Source (Optional)

```bash
git clone --recursive https://github.com/pytorch/pytorch
cd pytorch
mkdir build && cd build
cmake .. -DBUILD_SHARED_LIBS=ON -DCMAKE_INSTALL_PREFIX=/opt/libtorch
make -j$(nproc)
make install
```

## CMake Integration

### Basic CMakeLists.txt

```cmake
cmake_minimum_required(VERSION 3.18)
project(rl_project)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Find LibTorch
list(APPEND CMAKE_PREFIX_PATH "/opt/libtorch")
find_package(Torch REQUIRED)

# Define executable
add_executable(train_agent
    src/main.cpp
    src/dqn.cpp
    src/replay_buffer.cpp
    src/environment.cpp
)

target_link_libraries(train_agent "${TORCH_LIBRARIES}")

# Required for MSVC
if (MSVC)
    file(GLOB TORCH_DLLS "${TORCH_INSTALL_PREFIX}/lib/*.dll")
    add_custom_command(TARGET train_agent POST_BUILD
        COMMAND ${CMAKE_COMMAND} -E copy_if_different
        ${TORCH_DLLS} $<TARGET_FILE_DIR:train_agent>)
endif()
```

### Building with CUDA Support

```cmake
# CMake automatically detects CUDA if LibTorch was built with CUDA
find_package(Torch REQUIRED)

# Verify CUDA is available
message(STATUS "CUDA available: ${TORCH_CUDA_AVAILABLE}")
```

### Build Commands

```bash
mkdir build && cd build
cmake .. -DCMAKE_PREFIX_PATH=/opt/libtorch
make -j$(nproc)
```

## Core API Reference

### Tensor Creation

```cpp
#include <torch/torch.h>

// Create tensors
auto zeros = torch::zeros({3, 4});                    // 3x4 zeros
auto ones = torch::ones({3, 4});                      // 3x4 ones
auto rand = torch::rand({3, 4});                      // Uniform [0, 1)
auto randn = torch::randn({3, 4});                    // Normal N(0, 1)
auto arange = torch::arange(0, 10, 2);                // [0, 2, 4, 6, 8]
auto linspace = torch::linspace(0, 1, 5);             // 5 evenly spaced

// From C++ data
std::vector<float> data = {1, 2, 3, 4};
auto from_vec = torch::tensor(data);
auto from_ptr = torch::from_blob(data.data(), {4}, torch::kFloat32);

// With options
auto gpu_tensor = torch::zeros({3, 4},
    torch::TensorOptions().device(torch::kCUDA).dtype(torch::kFloat32));
```

### Tensor Operations

```cpp
// Arithmetic
auto c = a + b;
auto c = torch::add(a, b);
auto c = a.add(b);         // In-place: a.add_(b)

// Matrix operations
auto prod = torch::matmul(a, b);
auto prod = a.mm(b);       // 2D matrix multiply
auto batch_prod = a.bmm(b); // Batch matrix multiply

// Reductions
auto sum = tensor.sum();
auto mean = tensor.mean();
auto max_val = tensor.max();
auto argmax = tensor.argmax(/*dim=*/1);

// Reshaping
auto reshaped = tensor.view({-1, 4});
auto squeezed = tensor.squeeze();
auto unsqueezed = tensor.unsqueeze(0);

// Indexing
auto row = tensor[0];
auto element = tensor[0][1];
auto slice = tensor.slice(/*dim=*/0, /*start=*/0, /*end=*/5);
auto indexed = tensor.index({torch::indexing::Slice(), 0});
```

### Device Management

```cpp
// Check CUDA availability
bool cuda_available = torch::cuda::is_available();
int device_count = torch::cuda::device_count();

// Create device
torch::Device device = cuda_available ? torch::kCUDA : torch::kCPU;
torch::Device specific_gpu(torch::kCUDA, 0);  // GPU 0

// Move tensors
auto gpu_tensor = cpu_tensor.to(device);
auto cpu_tensor = gpu_tensor.to(torch::kCPU);

// Create on device
auto tensor = torch::zeros({3, 4},
    torch::TensorOptions().device(device));
```

### Autograd

```cpp
// Enable gradient tracking
auto x = torch::randn({3, 4}, torch::requires_grad());

// Forward computation
auto y = x * 2;
auto z = y.mean();

// Backward pass
z.backward();

// Access gradients
auto grad = x.grad();

// Disable gradients for inference
{
    torch::NoGradGuard no_grad;
    auto output = model->forward(input);  // No gradients computed
}

// Detach from computation graph
auto detached = tensor.detach();
```

## Neural Network Modules

### Defining a Module

```cpp
#include <torch/torch.h>

struct MyNet : torch::nn::Module {
    torch::nn::Linear fc1{nullptr}, fc2{nullptr};
    torch::nn::BatchNorm1d bn{nullptr};
    torch::nn::Dropout dropout{nullptr};

    MyNet(int64_t input_dim, int64_t hidden_dim, int64_t output_dim) {
        fc1 = register_module("fc1", torch::nn::Linear(input_dim, hidden_dim));
        bn = register_module("bn", torch::nn::BatchNorm1d(hidden_dim));
        dropout = register_module("dropout", torch::nn::Dropout(0.5));
        fc2 = register_module("fc2", torch::nn::Linear(hidden_dim, output_dim));
    }

    torch::Tensor forward(torch::Tensor x) {
        x = fc1->forward(x);
        x = bn->forward(x);
        x = torch::relu(x);
        x = dropout->forward(x);
        x = fc2->forward(x);
        return x;
    }
};
```

### Common Layers

```cpp
// Linear layers
torch::nn::Linear(in_features, out_features);

// Convolutional layers
torch::nn::Conv2d(torch::nn::Conv2dOptions(in_channels, out_channels, kernel_size)
    .stride(1).padding(1));

// Normalization
torch::nn::BatchNorm1d(num_features);
torch::nn::LayerNorm(torch::nn::LayerNormOptions({hidden_dim}));

// Recurrent layers
torch::nn::LSTM(torch::nn::LSTMOptions(input_size, hidden_size).num_layers(2));
torch::nn::GRU(torch::nn::GRUOptions(input_size, hidden_size));

// Dropout
torch::nn::Dropout(p);

// Activation (functional)
torch::relu(x);
torch::tanh(x);
torch::softmax(x, /*dim=*/1);
```

### Train/Eval Mode

```cpp
// Training mode (enables dropout, batch norm in training mode)
model->train();

// Evaluation mode (disables dropout, uses running stats for batch norm)
model->eval();
```

## Optimizers

```cpp
// Adam
torch::optim::Adam optimizer(model->parameters(),
    torch::optim::AdamOptions(/*lr=*/1e-3).betas({0.9, 0.999}));

// SGD with momentum
torch::optim::SGD optimizer(model->parameters(),
    torch::optim::SGDOptions(/*lr=*/0.01).momentum(0.9).weight_decay(1e-4));

// RMSprop
torch::optim::RMSprop optimizer(model->parameters(),
    torch::optim::RMSpropOptions(/*lr=*/1e-3).alpha(0.99));

// Training step
optimizer.zero_grad();
auto loss = compute_loss(model, batch);
loss.backward();
optimizer.step();
```

## Model Serialization

### Save and Load C++ Models

```cpp
// Save model
torch::save(model, "model.pt");

// Load model
torch::load(model, "model.pt");

// Save optimizer state
torch::save(optimizer, "optimizer.pt");
```

### Load Python PyTorch Models (TorchScript)

```python
# In Python: export model
import torch

model = MyModel()
model.load_state_dict(torch.load("weights.pth"))
model.eval()

# Option 1: Trace
traced = torch.jit.trace(model, example_input)
traced.save("model_traced.pt")

# Option 2: Script
scripted = torch.jit.script(model)
scripted.save("model_scripted.pt")
```

```cpp
// In C++: load TorchScript model
torch::jit::script::Module model = torch::jit::load("model_traced.pt");
model.to(device);
model.eval();

// Inference
std::vector<torch::jit::IValue> inputs;
inputs.push_back(input_tensor);
auto output = model.forward(inputs).toTensor();
```

## Other Libraries

### ONNX Runtime (Inference)

For deploying trained models in production, ONNX Runtime provides optimized cross-platform inference.

**Installation**: https://onnxruntime.ai/

```cpp
#include <onnxruntime_cxx_api.h>

Ort::Env env(ORT_LOGGING_LEVEL_WARNING, "rl_inference");
Ort::Session session(env, "model.onnx", Ort::SessionOptions{});

// Run inference
auto output_tensors = session.Run(
    Ort::RunOptions{nullptr},
    input_names.data(), &input_tensor, 1,
    output_names.data(), 1
);
```

### cpprl Reference Implementation

The `mhubii/cpprl` repository on GitHub provides reference implementations of PPO in C++ using LibTorch. Useful for:

- Understanding PPO implementation patterns
- Rollout buffer design
- GAE (Generalized Advantage Estimation) computation

```bash
git clone https://github.com/mhubii/cpprl
```

### TensorFlow C++ API (Alternative)

Less commonly used for RL but available. TensorFlow's C++ API is primarily designed for inference rather than training.

```cpp
#include "tensorflow/core/public/session.h"
// More complex setup than LibTorch
```

**Recommendation**: Use LibTorch for new RL projects due to better training support and documentation.
