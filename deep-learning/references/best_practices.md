# Deep Learning Best Practices

## Table of Contents
- [Hyperparameter Optimization](#hyperparameter-optimization)
- [Model Ensembling](#model-ensembling)
- [Mixed Precision Training](#mixed-precision-training)
- [Multi-GPU Training](#multi-gpu-training)
- [TPU Training](#tpu-training)
- [Data Pipeline Optimization](#data-pipeline-optimization)
- [Production Checklist](#production-checklist)
- [Debugging Tips](#debugging-tips)

## Hyperparameter Optimization

### KerasTuner

Automated hyperparameter search with various algorithms.

```python
import keras_tuner as kt

def build_model(hp):
    units = hp.Int("units", min_value=16, max_value=64, step=16)
    model = keras.Sequential([
        layers.Dense(units, activation="relu"),
        layers.Dense(10, activation="softmax")
    ])
    optimizer = hp.Choice("optimizer", values=["rmsprop", "adam"])
    model.compile(
        optimizer=optimizer,
        loss="sparse_categorical_crossentropy",
        metrics=["accuracy"]
    )
    return model
```

### HyperModel Class (For Complex Models)
```python
class SimpleMLP(kt.HyperModel):
    def __init__(self, num_classes):
        self.num_classes = num_classes

    def build(self, hp):
        units = hp.Int("units", min_value=16, max_value=64, step=16)
        dropout = hp.Float("dropout", min_value=0.0, max_value=0.5, step=0.1)
        lr = hp.Float("learning_rate", min_value=1e-4, max_value=1e-2, sampling="log")

        model = keras.Sequential([
            layers.Dense(units, activation="relu"),
            layers.Dropout(dropout),
            layers.Dense(self.num_classes, activation="softmax")
        ])
        model.compile(
            optimizer=keras.optimizers.Adam(learning_rate=lr),
            loss="sparse_categorical_crossentropy",
            metrics=["accuracy"]
        )
        return model
```

### Running the Search
```python
tuner = kt.BayesianOptimization(
    build_model,
    objective="val_accuracy",
    max_trials=100,
    executions_per_trial=2,  # Average over multiple runs
    directory="my_tuner",
    project_name="mnist_tuning",
    overwrite=True,
)

tuner.search_space_summary()

tuner.search(
    x_train, y_train,
    batch_size=128,
    epochs=100,
    validation_data=(x_val, y_val),
    callbacks=[keras.callbacks.EarlyStopping(patience=5)],
)

# Get best hyperparameters
best_hps = tuner.get_best_hyperparameters(num_trials=3)
print(best_hps[0].values)

# Get best model
best_model = tuner.get_best_models(num_models=1)[0]
```

### Tuner Types
- `kt.RandomSearch` - Random sampling
- `kt.BayesianOptimization` - Bayesian optimization (recommended)
- `kt.Hyperband` - Adaptive resource allocation

## Model Ensembling

Combine predictions from multiple models for better accuracy:

```python
# Train multiple models
models = [get_model() for _ in range(5)]
for model in models:
    model.fit(x_train, y_train, epochs=10, validation_data=(x_val, y_val))

# Ensemble predictions (average)
predictions = np.zeros_like(models[0].predict(x_test))
for model in models:
    predictions += model.predict(x_test)
predictions /= len(models)
final_predictions = np.argmax(predictions, axis=1)
```

## Mixed Precision Training

Use 16-bit floats for faster training on modern GPUs (Volta/Turing or newer):

```python
from tensorflow import keras

# Enable mixed precision globally
keras.mixed_precision.set_global_policy("mixed_float16")

# Build and train model as usual
model = build_model()
model.fit(x_train, y_train, epochs=10)

# Note: Final layer should stay float32 for numerical stability
# (Dense with softmax/sigmoid output is automatically handled)
```

**Benefits**:
- 2-3x training speedup on supported GPUs
- Lower memory usage (can use larger batch sizes)
- Minimal accuracy loss

## Multi-GPU Training

### Single Machine, Multiple GPUs
```python
strategy = tf.distribute.MirroredStrategy()
print(f"Number of devices: {strategy.num_replicas_in_sync}")

with strategy.scope():
    model = build_model()
    model.compile(
        optimizer="rmsprop",
        loss="sparse_categorical_crossentropy",
        metrics=["accuracy"]
    )

# Scale batch size with number of GPUs
global_batch_size = batch_size * strategy.num_replicas_in_sync
model.fit(x_train, y_train, batch_size=global_batch_size, epochs=10)
```

### Multiple Machines (Distributed Training)
```python
strategy = tf.distribute.MultiWorkerMirroredStrategy()

with strategy.scope():
    model = build_model()
    model.compile(...)
```

## TPU Training

### Using TPU on Google Colab
```python
# Connect to TPU
resolver = tf.distribute.cluster_resolver.TPUClusterResolver()
tf.config.experimental_connect_to_cluster(resolver)
tf.tpu.experimental.initialize_tpu_system(resolver)

strategy = tf.distribute.TPUStrategy(resolver)
print(f"Number of TPU cores: {strategy.num_replicas_in_sync}")

with strategy.scope():
    model = build_model()
    model.compile(...)

# Use larger batch sizes for TPUs (8 * 128 = 1024 typical)
model.fit(dataset, epochs=10, steps_per_epoch=steps_per_epoch)
```

### Step Fusing for TPU Efficiency
Run multiple training steps per TPU execution to reduce overhead:

```python
# Wrap model with step fusing
@tf.function
def train_multiple_steps(iterator, steps):
    for _ in tf.range(steps):
        x, y = next(iterator)
        with tf.GradientTape() as tape:
            predictions = model(x, training=True)
            loss = loss_fn(y, predictions)
        gradients = tape.gradient(loss, model.trainable_variables)
        optimizer.apply_gradients(zip(gradients, model.trainable_variables))
    return loss
```

## Data Pipeline Optimization

```python
# Optimal data pipeline
dataset = tf.data.Dataset.from_tensor_slices((x, y))
dataset = dataset.shuffle(buffer_size=10000)
dataset = dataset.batch(batch_size)
dataset = dataset.prefetch(tf.data.AUTOTUNE)  # Overlap loading with training
dataset = dataset.cache()  # Cache after first epoch (if fits in memory)
```

For large datasets:
```python
# Use TFRecord format for efficient I/O
dataset = tf.data.TFRecordDataset(filenames)
dataset = dataset.map(parse_fn, num_parallel_calls=tf.data.AUTOTUNE)
dataset = dataset.batch(batch_size)
dataset = dataset.prefetch(tf.data.AUTOTUNE)
```

## Production Checklist

1. **Data**
   - Normalize inputs (using training set statistics)
   - Handle missing values
   - Check for data leakage between train/val/test

2. **Model**
   - Start simple, increase complexity as needed
   - Use appropriate architecture for data type
   - Add regularization (dropout, L2) if overfitting

3. **Training**
   - Use callbacks (EarlyStopping, ModelCheckpoint)
   - Monitor both train and val metrics
   - Use learning rate scheduling if needed

4. **Deployment**
   - Save model with `model.save("model.keras")`
   - Test inference on new data
   - Consider quantization for edge deployment
   - Use `tf.function` for compiled inference

## Debugging Tips

```python
# Run eagerly for debugging (slower but allows print statements)
model.compile(..., run_eagerly=True)

# Check for NaN values
tf.debugging.enable_check_numerics()

# Profile training
tensorboard_callback = keras.callbacks.TensorBoard(
    log_dir="./logs",
    profile_batch=(10, 20)  # Profile batches 10-20
)
```
