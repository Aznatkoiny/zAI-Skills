# Advanced Computer Vision

## Table of Contents
- [Image Segmentation](#image-segmentation)
- [Modern Architecture Patterns](#modern-architecture-patterns)
- [Interpreting Convnets](#interpreting-convnets)
- [Object Detection & Beyond](#object-detection--beyond)

## Image Segmentation

Classifying every pixel in an image. Uses encoder-decoder architecture with `Conv2DTranspose` for upsampling.

```python
def get_segmentation_model(img_size, num_classes):
    inputs = keras.Input(shape=img_size + (3,))
    x = layers.Rescaling(1./255)(inputs)

    # Encoder (downsampling)
    x = layers.Conv2D(64, 3, strides=2, activation="relu", padding="same")(x)
    x = layers.Conv2D(64, 3, activation="relu", padding="same")(x)
    x = layers.Conv2D(128, 3, strides=2, activation="relu", padding="same")(x)
    x = layers.Conv2D(128, 3, activation="relu", padding="same")(x)
    x = layers.Conv2D(256, 3, strides=2, activation="relu", padding="same")(x)
    x = layers.Conv2D(256, 3, activation="relu", padding="same")(x)

    # Decoder (upsampling)
    x = layers.Conv2DTranspose(256, 3, activation="relu", padding="same")(x)
    x = layers.Conv2DTranspose(256, 3, strides=2, activation="relu", padding="same")(x)
    x = layers.Conv2DTranspose(128, 3, activation="relu", padding="same")(x)
    x = layers.Conv2DTranspose(128, 3, strides=2, activation="relu", padding="same")(x)
    x = layers.Conv2DTranspose(64, 3, activation="relu", padding="same")(x)
    x = layers.Conv2DTranspose(64, 3, strides=2, activation="relu", padding="same")(x)

    # Per-pixel classification
    outputs = layers.Conv2D(num_classes, 3, activation="softmax", padding="same")(x)

    return keras.Model(inputs, outputs)

model = get_segmentation_model((200, 200), num_classes=3)
model.compile(optimizer="rmsprop", loss="sparse_categorical_crossentropy")
```

## Modern Architecture Patterns

### Residual Connections
Solve vanishing gradients in deep networks by adding skip connections:

```python
def residual_block(x, filters, pooling=False):
    residual = x

    x = layers.Conv2D(filters, 3, activation="relu", padding="same")(x)
    x = layers.Conv2D(filters, 3, activation="relu", padding="same")(x)

    if pooling:
        x = layers.MaxPooling2D(2, padding="same")(x)
        residual = layers.Conv2D(filters, 1, strides=2)(residual)
    elif filters != residual.shape[-1]:
        residual = layers.Conv2D(filters, 1)(residual)

    x = layers.add([x, residual])
    return x

# Usage
x = residual_block(x, filters=32, pooling=True)
x = residual_block(x, filters=64, pooling=True)
x = residual_block(x, filters=128, pooling=False)
```

### Batch Normalization
Normalize activations to stabilize training:

```python
x = layers.Conv2D(32, 3, use_bias=False)(x)  # No bias needed with BN
x = layers.BatchNormalization()(x)
x = layers.Activation("relu")(x)
```

### Depthwise Separable Convolutions
`SeparableConv2D` is lighter and faster than `Conv2D`, assuming spatial and channel correlations are independent (Xception architecture):

```python
x = layers.SeparableConv2D(256, 3, padding="same", use_bias=False)(x)
```

### Mini Xception-like Model
```python
inputs = keras.Input(shape=(180, 180, 3))
x = data_augmentation(inputs)
x = layers.Rescaling(1./255)(x)
x = layers.Conv2D(32, 5, use_bias=False)(x)

for size in [32, 64, 128, 256, 512]:
    residual = x

    x = layers.BatchNormalization()(x)
    x = layers.Activation("relu")(x)
    x = layers.SeparableConv2D(size, 3, padding="same", use_bias=False)(x)

    x = layers.BatchNormalization()(x)
    x = layers.Activation("relu")(x)
    x = layers.SeparableConv2D(size, 3, padding="same", use_bias=False)(x)

    x = layers.MaxPooling2D(3, strides=2, padding="same")(x)

    residual = layers.Conv2D(size, 1, strides=2, padding="same", use_bias=False)(residual)
    x = layers.add([x, residual])

x = layers.GlobalAveragePooling2D()(x)
x = layers.Dropout(0.5)(x)
outputs = layers.Dense(1, activation="sigmoid")(x)
model = keras.Model(inputs, outputs)
```

## Interpreting Convnets

### Visualizing Intermediate Activations
See what each layer learns:

```python
# Create model that outputs all conv layer activations
layer_outputs = []
layer_names = []
for layer in model.layers:
    if isinstance(layer, (layers.Conv2D, layers.MaxPooling2D)):
        layer_outputs.append(layer.output)
        layer_names.append(layer.name)

activation_model = keras.Model(inputs=model.input, outputs=layer_outputs)

# Get activations for an image
activations = activation_model.predict(img_array)

# Visualize first layer, channel 5
plt.matshow(activations[0][0, :, :, 5], cmap="viridis")
```

### Grad-CAM (Class Activation Maps)
Visualize which image regions contributed most to a prediction:

```python
# 1. Get last conv layer output and predictions
last_conv_layer = model.get_layer("block14_sepconv2_act")
last_conv_layer_model = keras.Model(model.inputs, last_conv_layer.output)

classifier_input = keras.Input(shape=last_conv_layer.output.shape[1:])
x = classifier_input
for layer_name in ["avg_pool", "predictions"]:
    x = model.get_layer(layer_name)(x)
classifier_model = keras.Model(classifier_input, x)

# 2. Compute gradients
with tf.GradientTape() as tape:
    last_conv_output = last_conv_layer_model(img_array)
    tape.watch(last_conv_output)
    preds = classifier_model(last_conv_output)
    top_pred_index = tf.argmax(preds[0])
    top_class_channel = preds[:, top_pred_index]

grads = tape.gradient(top_class_channel, last_conv_output)

# 3. Create heatmap
pooled_grads = tf.reduce_mean(grads, axis=(0, 1, 2)).numpy()
last_conv_output = last_conv_output.numpy()[0]

for i in range(pooled_grads.shape[-1]):
    last_conv_output[:, :, i] *= pooled_grads[i]

heatmap = np.mean(last_conv_output, axis=-1)
heatmap = np.maximum(heatmap, 0)
heatmap /= np.max(heatmap)

# 4. Overlay on image
import matplotlib.cm as cm
jet = cm.get_cmap("jet")
jet_heatmap = jet(np.uint8(255 * heatmap))[:, :, :3]
superimposed = jet_heatmap * 0.4 + original_img / 255.
```

### Visualizing Convnet Filters
What patterns does each filter respond to:

```python
@tf.function
def gradient_ascent_step(image, filter_index, learning_rate):
    with tf.GradientTape() as tape:
        tape.watch(image)
        activation = feature_extractor(image)
        filter_activation = activation[:, 2:-2, 2:-2, filter_index]
        loss = tf.reduce_mean(filter_activation)
    grads = tape.gradient(loss, image)
    grads = tf.math.l2_normalize(grads)
    image += learning_rate * grads
    return image

def generate_filter_pattern(filter_index):
    image = tf.random.uniform(shape=(1, 200, 200, 3), minval=0.4, maxval=0.6)
    for _ in range(30):
        image = gradient_ascent_step(image, filter_index, learning_rate=10.)
    return image[0].numpy()
```

## Object Detection & Beyond

For tasks like object detection and instance segmentation, consider:
- **YOLO** (You Only Look Once) - Real-time object detection
- **Faster R-CNN** - Two-stage detector with region proposals
- **Mask R-CNN** - Instance segmentation (detection + pixel masks)

These are available in libraries like:
- `tensorflow.keras.applications` (some detection models)
- TensorFlow Object Detection API
- Detectron2 (Facebook/Meta)
