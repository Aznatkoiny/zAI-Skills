# Performance Optimization for C++ RL

## GPU Acceleration

### Device Selection and Management

```cpp
#include <torch/torch.h>

class DeviceManager {
public:
    static torch::Device get_best_device() {
        if (torch::cuda::is_available()) {
            return torch::kCUDA;
        }
        // Check for MPS on Apple Silicon
        if (torch::mps::is_available()) {
            return torch::kMPS;
        }
        return torch::kCPU;
    }

    static void print_device_info() {
        if (torch::cuda::is_available()) {
            std::cout << "CUDA available: " << torch::cuda::device_count()
                      << " device(s)\n";
            for (int i = 0; i < torch::cuda::device_count(); ++i) {
                // Print device properties
                cudaDeviceProp prop;
                cudaGetDeviceProperties(&prop, i);
                std::cout << "  Device " << i << ": " << prop.name << "\n";
                std::cout << "    Memory: " << prop.totalGlobalMem / (1024*1024*1024)
                          << " GB\n";
            }
        }
    }
};

// Usage
torch::Device device = DeviceManager::get_best_device();
model->to(device);
```

### Efficient Tensor Transfers

```cpp
// Minimize CPU-GPU transfers
class BatchProcessor {
public:
    BatchProcessor(torch::Device device, size_t batch_size)
        : device_(device), batch_size_(batch_size) {
        // Pre-allocate buffers on device
        state_buffer_ = torch::empty({batch_size, state_dim_},
            torch::TensorOptions().device(device).dtype(torch::kFloat32));
    }

    torch::Tensor process_batch(const std::vector<Experience>& batch) {
        // Stack on CPU first (faster for small tensors)
        std::vector<torch::Tensor> states;
        states.reserve(batch.size());
        for (const auto& exp : batch) {
            states.push_back(exp.state);
        }

        // Single transfer to GPU
        auto batch_tensor = torch::stack(states).to(device_);
        return batch_tensor;
    }

private:
    torch::Device device_;
    size_t batch_size_;
    size_t state_dim_;
    torch::Tensor state_buffer_;
};
```

### Pinned Memory for Faster Transfers

```cpp
// Use pinned (page-locked) memory for faster CPU->GPU transfers
auto pinned_tensor = torch::empty({batch_size, state_dim},
    torch::TensorOptions()
        .dtype(torch::kFloat32)
        .pinned_memory(true));  // Pinned memory

// Async transfer with pinned memory
auto gpu_tensor = pinned_tensor.to(device, /*non_blocking=*/true);
torch::cuda::synchronize();  // Only sync when needed
```

### CUDA Streams for Parallelism

```cpp
#include <c10/cuda/CUDAStream.h>

class AsyncTrainer {
public:
    void async_training_step(torch::Tensor states, torch::Tensor actions) {
        // Create separate streams for different operations
        auto compute_stream = c10::cuda::getStreamFromPool();
        auto transfer_stream = c10::cuda::getStreamFromPool();

        {
            c10::cuda::CUDAStreamGuard guard(transfer_stream);
            // Async data transfer
            next_batch_states_ = prepare_next_batch().to(device_, true);
        }

        {
            c10::cuda::CUDAStreamGuard guard(compute_stream);
            // Forward and backward pass
            auto loss = compute_loss(states, actions);
            loss.backward();
            optimizer_->step();
        }

        // Synchronize only when necessary
        compute_stream.synchronize();
    }

private:
    torch::Device device_{torch::kCUDA};
    torch::Tensor next_batch_states_;
    std::unique_ptr<torch::optim::Adam> optimizer_;
};
```

## Parallel Environment Rollouts

### Thread Pool Implementation

```cpp
#include <thread>
#include <future>
#include <queue>
#include <functional>

class ThreadPool {
public:
    explicit ThreadPool(size_t num_threads) : stop_(false) {
        for (size_t i = 0; i < num_threads; ++i) {
            workers_.emplace_back([this] {
                while (true) {
                    std::function<void()> task;
                    {
                        std::unique_lock<std::mutex> lock(queue_mutex_);
                        condition_.wait(lock, [this] {
                            return stop_ || !tasks_.empty();
                        });
                        if (stop_ && tasks_.empty()) return;
                        task = std::move(tasks_.front());
                        tasks_.pop();
                    }
                    task();
                }
            });
        }
    }

    ~ThreadPool() {
        {
            std::unique_lock<std::mutex> lock(queue_mutex_);
            stop_ = true;
        }
        condition_.notify_all();
        for (auto& worker : workers_) {
            worker.join();
        }
    }

    template<class F, class... Args>
    auto enqueue(F&& f, Args&&... args)
        -> std::future<typename std::invoke_result<F, Args...>::type> {
        using return_type = typename std::invoke_result<F, Args...>::type;

        auto task = std::make_shared<std::packaged_task<return_type()>>(
            std::bind(std::forward<F>(f), std::forward<Args>(args)...)
        );

        std::future<return_type> result = task->get_future();
        {
            std::unique_lock<std::mutex> lock(queue_mutex_);
            tasks_.emplace([task]() { (*task)(); });
        }
        condition_.notify_one();
        return result;
    }

private:
    std::vector<std::thread> workers_;
    std::queue<std::function<void()>> tasks_;
    std::mutex queue_mutex_;
    std::condition_variable condition_;
    bool stop_;
};
```

### Parallel Rollout Collection

```cpp
class ParallelRolloutCollector {
public:
    ParallelRolloutCollector(size_t num_envs, std::shared_ptr<DQNNet> model)
        : num_envs_(num_envs), pool_(num_envs) {
        // Create environment instances
        for (size_t i = 0; i < num_envs; ++i) {
            envs_.push_back(std::make_unique<Environment>("CartPole-v1"));
            // Clone model for thread safety
            models_.push_back(clone_model(*model));
        }
    }

    std::vector<Experience> collect(int steps_per_env) {
        std::vector<std::future<std::vector<Experience>>> futures;

        for (size_t i = 0; i < num_envs_; ++i) {
            futures.push_back(pool_.enqueue([this, i, steps_per_env]() {
                return collect_from_env(i, steps_per_env);
            }));
        }

        std::vector<Experience> all_experiences;
        for (auto& future : futures) {
            auto exps = future.get();
            all_experiences.insert(all_experiences.end(),
                                  std::make_move_iterator(exps.begin()),
                                  std::make_move_iterator(exps.end()));
        }

        return all_experiences;
    }

    void sync_weights(const DQNNet& source) {
        for (auto& model : models_) {
            torch::NoGradGuard no_grad;
            auto source_params = source.named_parameters();
            auto target_params = model->named_parameters();
            for (auto& param : target_params) {
                param.value().copy_(source_params[param.key()]);
            }
        }
    }

private:
    std::vector<Experience> collect_from_env(size_t env_idx, int steps) {
        std::vector<Experience> experiences;
        auto& env = envs_[env_idx];
        auto& model = models_[env_idx];

        auto state = env->reset();

        for (int step = 0; step < steps; ++step) {
            torch::NoGradGuard no_grad;
            auto q_values = model->forward(state.unsqueeze(0));
            auto action = q_values.argmax(1).item<int64_t>();

            auto [next_state, reward, done, info] = env->step(action);

            experiences.push_back({state.detach(), action, reward,
                                  next_state.detach(), done});

            state = done ? env->reset() : next_state;
        }

        return experiences;
    }

    size_t num_envs_;
    ThreadPool pool_;
    std::vector<std::unique_ptr<Environment>> envs_;
    std::vector<std::shared_ptr<DQNNet>> models_;
};
```

## Batch Processing Optimization

### Vectorized Operations

```cpp
// Avoid loops where possible - use vectorized operations
class VectorizedDQN {
public:
    torch::Tensor compute_td_targets(
        torch::Tensor rewards,
        torch::Tensor next_states,
        torch::Tensor dones,
        float gamma
    ) {
        torch::NoGradGuard no_grad;

        // Vectorized computation
        auto next_q_values = target_net_->forward(next_states);
        auto max_next_q = std::get<0>(next_q_values.max(1));

        // Element-wise operations (no loops)
        auto targets = rewards + gamma * max_next_q * (1 - dones);
        return targets;
    }

    // Batch action selection (vectorized)
    torch::Tensor select_actions_batch(torch::Tensor states) {
        torch::NoGradGuard no_grad;
        auto q_values = policy_net_->forward(states);
        return q_values.argmax(1);
    }

private:
    std::shared_ptr<DQNNet> policy_net_;
    std::shared_ptr<DQNNet> target_net_;
};
```

### Efficient Batch Stacking

```cpp
// Pre-allocate and fill (faster than repeated concatenation)
torch::Tensor efficient_stack(const std::vector<Experience>& batch,
                              torch::Device device) {
    size_t batch_size = batch.size();
    auto state_shape = batch[0].state.sizes();

    // Pre-allocate tensor
    std::vector<int64_t> shape = {static_cast<int64_t>(batch_size)};
    shape.insert(shape.end(), state_shape.begin(), state_shape.end());

    auto result = torch::empty(shape,
        torch::TensorOptions().device(torch::kCPU).dtype(torch::kFloat32));

    // Fill in place
    for (size_t i = 0; i < batch_size; ++i) {
        result[i].copy_(batch[i].state);
    }

    return result.to(device);
}
```

## Memory Optimization

### Gradient Checkpointing

For large models, trade compute for memory with gradient checkpointing.

```cpp
#include <torch/torch.h>

// Manual checkpointing for segments
torch::Tensor checkpoint_forward(
    torch::nn::Sequential& segment,
    torch::Tensor input
) {
    if (torch::autograd::GradMode::is_enabled()) {
        // During training: use checkpointing
        auto detached = input.detach();
        detached.set_requires_grad(true);

        auto output = segment->forward(detached);

        // Store function to recompute
        return torch::autograd::make_variable(
            output.data(),
            /*requires_grad=*/true
        );
    } else {
        // During inference: normal forward
        return segment->forward(input);
    }
}
```

### Mixed Precision Training

```cpp
// Use automatic mixed precision (AMP) with CUDA
class MixedPrecisionTrainer {
public:
    void train_step(torch::Tensor states, torch::Tensor targets) {
        optimizer_->zero_grad();

        // Forward in FP16
        at::autocast::set_enabled(true);
        auto output = model_->forward(states);
        auto loss = torch::mse_loss(output, targets);
        at::autocast::set_enabled(false);

        // Scale loss and backward
        auto scaled_loss = loss * loss_scale_;
        scaled_loss.backward();

        // Unscale and clip gradients
        for (auto& param : model_->parameters()) {
            if (param.grad().defined()) {
                param.grad().div_(loss_scale_);
            }
        }
        torch::nn::utils::clip_grad_norm_(model_->parameters(), max_grad_norm_);

        optimizer_->step();
    }

private:
    std::shared_ptr<DQNNet> model_;
    std::unique_ptr<torch::optim::Adam> optimizer_;
    float loss_scale_ = 65536.0f;
    float max_grad_norm_ = 1.0f;
};
```

## Compilation and Build Optimization

### CMake Release Configuration

```cmake
cmake_minimum_required(VERSION 3.18)
project(rl_project)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Release optimizations
set(CMAKE_CXX_FLAGS_RELEASE "-O3 -DNDEBUG -march=native -ffast-math")

# Enable LTO for better optimization
set(CMAKE_INTERPROCEDURAL_OPTIMIZATION TRUE)

find_package(Torch REQUIRED)

add_executable(train_agent src/main.cpp)
target_link_libraries(train_agent "${TORCH_LIBRARIES}")

# Use static linking where possible
if(NOT MSVC)
    target_link_options(train_agent PRIVATE -static-libgcc -static-libstdc++)
endif()
```

### Profile-Guided Optimization (PGO)

```bash
# Step 1: Build with instrumentation
cmake -DCMAKE_CXX_FLAGS="-fprofile-generate" ..
make
./train_agent  # Run representative workload

# Step 2: Build with profile data
cmake -DCMAKE_CXX_FLAGS="-fprofile-use" ..
make
```

## Profiling Tools

### Built-in Timing

```cpp
#include <chrono>

class Timer {
public:
    void start() {
        start_ = std::chrono::high_resolution_clock::now();
    }

    double elapsed_ms() const {
        auto end = std::chrono::high_resolution_clock::now();
        return std::chrono::duration<double, std::milli>(end - start_).count();
    }

    void print(const std::string& label) const {
        std::cout << label << ": " << elapsed_ms() << " ms\n";
    }

private:
    std::chrono::high_resolution_clock::time_point start_;
};

// Usage
Timer timer;
timer.start();
auto loss = compute_loss(batch);
loss.backward();
timer.print("Forward + Backward");
```

### CUDA Profiling

```cpp
// Use CUDA events for accurate GPU timing
class CUDATimer {
public:
    CUDATimer() {
        cudaEventCreate(&start_);
        cudaEventCreate(&stop_);
    }

    ~CUDATimer() {
        cudaEventDestroy(start_);
        cudaEventDestroy(stop_);
    }

    void start() {
        cudaEventRecord(start_);
    }

    float elapsed_ms() {
        cudaEventRecord(stop_);
        cudaEventSynchronize(stop_);
        float ms;
        cudaEventElapsedTime(&ms, start_, stop_);
        return ms;
    }

private:
    cudaEvent_t start_, stop_;
};
```

### Using nvprof / nsys

```bash
# Profile with NVIDIA tools
nsys profile --stats=true ./train_agent

# Detailed kernel analysis
ncu --set full ./train_agent
```
