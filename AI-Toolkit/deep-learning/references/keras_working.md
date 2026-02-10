# Working with Keras

## Table of Contents
- [Model Building APIs](#model-building-apis)
- [Custom Metrics](#custom-metrics)
- [Callbacks](#callbacks)
- [Custom Training Loops](#custom-training-loops)
- [Performance Optimization](#performance-optimization)
- [Model Serialization](#model-serialization)
- [TensorBoard Visualization](#tensorboard-visualization)

## Model Building APIs

### 1. Sequential API
Best for simple stacks where each layer has one input/output.
```python
import keras
from keras import layers, ops

model = keras.Sequential([
    layers.Dense(64, activation="relu"),
    layers.Dense(10, activation="softmax")
])

# Or incrementally
model = keras.Sequential()
model.add(layers.Dense(64, activation="relu"))
model.add(layers.Dense(10, activation="softmax"))
```

### 2. Functional API
For multi-input/output, shared layers, non-linear topologies.

**Multi-Input/Output Example**:
```python
title = keras.Input(shape=(vocab_size,), name="title")
text_body = keras.Input(shape=(vocab_size,), name="text_body")
tags = keras.Input(shape=(num_tags,), name="tags")

features = layers.Concatenate()([title, text_body, tags])
features = layers.Dense(64, activation="relu")(features)

priority = layers.Dense(1, activation="sigmoid", name="priority")(features)
department = layers.Dense(num_depts, activation="softmax", name="dept")(features)

model = keras.Model(
    inputs=[title, text_body, tags],
    outputs=[priority, department]
)

# Compile with per-output losses
model.compile(
    optimizer="rmsprop",
    loss={"priority": "mse", "dept": "categorical_crossentropy"},
    metrics={"priority": ["mae"], "dept": ["accuracy"]}
)
```

**Accessing Layer Connectivity**:
```python
model.layers[3].input   # Get layer's input tensor
model.layers[3].output  # Get layer's output tensor

# Create new model reusing intermediate outputs
features = model.layers[4].output
new_output = layers.Dense(3, activation="softmax")(features)
new_model = keras.Model(inputs=model.inputs, outputs=[*model.outputs, new_output])
```

### 3. Subclassing API
Full flexibility with loops, conditionals, dynamic behavior.
```python
class CustomerTicketModel(keras.Model):
    def __init__(self, num_departments):
        super().__init__()
        self.concat_layer = layers.Concatenate()
        self.mixing_layer = layers.Dense(64, activation="relu")
        self.priority_scorer = layers.Dense(1, activation="sigmoid")
        self.department_classifier = layers.Dense(num_departments, activation="softmax")

    def call(self, inputs):
        title = inputs["title"]
        text_body = inputs["text_body"]
        tags = inputs["tags"]
        features = self.concat_layer([title, text_body, tags])
        features = self.mixing_layer(features)
        priority = self.priority_scorer(features)
        department = self.department_classifier(features)
        return priority, department
```

*Note*: Subclassed models can't be inspected/plotted like Functional models.

## Custom Metrics

Using `keras.ops` makes your metric work with TensorFlow, JAX, and PyTorch backends.

```python
class RootMeanSquaredError(keras.metrics.Metric):
    def __init__(self, name="rmse", **kwargs):
        super().__init__(name=name, **kwargs)
        self.mse_sum = self.add_weight(name="mse_sum", initializer="zeros")
        self.total_samples = self.add_weight(name="total_samples",
                                              initializer="zeros", dtype="int32")

    def update_state(self, y_true, y_pred, sample_weight=None):
        # Use keras.ops for backend-agnostic math
        y_true = ops.one_hot(y_true, num_classes=ops.shape(y_pred)[1])
        mse = ops.sum(ops.square(y_true - y_pred))
        self.mse_sum.assign_add(mse)
        self.total_samples.assign_add(ops.shape(y_pred)[0])

    def result(self):
        return ops.sqrt(self.mse_sum / ops.cast(self.total_samples, "float32"))

    def reset_state(self):
        self.mse_sum.assign(0.)
        self.total_samples.assign(0)

# Usage
model.compile(..., metrics=["accuracy", RootMeanSquaredError()])
```

## Callbacks

### Built-in Callbacks
```python
callbacks = [
    keras.callbacks.EarlyStopping(
        monitor="val_accuracy",
        patience=2,
        restore_best_weights=True
    ),
    keras.callbacks.ModelCheckpoint(
        filepath="best_model.keras",
        monitor="val_loss",
        save_best_only=True
    ),
    keras.callbacks.ReduceLROnPlateau(
        monitor="val_loss",
        factor=0.5,
        patience=3
    ),
    keras.callbacks.TensorBoard(log_dir="./logs")
]
model.fit(..., callbacks=callbacks)
```

### Custom Callbacks
```python
import matplotlib.pyplot as plt

class LossHistory(keras.callbacks.Callback):
    def on_train_begin(self, logs):
        self.per_batch_losses = []

    def on_batch_end(self, batch, logs):
        self.per_batch_losses.append(logs.get("loss"))

    def on_epoch_end(self, epoch, logs):
        plt.plot(self.per_batch_losses)
        plt.savefig(f"loss_epoch_{epoch}.png")
        self.per_batch_losses = []
```

## Custom Training Loops

### Basic Training Step (TensorFlow Backend)
```python
import tensorflow as tf # Required for GradientTape

model = get_model()
loss_fn = keras.losses.SparseCategoricalCrossentropy()
optimizer = keras.optimizers.RMSprop()
metrics = [keras.metrics.SparseCategoricalAccuracy()]

def train_step(inputs, targets):
    with tf.GradientTape() as tape:
        predictions = model(inputs, training=True)
        loss = loss_fn(targets, predictions)
    gradients = tape.gradient(loss, model.trainable_weights)
    optimizer.apply_gradients(zip(gradients, model.trainable_weights))

    for metric in metrics:
        metric.update_state(targets, predictions)
    return loss

# Training loop
for epoch in range(epochs):
    for metric in metrics:
        metric.reset_state()
    for inputs_batch, targets_batch in dataset:
        loss = train_step(inputs_batch, targets_batch)
    print(f"Epoch {epoch}: {metrics[0].result():.4f}")
```

### Custom train_step with fit()
Override `train_step` to customize while keeping `fit()` benefits:

```python
class CustomModel(keras.Model):
    def train_step(self, data):
        inputs, targets = data
        with tf.GradientTape() as tape:
            predictions = self(inputs, training=True)
            loss = self.compiled_loss(targets, predictions)
        gradients = tape.gradient(loss, self.trainable_weights)
        self.optimizer.apply_gradients(zip(gradients, self.trainable_weights))
        self.compiled_metrics.update_state(targets, predictions)
        return {m.name: m.result() for m in self.metrics}

# Use like normal model
model = CustomModel(inputs, outputs)
model.compile(optimizer="rmsprop", loss="mse", metrics=["mae"])
model.fit(train_data, epochs=10)
```

## Performance Optimization

### tf.function Decorator
Compiles Python code to TensorFlow graph for 2-10x speedup:
```python
@tf.function
def train_step(inputs, targets):
    with tf.GradientTape() as tape:
        predictions = model(inputs, training=True)
        loss = loss_fn(targets, predictions)
    gradients = tape.gradient(loss, model.trainable_weights)
    optimizer.apply_gradients(zip(gradients, model.trainable_weights))
    return loss
```

### Dataset Optimization
```python
dataset = tf.data.Dataset.from_tensor_slices((x, y))
dataset = dataset.shuffle(buffer_size=1024)
dataset = dataset.batch(32)
dataset = dataset.prefetch(tf.data.AUTOTUNE)  # Overlap data loading with training
dataset = dataset.cache()  # Cache in memory after first epoch
```

## Model Serialization

### Saving/Loading with Custom Objects
```python
# When saving models with custom layers
class TransformerEncoder(layers.Layer):
    def get_config(self):
        config = super().get_config()
        config.update({
            "embed_dim": self.embed_dim,
            "dense_dim": self.dense_dim,
            "num_heads": self.num_heads,
        })
        return config

# Loading
model = keras.models.load_model(
    "model.keras",
    custom_objects={"TransformerEncoder": TransformerEncoder}
)
```

## TensorBoard Visualization

```python
# During training
tensorboard = keras.callbacks.TensorBoard(
    log_dir="./logs",
    histogram_freq=1,  # Log weight histograms
    write_graph=True,
    write_images=True
)
model.fit(..., callbacks=[tensorboard])

# View in terminal
# tensorboard --logdir ./logs
```
