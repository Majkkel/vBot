import json
import random
import os

# Ustalenie ścieżki do pliku intents.json
current_dir = os.path.dirname(os.path.abspath(__file__))
intents_path = os.path.join(current_dir, "..", "data", "intents.json")

with open(os.path.normpath(intents_path), encoding="utf-8") as file:
    intents = json.load(file)["intents"]

def get_random_response(tag):
    """Zwraca losową odpowiedź dla danego tagu intencji."""
    for intent in intents:
        if intent["tag"] == tag:
            return random.choice(intent["responses"])
    return "Nie rozumiem pytania."
