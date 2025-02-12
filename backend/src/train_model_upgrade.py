import os
import json
import numpy as np
import random
import pickle
from tensorflow.keras.preprocessing.text import Tokenizer
from tensorflow.keras.preprocessing.sequence import pad_sequences
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Embedding, LSTM, Dense, Dropout
from tensorflow.keras.optimizers import Adam

# Parametry modelu
MAX_NUM_WORDS = 10000      # maksymalna liczba unikalnych słów, które bierzemy pod uwagę
MAX_SEQUENCE_LENGTH = 20   # maksymalna długość sekwencji
EMBEDDING_DIM = 100        # wymiar wektorów osadzeń (embedding)
BATCH_SIZE = 16
EPOCHS = 50

# Ścieżka do pliku z danymi treningowymi (np. intents.json)
data_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../data/intents.json")
with open(data_path, encoding="utf-8") as f:
    data = json.load(f)

# Przygotowanie danych treningowych
texts = []    # przykłady (patterns)
labels = []   # odpowiadające tagi (etykiety)
label_map = {}  # mapowanie tag -> numer etykiety

# Przechodzimy po intencjach i zbieramy dane
for intent in data["intents"]:
    tag = intent["tag"]
    if tag not in label_map:
        label_map[tag] = len(label_map)
    for pattern in intent["patterns"]:
        texts.append(pattern)
        labels.append(label_map[tag])

# Tokenizacja tekstów
tokenizer = Tokenizer(num_words=MAX_NUM_WORDS, oov_token="<OOV>")
tokenizer.fit_on_texts(texts)
sequences = tokenizer.texts_to_sequences(texts)
X = pad_sequences(sequences, maxlen=MAX_SEQUENCE_LENGTH)

# Konwersja etykiet do formy one-hot
num_classes = len(label_map)
Y = np.eye(num_classes)[labels]

# Budowa modelu sekwencyjnego
model = Sequential()
model.add(Embedding(input_dim=MAX_NUM_WORDS, output_dim=EMBEDDING_DIM, input_length=MAX_SEQUENCE_LENGTH))
model.add(LSTM(128, return_sequences=False))
model.add(Dropout(0.5))
model.add(Dense(num_classes, activation='softmax'))

optimizer = Adam(learning_rate=0.001)
model.compile(loss='categorical_crossentropy', optimizer=optimizer, metrics=['accuracy'])
model.summary()

# Trenowanie modelu
history = model.fit(X, Y, epochs=EPOCHS, batch_size=BATCH_SIZE, validation_split=0.2, verbose=1)

# Zapisywanie wytrenowanego modelu i niezbędnych obiektów
models_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../models")
if not os.path.exists(models_dir):
    os.makedirs(models_dir)
model.save(os.path.join(models_dir, "chatbot_model_upgrade.h5"))

# Zapis tokenizera i mapowania etykiet
with open(os.path.join(models_dir, "tokenizer.pkl"), "wb") as f:
    pickle.dump(tokenizer, f)
with open(os.path.join(models_dir, "label_map.pkl"), "wb") as f:
    pickle.dump(label_map, f)

print("Model treningowy został zapisany.")
