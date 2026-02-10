# Memory Management for C++ RL

## Overview

Proper memory management is critical in C++ RL implementations. This guide covers replay buffers, smart pointer patterns, RAII principles, and avoiding common memory pitfalls.

## Replay Buffers

### Basic Ring Buffer Implementation

```cpp
#include <vector>
#include <random>
#include <torch/torch.h>

struct Experience {
    torch::Tensor state;
    int64_t action;
    float reward;
    torch::Tensor next_state;
    bool done;

    // Move constructor for efficiency
    Experience(Experience&& other) noexcept = default;
    Experience& operator=(Experience&& other) noexcept = default;

    // Explicit copy (avoid accidental copies)
    Experience(const Experience& other) = default;
    Experience& operator=(const Experience& other) = default;
};

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

    std::vector<Experience> sample(size_t batch_size) {
        if (batch_size > size_) {
            throw std::runtime_error("Batch size exceeds buffer size");
        }

        std::vector<Experience> batch;
        batch.reserve(batch_size);

        std::uniform_int_distribution<size_t> dist(0, size_ - 1);
        for (size_t i = 0; i < batch_size; ++i) {
            // Copy experiences for batch (tensor data is reference counted)
            batch.push_back(buffer_[dist(rng_)]);
        }
        return batch;
    }

    size_t size() const { return size_; }
    bool can_sample(size_t batch_size) const { return size_ >= batch_size; }

private:
    std::vector<Experience> buffer_;
    size_t capacity_;
    size_t position_;
    size_t size_;
    std::mt19937 rng_{std::random_device{}()};
};
```

### Prioritized Experience Replay (PER)

```cpp
#include <algorithm>
#include <cmath>

class SumTree {
public:
    explicit SumTree(size_t capacity)
        : capacity_(capacity), tree_(2 * capacity - 1, 0.0f),
          data_ptr_(0), min_priority_(1e10) {
        data_.reserve(capacity);
    }

    void add(float priority, Experience exp) {
        size_t tree_idx = data_ptr_ + capacity_ - 1;

        if (data_.size() < capacity_) {
            data_.push_back(std::move(exp));
        } else {
            data_[data_ptr_] = std::move(exp);
        }

        update(tree_idx, priority);
        data_ptr_ = (data_ptr_ + 1) % capacity_;
        min_priority_ = std::min(min_priority_, priority);
    }

    void update(size_t tree_idx, float priority) {
        float change = priority - tree_[tree_idx];
        tree_[tree_idx] = priority;

        // Propagate change up to root
        while (tree_idx != 0) {
            tree_idx = (tree_idx - 1) / 2;
            tree_[tree_idx] += change;
        }
    }

    std::tuple<size_t, float, Experience&> get(float s) {
        size_t idx = 0;

        while (true) {
            size_t left = 2 * idx + 1;
            size_t right = left + 1;

            if (left >= tree_.size()) {
                break;
            }

            if (s <= tree_[left]) {
                idx = left;
            } else {
                s -= tree_[left];
                idx = right;
            }
        }

        size_t data_idx = idx - capacity_ + 1;
        return {idx, tree_[idx], data_[data_idx]};
    }

    float total_priority() const { return tree_[0]; }
    float min_priority() const { return min_priority_; }

private:
    size_t capacity_;
    std::vector<float> tree_;
    std::vector<Experience> data_;
    size_t data_ptr_;
    float min_priority_;
};

class PrioritizedReplayBuffer {
public:
    PrioritizedReplayBuffer(size_t capacity, float alpha = 0.6f)
        : capacity_(capacity), alpha_(alpha), tree_(capacity),
          max_priority_(1.0f) {}

    void push(Experience exp) {
        tree_.add(std::pow(max_priority_, alpha_), std::move(exp));
    }

    struct SampleResult {
        std::vector<Experience> experiences;
        std::vector<size_t> indices;
        torch::Tensor weights;
    };

    SampleResult sample(size_t batch_size, float beta = 0.4f) {
        SampleResult result;
        result.experiences.reserve(batch_size);
        result.indices.reserve(batch_size);

        float total = tree_.total_priority();
        float segment = total / batch_size;

        // Importance sampling weights
        float min_prob = tree_.min_priority() / total;
        float max_weight = std::pow(capacity_ * min_prob, -beta);

        std::vector<float> weights;
        weights.reserve(batch_size);

        std::uniform_real_distribution<float> dist(0, segment);

        for (size_t i = 0; i < batch_size; ++i) {
            float a = segment * i;
            float b = segment * (i + 1);
            float s = a + dist(rng_);

            auto [idx, priority, exp] = tree_.get(s);
            result.indices.push_back(idx);
            result.experiences.push_back(exp);

            float prob = priority / total;
            float weight = std::pow(capacity_ * prob, -beta) / max_weight;
            weights.push_back(weight);
        }

        result.weights = torch::tensor(weights);
        return result;
    }

    void update_priorities(const std::vector<size_t>& indices,
                          const std::vector<float>& priorities) {
        for (size_t i = 0; i < indices.size(); ++i) {
            float priority = std::pow(priorities[i] + 1e-6f, alpha_);
            tree_.update(indices[i], priority);
            max_priority_ = std::max(max_priority_, priorities[i]);
        }
    }

private:
    size_t capacity_;
    float alpha_;
    SumTree tree_;
    float max_priority_;
    std::mt19937 rng_{std::random_device{}()};
};
```

### N-Step Returns Buffer

```cpp
#include <deque>

class NStepBuffer {
public:
    NStepBuffer(size_t n_step, float gamma)
        : n_step_(n_step), gamma_(gamma) {}

    std::optional<Experience> add(Experience exp) {
        buffer_.push_back(std::move(exp));

        if (buffer_.size() < n_step_) {
            return std::nullopt;
        }

        // Compute n-step return
        float n_step_reward = 0.0f;
        float discount = 1.0f;

        for (size_t i = 0; i < n_step_; ++i) {
            n_step_reward += discount * buffer_[i].reward;
            discount *= gamma_;

            if (buffer_[i].done) {
                break;
            }
        }

        Experience n_step_exp;
        n_step_exp.state = buffer_.front().state;
        n_step_exp.action = buffer_.front().action;
        n_step_exp.reward = n_step_reward;
        n_step_exp.next_state = buffer_.back().next_state;
        n_step_exp.done = buffer_.back().done;

        buffer_.pop_front();
        return n_step_exp;
    }

    std::vector<Experience> flush() {
        std::vector<Experience> remaining;

        while (!buffer_.empty()) {
            float n_step_reward = 0.0f;
            float discount = 1.0f;

            for (const auto& exp : buffer_) {
                n_step_reward += discount * exp.reward;
                discount *= gamma_;
                if (exp.done) break;
            }

            Experience exp;
            exp.state = buffer_.front().state;
            exp.action = buffer_.front().action;
            exp.reward = n_step_reward;
            exp.next_state = buffer_.back().next_state;
            exp.done = buffer_.back().done;

            remaining.push_back(std::move(exp));
            buffer_.pop_front();
        }

        return remaining;
    }

private:
    std::deque<Experience> buffer_;
    size_t n_step_;
    float gamma_;
};
```

## Smart Pointer Patterns

### Model Ownership

```cpp
// Single-ownership: use unique_ptr
class Agent {
private:
    std::unique_ptr<torch::optim::Adam> optimizer_;
    // ...

public:
    Agent(std::shared_ptr<DQNNet> model) {
        // Optimizer owns its parameters
        optimizer_ = std::make_unique<torch::optim::Adam>(
            model->parameters(), 1e-3);
    }
};

// Shared-ownership: use shared_ptr
class DistributedTrainer {
private:
    std::shared_ptr<DQNNet> shared_model_;

public:
    void train_worker(int worker_id) {
        // Each worker gets reference to shared model
        auto local_model = shared_model_;
        // ...
    }
};
```

### Thread-Safe Model Cloning

```cpp
// Clone model for thread safety
std::shared_ptr<DQNNet> clone_model(const DQNNet& source) {
    auto cloned = std::make_shared<DQNNet>(source.state_dim_, source.action_dim_);

    torch::NoGradGuard no_grad;
    auto source_params = source.named_parameters();
    auto cloned_params = cloned->named_parameters();

    for (auto& param : cloned_params) {
        param.value().copy_(source_params[param.key()]);
    }

    return cloned;
}

// Usage in parallel workers
void parallel_rollout(std::shared_ptr<DQNNet> main_model, int num_workers) {
    std::vector<std::thread> workers;

    for (int i = 0; i < num_workers; ++i) {
        // Each worker gets its own copy
        auto worker_model = clone_model(*main_model);
        workers.emplace_back([worker_model, i]() {
            collect_experience(*worker_model, i);
        });
    }

    for (auto& w : workers) {
        w.join();
    }
}
```

## RAII Patterns

### GPU Memory Guard

```cpp
// RAII for temporary GPU memory allocation
class GPUMemoryGuard {
public:
    GPUMemoryGuard() {
        // Record current memory usage
        if (torch::cuda::is_available()) {
            initial_memory_ = torch::cuda::memory_allocated();
        }
    }

    ~GPUMemoryGuard() {
        // Force synchronization and memory release
        if (torch::cuda::is_available()) {
            torch::cuda::synchronize();
            // Optional: empty cache
            // torch::cuda::empty_cache();
        }
    }

    size_t memory_used() const {
        if (torch::cuda::is_available()) {
            return torch::cuda::memory_allocated() - initial_memory_;
        }
        return 0;
    }

private:
    size_t initial_memory_ = 0;
};

// Usage
void train_step() {
    GPUMemoryGuard guard;

    // ... training code ...

    // Memory automatically cleaned up when guard goes out of scope
}
```

### Environment RAII Wrapper

```cpp
class EnvironmentWrapper {
public:
    explicit EnvironmentWrapper(const std::string& env_name)
        : env_(create_environment(env_name)) {}

    ~EnvironmentWrapper() {
        if (env_) {
            env_->close();
        }
    }

    // Delete copy, allow move
    EnvironmentWrapper(const EnvironmentWrapper&) = delete;
    EnvironmentWrapper& operator=(const EnvironmentWrapper&) = delete;
    EnvironmentWrapper(EnvironmentWrapper&&) = default;
    EnvironmentWrapper& operator=(EnvironmentWrapper&&) = default;

    Environment* operator->() { return env_.get(); }

private:
    std::unique_ptr<Environment> env_;
};
```

## Common Memory Issues and Solutions

### Issue 1: Tensor Accumulation in Loops

**Problem**: Gradients accumulate when storing tensors.

```cpp
// BAD: Gradients accumulate
std::vector<torch::Tensor> stored_values;
for (int i = 0; i < 1000; ++i) {
    auto value = model->forward(state);
    stored_values.push_back(value);  // Keeps computation graph!
}
```

**Solution**: Detach tensors before storing.

```cpp
// GOOD: Detach to release computation graph
std::vector<torch::Tensor> stored_values;
for (int i = 0; i < 1000; ++i) {
    auto value = model->forward(state);
    stored_values.push_back(value.detach());  // Computation graph released
}
```

### Issue 2: Memory Leak in Replay Buffer

**Problem**: Tensors in Experience keep references.

```cpp
// Ensure proper tensor handling in Experience
struct Experience {
    torch::Tensor state;
    // ...

    // Detach state when creating experience
    static Experience create(torch::Tensor s, int64_t a, float r,
                            torch::Tensor ns, bool d) {
        return {s.detach(), a, r, ns.detach(), d};
    }
};
```

### Issue 3: GPU Memory Not Released

**Problem**: Tensors hold GPU memory after use.

```cpp
// Force cleanup
void cleanup_gpu_memory() {
    torch::cuda::synchronize();
    // Set tensors to empty or let them go out of scope
}

// Use scoped lifetime
void training_iteration() {
    {
        auto batch = buffer.sample(batch_size);
        auto loss = compute_loss(batch);
        loss.backward();
        optimizer.step();
    }  // batch tensors released here

    // Periodic cleanup
    if (iteration % 100 == 0) {
        torch::cuda::synchronize();
    }
}
```

### Issue 4: Thread Safety with Models

**Problem**: Multiple threads accessing same model.

```cpp
// Option 1: Clone for each thread
for (int i = 0; i < num_threads; ++i) {
    auto thread_model = clone_model(*shared_model);
    // Use thread_model in thread
}

// Option 2: Mutex protection
class ThreadSafeAgent {
private:
    std::shared_ptr<DQNNet> model_;
    std::mutex model_mutex_;

public:
    torch::Tensor forward(torch::Tensor input) {
        std::lock_guard<std::mutex> lock(model_mutex_);
        return model_->forward(input);
    }
};
```

## Memory Profiling

### Tracking GPU Memory

```cpp
void log_memory_stats() {
    if (torch::cuda::is_available()) {
        std::cout << "Allocated: "
                  << torch::cuda::memory_allocated() / (1024 * 1024) << " MB\n";
        std::cout << "Cached: "
                  << torch::cuda::memory_reserved() / (1024 * 1024) << " MB\n";
    }
}
```

### Tensor Reference Counting

```cpp
void check_tensor_refs(const torch::Tensor& t) {
    // Internal reference count (for debugging)
    std::cout << "Use count: " << t.use_count() << "\n";
    std::cout << "Storage use count: " << t.storage().use_count() << "\n";
}
```
