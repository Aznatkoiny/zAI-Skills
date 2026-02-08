# Deep Learning for Text & Transformers

## Table of Contents
- [Text Preprocessing](#text-preprocessing)
- [Bag-of-Words Approaches](#bag-of-words-approaches)
- [Word Embeddings](#word-embeddings)
- [Transformer Architecture](#transformer-architecture)
- [Sequence-to-Sequence Learning](#sequence-to-sequence-learning)
- [When to Use Which Approach](#when-to-use-which-approach)

## Text Preprocessing

### TextVectorization Layer
```python
from tensorflow.keras.layers import TextVectorization

text_vectorization = TextVectorization(
    max_tokens=20000,           # Vocabulary size
    output_mode="int",          # Output integer indices
    output_sequence_length=600, # Pad/truncate to this length
)

# Fit on training data
text_only_train_ds = train_ds.map(lambda x, y: x)
text_vectorization.adapt(text_only_train_ds)

# Apply to datasets
int_train_ds = train_ds.map(lambda x, y: (text_vectorization(x), y))
```

### Output Modes
```python
# Integer sequences (for RNNs, Transformers)
TextVectorization(output_mode="int", output_sequence_length=600)

# Binary bag-of-words
TextVectorization(output_mode="multi_hot", max_tokens=20000)

# TF-IDF weighted
TextVectorization(output_mode="tf_idf", max_tokens=20000)

# N-grams (bigrams)
TextVectorization(ngrams=2, output_mode="multi_hot", max_tokens=20000)
```

### Custom Standardization
```python
import re, string

def custom_standardization(input_string):
    lowercase = tf.strings.lower(input_string)
    return tf.strings.regex_replace(
        lowercase, f"[{re.escape(string.punctuation)}]", "")

text_vectorization = TextVectorization(
    standardize=custom_standardization,
    split="whitespace",
)
```

## Bag-of-Words Approaches

Simple but effective for many text classification tasks:

```python
# Binary unigram model
text_vectorization = TextVectorization(max_tokens=20000, output_mode="multi_hot")
text_vectorization.adapt(text_only_train_ds)

inputs = keras.Input(shape=(20000,))
x = layers.Dense(16, activation="relu")(inputs)
x = layers.Dropout(0.5)(x)
outputs = layers.Dense(1, activation="sigmoid")(x)
model = keras.Model(inputs, outputs)
model.compile(optimizer="rmsprop", loss="binary_crossentropy", metrics=["accuracy"])
```

## Word Embeddings

### Learning Embeddings from Scratch
```python
inputs = keras.Input(shape=(None,), dtype="int64")
embedded = layers.Embedding(input_dim=max_tokens, output_dim=256)(inputs)
x = layers.Bidirectional(layers.LSTM(32))(embedded)
x = layers.Dropout(0.5)(x)
outputs = layers.Dense(1, activation="sigmoid")(x)
model = keras.Model(inputs, outputs)
```

### Masking Padded Values
```python
# mask_zero=True tells downstream layers to ignore padding (index 0)
embedded = layers.Embedding(
    input_dim=max_tokens,
    output_dim=256,
    mask_zero=True
)(inputs)
```

### Using Pretrained Embeddings (GloVe)
```python
# Load GloVe embeddings
embeddings_index = {}
with open("glove.6B.100d.txt") as f:
    for line in f:
        word, coefs = line.split(maxsplit=1)
        coefs = np.fromstring(coefs, "f", sep=" ")
        embeddings_index[word] = coefs

# Create embedding matrix
embedding_dim = 100
vocabulary = text_vectorization.get_vocabulary()
word_index = dict(zip(vocabulary, range(len(vocabulary))))

embedding_matrix = np.zeros((max_tokens, embedding_dim))
for word, i in word_index.items():
    if i < max_tokens:
        embedding_vector = embeddings_index.get(word)
        if embedding_vector is not None:
            embedding_matrix[i] = embedding_vector

# Create frozen embedding layer
embedding_layer = layers.Embedding(
    max_tokens,
    embedding_dim,
    embeddings_initializer=keras.initializers.Constant(embedding_matrix),
    trainable=False,  # Freeze pretrained weights
    mask_zero=True,
)
```

## Transformer Architecture

### Positional Embedding
Transformers are order-agnostic, so we inject position information:

```python
class PositionalEmbedding(layers.Layer):
    def __init__(self, sequence_length, input_dim, output_dim, **kwargs):
        super().__init__(**kwargs)
        self.token_embeddings = layers.Embedding(input_dim, output_dim)
        self.position_embeddings = layers.Embedding(sequence_length, output_dim)
        self.sequence_length = sequence_length
        self.input_dim = input_dim
        self.output_dim = output_dim

    def call(self, inputs):
        length = tf.shape(inputs)[-1]
        positions = tf.range(start=0, limit=length, delta=1)
        embedded_tokens = self.token_embeddings(inputs)
        embedded_positions = self.position_embeddings(positions)
        return embedded_tokens + embedded_positions

    def compute_mask(self, inputs, mask=None):
        return tf.math.not_equal(inputs, 0)

    def get_config(self):
        config = super().get_config()
        config.update({
            "sequence_length": self.sequence_length,
            "input_dim": self.input_dim,
            "output_dim": self.output_dim,
        })
        return config
```

### Transformer Encoder
For text classification, sequence encoding:

```python
class TransformerEncoder(layers.Layer):
    def __init__(self, embed_dim, dense_dim, num_heads, **kwargs):
        super().__init__(**kwargs)
        self.embed_dim = embed_dim
        self.dense_dim = dense_dim
        self.num_heads = num_heads
        self.attention = layers.MultiHeadAttention(
            num_heads=num_heads, key_dim=embed_dim)
        self.dense_proj = keras.Sequential([
            layers.Dense(dense_dim, activation="relu"),
            layers.Dense(embed_dim),
        ])
        self.layernorm_1 = layers.LayerNormalization()
        self.layernorm_2 = layers.LayerNormalization()

    def call(self, inputs, mask=None):
        if mask is not None:
            mask = mask[:, tf.newaxis, :]
        attention_output = self.attention(inputs, inputs, attention_mask=mask)
        proj_input = self.layernorm_1(inputs + attention_output)
        proj_output = self.dense_proj(proj_input)
        return self.layernorm_2(proj_input + proj_output)

    def get_config(self):
        config = super().get_config()
        config.update({
            "embed_dim": self.embed_dim,
            "dense_dim": self.dense_dim,
            "num_heads": self.num_heads,
        })
        return config
```

### Text Classification with Transformer
```python
vocab_size = 20000
sequence_length = 600
embed_dim = 256
num_heads = 2
dense_dim = 32

inputs = keras.Input(shape=(None,), dtype="int64")
x = PositionalEmbedding(sequence_length, vocab_size, embed_dim)(inputs)
x = TransformerEncoder(embed_dim, dense_dim, num_heads)(x)
x = layers.GlobalMaxPooling1D()(x)
x = layers.Dropout(0.5)(x)
outputs = layers.Dense(1, activation="sigmoid")(x)
model = keras.Model(inputs, outputs)
```

## Sequence-to-Sequence Learning

### Transformer Decoder
For generation tasks (translation, text generation):

```python
class TransformerDecoder(layers.Layer):
    def __init__(self, embed_dim, dense_dim, num_heads, **kwargs):
        super().__init__(**kwargs)
        self.embed_dim = embed_dim
        self.dense_dim = dense_dim
        self.num_heads = num_heads
        self.attention_1 = layers.MultiHeadAttention(num_heads=num_heads, key_dim=embed_dim)
        self.attention_2 = layers.MultiHeadAttention(num_heads=num_heads, key_dim=embed_dim)
        self.dense_proj = keras.Sequential([
            layers.Dense(dense_dim, activation="relu"),
            layers.Dense(embed_dim),
        ])
        self.layernorm_1 = layers.LayerNormalization()
        self.layernorm_2 = layers.LayerNormalization()
        self.layernorm_3 = layers.LayerNormalization()
        self.supports_masking = True

    def get_causal_attention_mask(self, inputs):
        input_shape = tf.shape(inputs)
        batch_size, sequence_length = input_shape[0], input_shape[1]
        i = tf.range(sequence_length)[:, tf.newaxis]
        j = tf.range(sequence_length)
        mask = tf.cast(i >= j, dtype="int32")
        mask = tf.reshape(mask, (1, sequence_length, sequence_length))
        mult = tf.concat([tf.expand_dims(batch_size, -1), tf.constant([1, 1], dtype=tf.int32)], axis=0)
        return tf.tile(mask, mult)

    def call(self, inputs, encoder_outputs, mask=None):
        causal_mask = self.get_causal_attention_mask(inputs)
        if mask is not None:
            padding_mask = tf.cast(mask[:, tf.newaxis, :], dtype="int32")
            padding_mask = tf.minimum(padding_mask, causal_mask)

        # Self-attention (masked)
        attention_output_1 = self.attention_1(
            query=inputs, value=inputs, key=inputs, attention_mask=causal_mask)
        attention_output_1 = self.layernorm_1(inputs + attention_output_1)

        # Cross-attention with encoder outputs
        attention_output_2 = self.attention_2(
            query=attention_output_1,
            value=encoder_outputs,
            key=encoder_outputs,
            attention_mask=padding_mask)
        attention_output_2 = self.layernorm_2(attention_output_1 + attention_output_2)

        proj_output = self.dense_proj(attention_output_2)
        return self.layernorm_3(attention_output_2 + proj_output)

    def get_config(self):
        config = super().get_config()
        config.update({
            "embed_dim": self.embed_dim,
            "dense_dim": self.dense_dim,
            "num_heads": self.num_heads,
        })
        return config
```

### End-to-End Transformer (Machine Translation)
```python
embed_dim = 256
dense_dim = 2048
num_heads = 8

# Encoder
encoder_inputs = keras.Input(shape=(None,), dtype="int64", name="english")
x = PositionalEmbedding(sequence_length, vocab_size, embed_dim)(encoder_inputs)
encoder_outputs = TransformerEncoder(embed_dim, dense_dim, num_heads)(x)

# Decoder
decoder_inputs = keras.Input(shape=(None,), dtype="int64", name="spanish")
x = PositionalEmbedding(sequence_length, vocab_size, embed_dim)(decoder_inputs)
x = TransformerDecoder(embed_dim, dense_dim, num_heads)(x, encoder_outputs)
x = layers.Dropout(0.5)(x)
decoder_outputs = layers.Dense(vocab_size, activation="softmax")(x)

transformer = keras.Model([encoder_inputs, decoder_inputs], decoder_outputs)
transformer.compile(optimizer="rmsprop", loss="sparse_categorical_crossentropy", metrics=["accuracy"])
```

### Inference (Decoding)
```python
def decode_sequence(input_sentence):
    tokenized_input = source_vectorization([input_sentence])
    decoded_sentence = "[start]"

    for i in range(max_decoded_length):
        tokenized_target = target_vectorization([decoded_sentence])[:, :-1]
        predictions = transformer([tokenized_input, tokenized_target])
        sampled_token_index = np.argmax(predictions[0, i, :])
        sampled_token = spa_index_lookup[sampled_token_index]
        decoded_sentence += " " + sampled_token
        if sampled_token == "[end]":
            break

    return decoded_sentence
```

## When to Use Which Approach

| Data Size | Approach |
|-----------|----------|
| < 500 samples | Bag-of-words + Dense |
| 500 - 5,000 | Bag-of-words or sequence model |
| > 5,000 | Sequence models (LSTM, Transformer) |

Sequence models capture word order and are better when order matters (sentiment, QA).
Bag-of-words is faster and works well for topic classification.
