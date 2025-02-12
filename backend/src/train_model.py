# backend/src/train_model.py
import json
import numpy as np
import random
import spacy
import unicodedata
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, Dropout
from tensorflow.keras.optimizers import SGD
import pickle
import os

# Ustalenie ścieżek
current_dir = os.path.dirname(os.path.abspath(__file__))
data_dir = os.path.join(current_dir, "../data")
models_dir = os.path.join(current_dir, "../models")

# Wczytanie modelu spaCy dla języka polskiego
nlp = spacy.load("pl_core_news_sm")

def normalize_text(text):
    """Normalizuje tekst, usuwając znaki diakrytyczne."""
    normalized = unicodedata.normalize('NFD', text)
    return ''.join([c for c in normalized if unicodedata.category(c) != 'Mn'])

def preprocess_text(text):
    """
    Przetwarza tekst:
      1. Normalizacja (usuwanie diakrytyków)
      2. Tokenizacja, lematyzacja, konwersja do małych liter
      3. Filtrowanie – pozostawiamy tylko tokeny alfabetyczne
    """
    text = normalize_text(text)
    doc = nlp(text)
    tokens = [token.lemma_.lower() for token in doc if token.is_alpha]
    return tokens

def bag_of_words(sentence, words):
    """
    Tworzy wektor reprezentujący "bag-of-words" na podstawie znormalizowanego zdania.
    """
    sentence_words = preprocess_text(sentence)
    bag = [0] * len(words)
    for s in sentence_words:
        for i, w in enumerate(words):
            if w == s:
                bag[i] = 1
    return np.array(bag)

# Wczytanie danych z intents.json znajdującego się w folderze data
intents_file = os.path.join(data_dir, "intents.json")
with open(intents_file, encoding="utf-8") as json_data:
    intents = json.load(json_data)

words = []       # lista unikalnych słów (po preprocessing'u)
classes = []     # lista tagów (intencji)
documents = []   # lista par: (oryginalny pattern, tag)

# Przetwarzanie danych z intents.json
for intent in intents["intents"]:
    for pattern in intent["patterns"]:
        tokens = preprocess_text(pattern)
        words.extend(tokens)
        documents.append((pattern, intent["tag"]))
    if intent["tag"] not in classes:
        classes.append(intent["tag"])

# Usunięcie duplikatów i sortowanie
words = sorted(list(set(words)))
classes = sorted(list(set(classes)))

# Przygotowanie danych treningowych
training = []
output_empty = [0] * len(classes)

for doc in documents:
    bow = bag_of_words(doc[0], words)
    output_row = list(output_empty)
    output_row[classes.index(doc[1])] = 1
    training.append([bow, output_row])

# Tasowanie danych
random.shuffle(training)
training = np.array(training, dtype=object)

# Rozdzielenie na dane wejściowe (X) i etykiety (y)
train_x = np.array(list(training[:, 0]))
train_y = np.array(list(training[:, 1]))

# Budowanie modelu sieci neuronowej
model = Sequential()
model.add(Dense(128, input_shape=(len(train_x[0]),), activation='relu'))
model.add(Dropout(0.5))
model.add(Dense(64, activation='relu'))
model.add(Dropout(0.5))
model.add(Dense(len(train_y[0]), activation='softmax'))

# Konfiguracja optymalizatora
sgd = SGD(learning_rate=0.01, decay=1e-6, momentum=0.9, nesterov=True)
model.compile(loss='categorical_crossentropy', optimizer=sgd, metrics=['accuracy'])

# Trenowanie modelu
model.fit(train_x, train_y, epochs=200, batch_size=5, verbose=1)

# Zapis wytrenowanego modelu i pomocniczych danych do folderu models
model_save_path = os.path.join(models_dir, "chatbot_model.h5")
model.save(model_save_path)
print(f"Model treningowy zapisany do pliku '{model_save_path}'")

pickle.dump(words, open(os.path.join(models_dir, "words.pkl"), "wb"))
pickle.dump(classes, open(os.path.join(models_dir, "classes.pkl"), "wb"))
