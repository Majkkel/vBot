# backend/src/intent_classifier.py
import pickle
import numpy as np
import spacy
import unicodedata
import tensorflow as tf
import os

# Ustalenie ścieżki do folderu models
current_dir = os.path.dirname(os.path.abspath(__file__))
models_dir = os.path.join(current_dir, "../models")

# Wczytanie modelu spaCy
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
    Tworzy wektor bag-of-words na podstawie znormalizowanego zdania.
    """
    sentence_words = preprocess_text(sentence)
    bag = [0] * len(words)
    for s in sentence_words:
        for i, w in enumerate(words):
            if w == s:
                bag[i] = 1
    return np.array(bag)

# Ładowanie modelu i pomocniczych danych z folderu models
model_path = os.path.join(models_dir, "chatbot_model.h5")
model = tf.keras.models.load_model(model_path)
words = pickle.load(open(os.path.join(models_dir, "words.pkl"), "rb"))
classes = pickle.load(open(os.path.join(models_dir, "classes.pkl"), "rb"))

def predict_intent(text, threshold=0.8, margin=0.2):
    """
    Zwraca przewidywaną intencję (tag) na podstawie tekstu wejściowego.
    Jeśli:
      - maksymalne prawdopodobieństwo jest mniejsze niż threshold
      - lub różnica między najwyższym a drugim najwyższym prawdopodobieństwem jest mniejsza niż margin
    to funkcja zwraca "nie_znaleziono".
    """
    bow = bag_of_words(text, words)
    results = model.predict(np.array([bow]))[0]
    max_prob = np.max(results)
    sorted_probs = np.sort(results)
    second_max = sorted_probs[-2] if len(sorted_probs) > 1 else 0

    if max_prob < threshold or (max_prob - second_max) < margin:
         return "nie_znaleziono"
    
    index = np.argmax(results)
    return classes[index]
