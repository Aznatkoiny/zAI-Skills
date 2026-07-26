#!/usr/bin/env python3
"""
Convnet Filter Visualization Script

Visualize what patterns convnet filters respond to using gradient ascent.
Works with any Keras model that has convolution layers (Conv2D,
SeparableConv2D, DepthwiseConv2D).

Usage:
    python visualize_filters.py --model path/to/model.keras --layer conv2d_5

    # Or import and use programmatically
    from visualize_filters import visualize_layer_filters
    visualize_layer_filters(model, "conv2d_5", save_path="filters.png")
"""

import os
os.environ.setdefault("KERAS_BACKEND", "tensorflow")

# Support both standalone Keras 3 and TensorFlow's bundled Keras
try:
    import keras
except ImportError:
    from tensorflow import keras

import numpy as np
import matplotlib.pyplot as plt
import tensorflow as tf
import argparse

# Convolution layer types eligible for filter visualization
CONV_LAYER_TYPES = (
    keras.layers.Conv2D,
    keras.layers.SeparableConv2D,
    keras.layers.DepthwiseConv2D,
)


def deprocess_image(img: np.ndarray) -> np.ndarray:
    """
    Convert tensor to displayable image.

    Args:
        img: Image tensor

    Returns:
        Normalized image array (0-255, uint8)
    """
    img = img.copy()
    # Normalize
    img -= img.mean()
    img /= img.std() + 1e-5
    img *= 0.15

    # Center crop a 12.5% border to remove edge artifacts
    margin = min(img.shape[0], img.shape[1]) // 8
    if margin > 0:
        img = img[margin:-margin, margin:-margin, :]

    # Clip to [0, 1]
    img += 0.5
    img = np.clip(img, 0, 1)

    # Convert to RGB array
    img *= 255
    img = np.clip(img, 0, 255).astype("uint8")
    return img


def generate_filter_pattern(
    feature_extractor: keras.Model,
    filter_index: int,
    img_size: tuple = (200, 200),
    iterations: int = 30,
    learning_rate: float = 10.0
) -> np.ndarray:
    """
    Generate an image that maximally activates a specific filter.

    Args:
        feature_extractor: Model that outputs the target layer activations
        filter_index: Index of the filter to visualize
        img_size: Size of generated image
        iterations: Number of gradient ascent steps
        learning_rate: Step size for gradient ascent

    Returns:
        Generated image as numpy array
    """
    # Start with random noise
    img = tf.Variable(
        tf.random.uniform((1, img_size[0], img_size[1], 3), minval=0.4, maxval=0.6)
    )

    for _ in range(iterations):
        with tf.GradientTape() as tape:
            activation = feature_extractor(img)
            # Avoid border artifacts
            filter_activation = activation[:, 2:-2, 2:-2, filter_index]
            loss = tf.reduce_mean(filter_activation)

        grads = tape.gradient(loss, img)
        grads = tf.math.l2_normalize(grads)
        img.assign_add(learning_rate * grads)

    return img[0].numpy()


def visualize_layer_filters(
    model: keras.Model,
    layer_name: str,
    num_filters: int = 64,
    filters_per_row: int = 8,
    img_size: tuple = (200, 200),
    save_path: str = None
) -> None:
    """
    Visualize filters from a convolutional layer.

    Args:
        model: Keras model
        layer_name: Name of the convolution layer to visualize
        num_filters: Number of filters to visualize
        filters_per_row: Filters per row in the grid
        img_size: Size of each filter visualization
        save_path: Optional path to save the figure
    """
    # Get the target layer
    try:
        layer = model.get_layer(layer_name)
    except ValueError:
        print(f"Layer '{layer_name}' not found. Available layers:")
        for l in model.layers:
            if isinstance(l, CONV_LAYER_TYPES):
                print(f"  - {l.name}")
        return

    # Sequential models have no symbolic input until they are built
    if isinstance(model, keras.Sequential) and not model.built:
        model.build((None, img_size[0], img_size[1], 3))

    try:
        model_input = model.input
    except (AttributeError, ValueError) as exc:
        print(f"Cannot create feature extractor: model has no symbolic input ({exc}).")
        print("Build or call the model on an input batch first, then retry.")
        return

    # Create feature extractor
    feature_extractor = keras.Model(inputs=model_input, outputs=layer.output)

    # Limit to actual number of filters
    actual_filters = layer.output.shape[-1]
    num_filters = min(num_filters, actual_filters)

    print(f"Visualizing {num_filters} filters from layer '{layer_name}'...")

    # Generate filter patterns
    all_imgs = []
    for i in range(num_filters):
        print(f"  Processing filter {i + 1}/{num_filters}", end="\r")
        img = generate_filter_pattern(feature_extractor, i, img_size)
        img = deprocess_image(img)
        all_imgs.append(img)
    print()

    # Create grid (display size comes from the cropped images themselves)
    n_cols = filters_per_row
    n_rows = (num_filters + n_cols - 1) // n_cols

    display_height, display_width = all_imgs[0].shape[:2]
    margin = 5

    grid_width = n_cols * display_width + (n_cols - 1) * margin
    grid_height = n_rows * display_height + (n_rows - 1) * margin

    grid = np.zeros((grid_height, grid_width, 3), dtype="uint8")

    for idx, img in enumerate(all_imgs):
        row = idx // n_cols
        col = idx % n_cols
        y = row * (display_height + margin)
        x = col * (display_width + margin)
        grid[y:y + display_height, x:x + display_width, :] = img

    # Display
    plt.figure(figsize=(15, 15 * n_rows / n_cols))
    plt.imshow(grid)
    plt.axis("off")
    plt.title(f"Filter patterns for layer: {layer_name}")

    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches="tight")
        print(f"Saved to {save_path}")

    plt.show()


def list_conv_layers(model: keras.Model) -> list:
    """List all convolution layers (Conv2D, SeparableConv2D, DepthwiseConv2D)."""
    conv_layers = []
    for layer in model.layers:
        if isinstance(layer, CONV_LAYER_TYPES):
            conv_layers.append({
                "name": layer.name,
                # DepthwiseConv2D has no `filters` attribute
                "filters": getattr(layer, "filters", None),
                "kernel_size": layer.kernel_size
            })
    return conv_layers


def main():
    parser = argparse.ArgumentParser(description="Visualize convnet filters")
    parser.add_argument("--model", type=str, required=True, help="Path to saved model")
    parser.add_argument("--layer", type=str, help="Layer name to visualize")
    parser.add_argument("--num-filters", type=int, default=64, help="Number of filters")
    parser.add_argument("--output", type=str, help="Output image path")
    parser.add_argument("--list-layers", action="store_true", help="List convolution layers")

    args = parser.parse_args()

    # Load model
    print(f"Loading model from {args.model}...")
    model = keras.models.load_model(args.model)

    if args.list_layers:
        print("\nConvolution layers in model:")
        for layer in list_conv_layers(model):
            filters = layer['filters'] if layer['filters'] is not None else "depthwise"
            print(f"  {layer['name']}: {filters} filters, kernel {layer['kernel_size']}")
        return

    if not args.layer:
        # Default to last conv layer
        conv_layers = list_conv_layers(model)
        if not conv_layers:
            print("No convolution layers found in model!")
            return
        args.layer = conv_layers[-1]["name"]
        print(f"No layer specified, using last conv layer: {args.layer}")

    visualize_layer_filters(
        model=model,
        layer_name=args.layer,
        num_filters=args.num_filters,
        save_path=args.output
    )


if __name__ == "__main__":
    main()
