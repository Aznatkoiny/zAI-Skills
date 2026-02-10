# Deep Learning for Computer Vision

## Table of Contents
- [Convnets (Convolutional Neural Networks)](#convnets-convolutional-neural-networks)
- [Data Loading](#data-loading)
- [Data Augmentation](#data-augmentation)
- [Transfer Learning](#transfer-learning)
- [Available Pretrained Models](#available-pretrained-models)
- [Complete Training Pipeline](#complete-training-pipeline)

## Convnets (Convolutional Neural Networks)

Key components: `Conv2D`, `MaxPooling2D`, `Flatten`.

### Basic Convnet Structure
```python
inputs = keras.Input(shape=(28, 28, 1))
x = layers.Conv2D(filters=32, kernel_size=3, activation="relu")(inputs)
x = layers.MaxPooling2D(pool_size=2)(x)
x = layers.Conv2D(filters=64, kernel_size=3, activation="relu")(x)
x = layers.MaxPooling2D(pool_size=2)(x)
x = layers.Conv2D(filters=128, kernel_size=3, activation="relu")(x)
x = layers.Flatten()(x)
outputs = layers.Dense(10, activation="softmax")(x)
model = keras.Model(inputs=inputs, outputs=outputs)
```

### Why MaxPooling Matters
Without pooling, the model has too many parameters and limited receptive field:
```python
# BAD: No pooling - 3.5M parameters, small receptive field
inputs = keras.Input(shape=(28, 28, 1))
x = layers.Conv2D(32, 3, activation="relu")(inputs)
x = layers.Conv2D(64, 3, activation="relu")(x)
x = layers.Conv2D(128, 3, activation="relu")(x)
x = layers.Flatten()(x)  # Huge flattened output!
```

## Data Loading

### image_dataset_from_directory
```python
from tensorflow.keras.utils import image_dataset_from_directory

train_dataset = image_dataset_from_directory(
    "path/to/train",
    image_size=(180, 180),
    batch_size=32,
    label_mode="binary"  # or "categorical", "int"
)

# Check shapes
for images, labels in train_dataset.take(1):
    print(f"images: {images.shape}")  # (32, 180, 180, 3)
    print(f"labels: {labels.shape}")  # (32,)
```

### Dataset Operations
```python
# Apply transformations
dataset = dataset.map(lambda x: x / 255.)  # Normalize

# Cache and prefetch for performance
dataset = dataset.cache().prefetch(tf.data.AUTOTUNE)
```

## Data Augmentation

Apply random transformations to increase training data diversity:

```python
data_augmentation = keras.Sequential([
    layers.RandomFlip("horizontal"),
    layers.RandomRotation(0.1),   # ±10% rotation
    layers.RandomZoom(0.2),       # ±20% zoom
    layers.RandomTranslation(0.1, 0.1),
    layers.RandomContrast(0.1),
])

# Use in model (only active during training)
inputs = keras.Input(shape=(180, 180, 3))
x = data_augmentation(inputs)
x = layers.Rescaling(1./255)(x)
x = layers.Conv2D(32, 3, activation="relu")(x)
# ...
```

## Transfer Learning

### Feature Extraction (Frozen Base)
Use pretrained model as fixed feature extractor:

```python
# Load pretrained base
conv_base = keras.applications.VGG16(
    weights="imagenet",
    include_top=False,
    input_shape=(180, 180, 3)
)
conv_base.trainable = False  # Freeze weights

# Build model
inputs = keras.Input(shape=(180, 180, 3))
x = keras.applications.vgg16.preprocess_input(inputs)
x = conv_base(x)
x = layers.Flatten()(x)
x = layers.Dense(256, activation="relu")(x)
x = layers.Dropout(0.5)(x)
outputs = layers.Dense(1, activation="sigmoid")(x)
model = keras.Model(inputs, outputs)

model.compile(optimizer="rmsprop", loss="binary_crossentropy", metrics=["accuracy"])
```

### Fast Feature Extraction (No Augmentation)
Extract features once, train classifier on extracted features:

```python
def get_features_and_labels(dataset):
    all_features, all_labels = [], []
    for images, labels in dataset:
        preprocessed = keras.applications.vgg16.preprocess_input(images)
        features = conv_base.predict(preprocessed)
        all_features.append(features)
        all_labels.append(labels)
    return np.concatenate(all_features), np.concatenate(all_labels)

train_features, train_labels = get_features_and_labels(train_dataset)

# Train lightweight classifier
classifier = keras.Sequential([
    keras.Input(shape=(5, 5, 512)),
    layers.Flatten(),
    layers.Dense(256, activation="relu"),
    layers.Dropout(0.5),
    layers.Dense(1, activation="sigmoid")
])
classifier.fit(train_features, train_labels, epochs=20)
```

### Fine-Tuning
Unfreeze top layers of base after initial training:

```python
# After training frozen model...
conv_base.trainable = True

# Freeze all layers except last 4
for layer in conv_base.layers[:-4]:
    layer.trainable = False

# Recompile with lower learning rate
model.compile(
    optimizer=keras.optimizers.RMSprop(learning_rate=1e-5),
    loss="binary_crossentropy",
    metrics=["accuracy"]
)

# Continue training
model.fit(train_dataset, epochs=30, validation_data=val_dataset)
```

## Available Pretrained Models

```python
# Common architectures (all from keras.applications)
keras.applications.VGG16(weights="imagenet", include_top=False)
keras.applications.ResNet50(weights="imagenet", include_top=False)
keras.applications.Xception(weights="imagenet", include_top=False)
keras.applications.EfficientNetB0(weights="imagenet", include_top=False)
keras.applications.MobileNetV2(weights="imagenet", include_top=False)

# Each has its own preprocess_input function
from keras.applications.resnet50 import preprocess_input
```

## Complete Training Pipeline

```python
# 1. Load data
train_dataset = image_dataset_from_directory("train", image_size=(180, 180), batch_size=32)
val_dataset = image_dataset_from_directory("val", image_size=(180, 180), batch_size=32)

# 2. Define augmentation
data_augmentation = keras.Sequential([
    layers.RandomFlip("horizontal"),
    layers.RandomRotation(0.1),
    layers.RandomZoom(0.2),
])

# 3. Build model with augmentation
inputs = keras.Input(shape=(180, 180, 3))
x = data_augmentation(inputs)
x = layers.Rescaling(1./255)(x)
x = layers.Conv2D(32, 3, activation="relu")(x)
x = layers.MaxPooling2D(2)(x)
x = layers.Conv2D(64, 3, activation="relu")(x)
x = layers.MaxPooling2D(2)(x)
x = layers.Conv2D(128, 3, activation="relu")(x)
x = layers.MaxPooling2D(2)(x)
x = layers.Conv2D(256, 3, activation="relu")(x)
x = layers.Flatten()(x)
x = layers.Dropout(0.5)(x)
outputs = layers.Dense(1, activation="sigmoid")(x)
model = keras.Model(inputs, outputs)

# 4. Compile and train
model.compile(optimizer="rmsprop", loss="binary_crossentropy", metrics=["accuracy"])

callbacks = [
    keras.callbacks.ModelCheckpoint("best.keras", save_best_only=True),
    keras.callbacks.EarlyStopping(patience=5, restore_best_weights=True)
]

model.fit(train_dataset, epochs=100, validation_data=val_dataset, callbacks=callbacks)
```
