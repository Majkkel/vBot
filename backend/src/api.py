# backend/src/api.py
from flask import Flask, request, jsonify, send_file, g
from flask_cors import CORS
import re
import os
import tempfile
import time

from intent_classifier import predict_intent
from bot_logic import get_room_info
from responses import get_random_response
from speech import synthesize_to_file, recognize_speech_file

app = Flask(__name__)
CORS(app)

# Słownik do tymczasowego przechowywania rezerwacji
rezerwacje = {}
def remove_file(filename):
    try:
        os.remove(filename)
    except Exception as e:
        print("Błąd przy usuwaniu pliku tymczasowego TTS:", e)

@app.route('/chat', methods=['POST'])
def chat():
    data = request.get_json()
    user_input = data.get("text", "")
    
    # Używamy funkcji predict_intent z ustawionym threshold i margin
    intent = predict_intent(user_input, threshold=0.8, margin=0.2)
    
    # Logika odpowiadania na podstawie intencji
    if intent == "nie_znaleziono":
        response_text = "Nie rozumiem pytania."
    else:
        if intent == "lokalizacja_sali":
            room_numbers = re.findall(r'\d+', user_input)
            if room_numbers:
                room_number = room_numbers[0]
                response_text = get_room_info(room_number)
                response_text = response_text.replace("{number}", room_number)
            else:
                response_text = "Nie podałeś numeru sali."
        elif intent == "przywitanie":
            response_text = get_random_response("przywitanie")
        elif intent == "pożegnanie":
            response_text = get_random_response("pożegnanie")
        elif intent == "podziekowanie":
            response_text = get_random_response("podziekowanie")
        elif intent == "harmonogram":
            response_text = get_random_response("harmonogram")
        elif intent == "rezerwacja_sali":
            room_numbers = re.findall(r'\d+', user_input)
            if room_numbers:
                room_number = room_numbers[0]
                if room_number in rezerwacje:
                    response_text = f"Sala {room_number} jest już zarezerwowana."
                else:
                    rezerwacje[room_number] = "Zarezerwowana"
                    response_text = get_random_response("rezerwacja_sali")
                    response_text = response_text.replace("{number}", room_number)
            else:
                response_text = "Nie wiem jak na to odpowiedzieć"
        else:
            response_text = "Nie rozumiem pytania."
    
    return jsonify({"response": response_text, "intent": intent})

@app.route('/tts', methods=['POST'])
def tts():
    data = request.get_json()
    text = data.get("text", "")
    if not text:
        return jsonify({"error": "Nie podano tekstu"}), 400

    # Utwórz tymczasowy plik audio (.wav)
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
    tmp_filename = tmp.name
    tmp.close()  # Zamykamy plik, by pyttsx3 mógł do niego zapisać
    synthesize_to_file(text, tmp_filename)
    response = send_file(tmp_filename, mimetype="audio/wav")
    response.call_on_close(lambda: remove_file(tmp_filename))
    return response

@app.after_request
def remove_temp_file(response):
    temp_file = getattr(g, 'temp_file', None)
    if temp_file and os.path.exists(temp_file):
        try:
            os.remove(temp_file)
        except Exception as e:
            print("Błąd przy usuwaniu pliku tymczasowego:", e)
    return response

@app.route('/asr', methods=['POST'])
def asr():
    if 'audio' not in request.files:
        return jsonify({"error": "Nie przesłano pliku audio"}), 400

    audio_file = request.files['audio']
    temp = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
    audio_file.save(temp.name)
    temp_filename = temp.name
    temp.close()

    try:
        recognized_text = recognize_speech_file(temp_filename)
    except ValueError as e:
        recognized_text = "Błąd rozpoznawania: " + str(e)
    finally:
        # Spróbuj usunąć plik – jeśli nie uda się, odczekaj chwilę i spróbuj ponownie
        try:
            os.remove(temp_filename)
        except Exception as e:
            print("Pierwsza próba usunięcia pliku ASR nie powiodła się:", e)
            time.sleep(0.5)  # opóźnienie 500 ms
            try:
                os.remove(temp_filename)
            except Exception as e:
                print("Druga próba usunięcia pliku ASR nie powiodła się:", e)
    return jsonify({"text": recognized_text})

if __name__ == '__main__':
    app.run(debug=True)
