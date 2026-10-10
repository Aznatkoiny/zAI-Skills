---
name: deep-learning
description: Build and train neural networks with Keras 3 on any backend (JAX, TensorFlow or PyTorch). Use when the user is writing Keras code or asks for a Keras model, wants to migrate tf.keras / Keras 2 code to Keras 3, or is working on image classification, segmentation, text classification, sequence-to-sequence, time-series forecasting, or generative models (VAE, GAN) in Keras, including custom training loops, callbacks, transfer learning, mixed precision and multi-GPU training. Not for plain PyTorch or JAX training loops without Keras, Hugging Face / LLM fine-tuning, or reinforcement learning (use reinforcement-learning).
---

# Deep learning with Keras 3

Help the user build models that train correctly and generalize, using patterns from *Deep Learning with Python* by François Chollet (the 3rd edition, 2025, covers Keras 3 on JAX, PyTorch and TensorFlow).

Keras 3 runs on several backends, and several references below use TensorFlow-only APIs (`tf.data`, `tf.GradientTape`, `tf.distribute`). Check which backend the user runs (`keras.backend.backend()`, or `KERAS_BACKEND`) before using a TensorFlow-only pattern, and prefer `keras.ops` and backend-neutral APIs when the user isn't on TensorFlow. Library APIs move between releases: check `keras.__version__` and, if a docs or web tool is available, look up anything you're unsure of. Current as of October 2026: Keras 3.15.

## Core workflow

1. **Prepare data:** normalize, split train/validation/test, and feed it as NumPy arrays, a `tf.data.Dataset`, a PyTorch `DataLoader`, or a `keras.utils.PyDataset`. All of these work with every backend.
2. **Build the model:** Sequential, Functional, or subclassing API (below).
3. **Compile:** `model.compile(optimizer, loss, metrics)`.
4. **Train:** `model.fit(data, epochs=..., validation_data=..., callbacks=...)`.
5. **Evaluate** on held-out test data once, at the end: `model.evaluate(test_data)`.

## Model Building APIs

**Sequential** - Simple stack of layers:
```python
model = keras.Sequential([
    layers.Dense(64, activation="relu"),
    layers.Dense(10, activation="softmax")
])
```

**Functional** - Multi-input/output, shared layers, non-linear topologies:
```python
inputs = keras.Input(shape=(64,))
x = layers.Dense(64, activation="relu")(inputs)
outputs = layers.Dense(10, activation="softmax")(x)
model = keras.Model(inputs=inputs, outputs=outputs)
```

**Subclassing** - Full flexibility with `call()` method:
```python
class MyModel(keras.Model):
    def __init__(self):
        super().__init__()
        self.dense1 = layers.Dense(64, activation="relu")
        self.dense2 = layers.Dense(10, activation="softmax")

    def call(self, inputs):
        x = self.dense1(inputs)
        return self.dense2(x)
```

## Quick Reference: Loss & Optimizer Selection

| Task | Loss | Final Activation |
|------|------|------------------|
| Binary classification | `binary_crossentropy` | `sigmoid` |
| Multiclass (one-hot) | `categorical_crossentropy` | `softmax` |
| Multiclass (integers) | `sparse_categorical_crossentropy` | `softmax` |
| Regression | `mse` or `mae` | None |

**Optimizers:** `adam` is the usual starting point; `rmsprop` is the book's default for many examples; `sgd` with momentum is common when fine-tuning a pretrained model.

## Domain guides

| Topic | Reference | Use for | Backend |
|---|---|---|---|
| **Keras 3 and backends** | `references/keras3_changes.md` | Start here: multi-backend setup, `keras.ops`, `import keras`, migrating from tf.keras | Any |
| Fundamentals | `references/basics.md` | Overfitting, regularization, data prep, K-fold validation | Any |
| Keras in depth | `references/keras_working.md` | Custom metrics, callbacks, custom training steps | Mostly any; training-loop sections are TensorFlow |
| Computer vision | `references/computer_vision.md` | Convnets, augmentation, transfer learning | Any (uses `tf.data` for loading) |
| Advanced vision | `references/advanced_cv.md` | Segmentation, residual nets, Xception, Grad-CAM | TensorFlow |
| Time series | `references/timeseries.md` | LSTM/GRU, 1D convnets, forecasting | Any |
| Text and Transformers | `references/nlp_transformers.md` | Text vectorization, embeddings, Transformer encoder/decoder | TensorFlow |
| Generative models | `references/generative_dl.md` | Text generation, VAEs, GANs, style transfer | TensorFlow |
| Best practices | `references/best_practices.md` | KerasTuner, mixed precision, multi-GPU, TPU | Mixed: noted per section |

When a reference is TensorFlow-only and the user is on JAX or PyTorch, translate `tf.*` calls to `keras.ops` where an equivalent exists, or say that the pattern needs the TensorFlow backend.

## Essential Callbacks

```python
callbacks = [
    keras.callbacks.EarlyStopping(monitor="val_loss", patience=3),
    keras.callbacks.ModelCheckpoint("best.keras", save_best_only=True),
    keras.callbacks.TensorBoard(log_dir="./logs")
]
model.fit(..., callbacks=callbacks)
```

## Utility scripts

In this skill's `scripts/` folder (after install: `${CLAUDE_PLUGIN_ROOT}/skills/deep-learning/scripts/`).

| Script | Description |
|--------|-------------|
| `scripts/quick_train.py` | Reusable training template with standard callbacks and history plotting |
| `scripts/visualize_filters.py` | Visualize convnet filter patterns via gradient ascent (TensorFlow backend) |
