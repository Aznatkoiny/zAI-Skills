# Deep Learning for Timeseries

## Table of Contents
- [Data Preparation](#data-preparation)
- [Baseline: Common-Sense Approach](#baseline-common-sense-approach)
- [Architectures](#architectures)
- [Recurrent Dropout](#recurrent-dropout)
- [Practical Tips](#practical-tips)
- [Multi-Step Forecasting](#multi-step-forecasting)

## Data Preparation

### timeseries_dataset_from_array
Efficiently create sliding window datasets:

```python
sampling_rate = 6       # Sample every 6 timesteps (1 hour if 10-min data)
sequence_length = 120   # Look back 120 samples
delay = sampling_rate * (sequence_length + 24 - 1)  # Predict 24 steps ahead
batch_size = 256

train_dataset = keras.utils.timeseries_dataset_from_array(
    data=raw_data[:-delay],         # Input sequences
    targets=temperature[delay:],     # Target values
    sampling_rate=sampling_rate,
    sequence_length=sequence_length,
    shuffle=True,
    batch_size=batch_size,
    start_index=0,
    end_index=num_train_samples
)

val_dataset = keras.utils.timeseries_dataset_from_array(
    data=raw_data[:-delay],
    targets=temperature[delay:],
    sampling_rate=sampling_rate,
    sequence_length=sequence_length,
    shuffle=True,
    batch_size=batch_size,
    start_index=num_train_samples,
    end_index=num_train_samples + num_val_samples
)

# Check shapes
for samples, targets in train_dataset.take(1):
    print(f"samples: {samples.shape}")  # (batch, sequence_length, features)
    print(f"targets: {targets.shape}")  # (batch,)
```

### Normalization
Always normalize timeseries data:

```python
mean = raw_data[:num_train_samples].mean(axis=0)
std = raw_data[:num_train_samples].std(axis=0)
raw_data -= mean
raw_data /= std
```

## Baseline: Common-Sense Approach

Always establish a baseline before deep learning:

```python
def evaluate_naive_method(dataset):
    """Predict last observed value."""
    total_abs_err = 0.
    samples_seen = 0
    for samples, targets in dataset:
        preds = samples[:, -1, 1] * std[1] + mean[1]  # Last value, denormalized
        total_abs_err += np.sum(np.abs(preds - targets))
        samples_seen += samples.shape[0]
    return total_abs_err / samples_seen

print(f"Baseline MAE: {evaluate_naive_method(val_dataset):.2f}")
```

## Architectures

### 1. Dense Baseline
Often surprisingly competitive:

```python
inputs = keras.Input(shape=(sequence_length, num_features))
x = layers.Flatten()(inputs)
x = layers.Dense(16, activation="relu")(x)
outputs = layers.Dense(1)(x)
model = keras.Model(inputs, outputs)
model.compile(optimizer="rmsprop", loss="mse", metrics=["mae"])
```

### 2. 1D Convnets
Fast and good for capturing local patterns:

```python
inputs = keras.Input(shape=(sequence_length, num_features))
x = layers.Conv1D(8, 24, activation="relu")(inputs)
x = layers.MaxPooling1D(2)(x)
x = layers.Conv1D(8, 12, activation="relu")(x)
x = layers.MaxPooling1D(2)(x)
x = layers.Conv1D(8, 6, activation="relu")(x)
x = layers.GlobalAveragePooling1D()(x)
outputs = layers.Dense(1)(x)
model = keras.Model(inputs, outputs)
```

### 3. Simple RNN
```python
inputs = keras.Input(shape=(sequence_length, num_features))
x = layers.SimpleRNN(16)(inputs)
outputs = layers.Dense(1)(x)
model = keras.Model(inputs, outputs)
```

### 4. LSTM (Long Short-Term Memory)
Better at long-term dependencies:

```python
inputs = keras.Input(shape=(sequence_length, num_features))
x = layers.LSTM(32, recurrent_dropout=0.25)(inputs)
x = layers.Dropout(0.5)(x)
outputs = layers.Dense(1)(x)
model = keras.Model(inputs, outputs)
```

### 5. GRU (Gated Recurrent Unit)
Simpler/faster than LSTM, often similar performance:

```python
inputs = keras.Input(shape=(sequence_length, num_features))
x = layers.GRU(32, recurrent_dropout=0.25)(inputs)
x = layers.Dropout(0.5)(x)
outputs = layers.Dense(1)(x)
model = keras.Model(inputs, outputs)
```

### 6. Stacked RNNs
Increase capacity with multiple layers:

```python
inputs = keras.Input(shape=(sequence_length, num_features))
x = layers.GRU(32, recurrent_dropout=0.5, return_sequences=True)(inputs)  # Must return sequences
x = layers.GRU(32, recurrent_dropout=0.5)(x)
x = layers.Dropout(0.5)(x)
outputs = layers.Dense(1)(x)
model = keras.Model(inputs, outputs)
```

### 7. Bidirectional RNNs
Process sequence in both directions. Good for NLP, usually **not** for forecasting:

```python
inputs = keras.Input(shape=(sequence_length, num_features))
x = layers.Bidirectional(layers.LSTM(16))(inputs)
outputs = layers.Dense(1)(x)
model = keras.Model(inputs, outputs)
```

**When to use**: When context from "future" is available (NLP, not real-time forecasting).

## Recurrent Dropout

Use `recurrent_dropout` to regularize RNNs:

```python
# Dropout on recurrent connections (not input/output)
layers.LSTM(32, recurrent_dropout=0.25)
layers.GRU(32, recurrent_dropout=0.5)

# Note: recurrent_dropout prevents cuDNN optimization
# For faster training with recurrent_dropout, use unroll=True
layers.LSTM(32, recurrent_dropout=0.2, unroll=True)
```

## Practical Tips

### Key Settings
- `return_sequences=True` for stacking RNN layers
- `recurrent_dropout` for RNN regularization
- `Dropout` after RNN layer for additional regularization

### When to Use What

| Data Pattern | Recommended Architecture |
|--------------|-------------------------|
| Short sequences, local patterns | 1D Conv |
| Long-term dependencies | LSTM or GRU |
| Very long sequences | Stacked LSTM/GRU or Transformer |
| NLP tasks | Bidirectional LSTM/GRU or Transformer |
| Real-time forecasting | LSTM/GRU (unidirectional) |

### Training Recipe
```python
callbacks = [
    keras.callbacks.ModelCheckpoint("best_model.keras", save_best_only=True),
    keras.callbacks.EarlyStopping(patience=5, restore_best_weights=True)
]

model.compile(optimizer="rmsprop", loss="mse", metrics=["mae"])
history = model.fit(
    train_dataset,
    epochs=50,
    validation_data=val_dataset,
    callbacks=callbacks
)
```

## Multi-Step Forecasting

For predicting multiple future steps:

```python
# Option 1: Multi-output model
inputs = keras.Input(shape=(sequence_length, num_features))
x = layers.LSTM(32)(inputs)
outputs = layers.Dense(24)(x)  # Predict 24 future steps
model = keras.Model(inputs, outputs)
model.compile(optimizer="rmsprop", loss="mse")

# Option 2: Autoregressive (feed predictions back as input)
def forecast_autoregressive(model, input_seq, steps):
    predictions = []
    current_seq = input_seq.copy()
    for _ in range(steps):
        pred = model.predict(current_seq[np.newaxis, :, :])
        predictions.append(pred[0, 0])
        current_seq = np.roll(current_seq, -1, axis=0)
        current_seq[-1, 0] = pred[0, 0]  # Add prediction to sequence
    return np.array(predictions)
```
