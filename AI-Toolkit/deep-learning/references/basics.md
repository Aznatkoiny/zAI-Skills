# Deep Learning Basics

Based on *Deep Learning with Python, 2nd Edition* by François Chollet.

## Table of Contents
- [Tensor Operations](#tensor-operations)
- [Data Preparation](#data-preparation)
- [Generalization: Underfitting vs Overfitting](#generalization-underfitting-vs-overfitting)
- [Common Mistakes](#common-mistakes)
- [Quick Recipes](#quick-recipes)

## Tensor Operations

### Key Attributes
```python
x.ndim    # Number of axes (rank)
x.shape   # Dimensions along each axis
x.dtype   # Data type (float32, int32, etc.)
```

### Common Tensor Shapes
- **Vector data**: `(samples, features)` - 2D
- **Timeseries/Sequence**: `(samples, timesteps, features)` - 3D
- **Images**: `(samples, height, width, channels)` - 4D
- **Video**: `(samples, frames, height, width, channels)` - 5D

### GradientTape for Automatic Differentiation
```python
x = tf.Variable(3.0)
with tf.GradientTape() as tape:
    y = x ** 2
grad = tape.gradient(y, x)  # dy/dx = 2x = 6
```

**Nested tapes for second-order gradients**:
```python
with tf.GradientTape() as outer_tape:
    with tf.GradientTape() as inner_tape:
        y = x ** 3
    first_grad = inner_tape.gradient(y, x)
second_grad = outer_tape.gradient(first_grad, x)
```

## Data Preparation

### Normalization (Critical for Training)
```python
# Compute stats on TRAINING data only
mean = train_data.mean(axis=0)
std = train_data.std(axis=0)

# Apply to all splits
train_data = (train_data - mean) / std
val_data = (val_data - mean) / std
test_data = (test_data - mean) / std
```

### Train/Val/Test Split
```python
num_val = int(0.2 * len(data))
num_test = int(0.1 * len(data))

val_data = data[:num_val]
test_data = data[num_val:num_val + num_test]
train_data = data[num_val + num_test:]
```

### K-Fold Cross-Validation
Use when data is limited (< 10,000 samples).

```python
k = 4
num_val_samples = len(data) // k
all_scores = []

for fold in range(k):
    val_data = data[fold * num_val_samples:(fold + 1) * num_val_samples]
    train_data = np.concatenate([
        data[:fold * num_val_samples],
        data[(fold + 1) * num_val_samples:]
    ], axis=0)

    model = build_model()
    model.fit(train_data, train_targets, epochs=100, verbose=0)
    val_score = model.evaluate(val_data, val_targets)
    all_scores.append(val_score)

print(f"Average score: {np.mean(all_scores)}")
```

## Generalization: Underfitting vs Overfitting

### Diagnosing from Learning Curves
- **Underfitting**: Both train and val loss are high
- **Overfitting**: Train loss decreases, val loss increases
- **Good fit**: Both losses decrease, then val loss plateaus

### Fighting Overfitting (in order of preference)

**1. Get more training data** - Always the best solution

**2. Reduce network capacity**:
```python
# Smaller model
model = keras.Sequential([
    layers.Dense(4, activation="relu"),
    layers.Dense(4, activation="relu"),
    layers.Dense(1, activation="sigmoid")
])
```

**3. Add weight regularization**:
```python
from tensorflow.keras import regularizers

layers.Dense(16,
    kernel_regularizer=regularizers.l2(0.002),
    activation="relu")

# Options: l1(0.001), l2(0.001), l1_l2(l1=0.001, l2=0.001)
```

**4. Add dropout**:
```python
model = keras.Sequential([
    layers.Dense(16, activation="relu"),
    layers.Dropout(0.5),  # Drop 50% of units during training
    layers.Dense(16, activation="relu"),
    layers.Dropout(0.5),
    layers.Dense(1, activation="sigmoid")
])
```

## Common Mistakes

### Wrong Learning Rate
```python
# Too high - loss explodes or oscillates
model.compile(optimizer=keras.optimizers.RMSprop(1.0), ...)

# Good starting point
model.compile(optimizer=keras.optimizers.RMSprop(1e-3), ...)

# For fine-tuning pretrained models
model.compile(optimizer=keras.optimizers.RMSprop(1e-5), ...)
```

### Information Bottleneck
Don't use layers smaller than the output dimension in intermediate layers:
```python
# BAD: 4-unit bottleneck loses information for 46-class classification
model = keras.Sequential([
    layers.Dense(64, activation="relu"),
    layers.Dense(4, activation="relu"),   # Bottleneck!
    layers.Dense(46, activation="softmax")
])

# GOOD: Maintain representational capacity
model = keras.Sequential([
    layers.Dense(64, activation="relu"),
    layers.Dense(64, activation="relu"),
    layers.Dense(46, activation="softmax")
])
```

## Quick Recipes

### Binary Classification (e.g., Sentiment)
```python
model = keras.Sequential([
    layers.Dense(16, activation="relu"),
    layers.Dense(16, activation="relu"),
    layers.Dense(1, activation="sigmoid")
])
model.compile(optimizer="rmsprop",
              loss="binary_crossentropy",
              metrics=["accuracy"])
```

### Multiclass Classification (e.g., Topic)
```python
model = keras.Sequential([
    layers.Dense(64, activation="relu"),
    layers.Dense(64, activation="relu"),
    layers.Dense(num_classes, activation="softmax")
])
model.compile(optimizer="rmsprop",
              loss="sparse_categorical_crossentropy",  # integer labels
              metrics=["accuracy"])
```

### Regression (e.g., Price Prediction)
```python
model = keras.Sequential([
    layers.Dense(64, activation="relu"),
    layers.Dense(64, activation="relu"),
    layers.Dense(1)  # No activation for regression
])
model.compile(optimizer="rmsprop",
              loss="mse",
              metrics=["mae"])
```
