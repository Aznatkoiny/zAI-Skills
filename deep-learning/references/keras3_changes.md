# Keras 3 & Multi-Backend Guide

Keras 3 is a multi-backend deep learning framework that can run on top of JAX, TensorFlow, or PyTorch.

## Core Concepts

### 1. Setup & Backend Selection
Always import `keras` directly. Set the backend via environment variable *before* importing keras.

```python
import os
os.environ["KERAS_BACKEND"] = "jax"  # Options: "jax", "tensorflow", "torch"

import keras
```

### 2. Backend-Agnostic Operations (`keras.ops`)
To write layers/metrics that work on ANY backend, use `keras.ops` (which mimics the NumPy API) instead of `tf.*` or `torch.*`.

```python
from keras import ops

# Instead of tf.reduce_sum or torch.sum
x = ops.ones((2, 2))
y = ops.sum(x, axis=1)
```

### 3. Cross-Framework Compatibility
- **Data Pipelines**: `tf.data` is recommended for all backends. It produces data efficiently.
- **Saving**: Always use the `.keras` extension. It saves the model architecture and weights in a backend-agnostic format (zip archive).
  ```python
  model.save("my_model.keras")
  ```

### 4. Custom Components (Layers/Models)
Implement `call()` using `keras.ops`.

```python
class MyLayer(keras.layers.Layer):
    def call(self, inputs):
        return ops.square(inputs)
```

## Migration from Keras 2 (TensorFlow)

| Concept | Keras 2 (TF) | Keras 3 |
|---------|--------------|---------|
| **Import** | `from tensorflow import keras` | `import keras` |
| **Math** | `tf.math.*` | `keras.ops.*` |
| **Random** | `tf.random.*` | `keras.random.*` |
| **Saving** | `.h5` or SavedModel | `.keras` |
| **Variable** | `tf.Variable` | `keras.Variable` |

## Debugging

- **JAX**: Fast, but compilation overhead. Good for research.
- **TensorFlow**: Robust, good deployment ecosystem.
- **PyTorch**: Eager execution by default, easy to debug.

To debug, you can temporarily switch backend to `tensorflow` or `torch` if you are familiar with their eager execution modes, or use `run_eagerly=True` in `compile()`.
