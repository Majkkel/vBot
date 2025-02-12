# backend/src/speech.py
import speech_recognition as sr
import pyttsx3

def recognize_speech():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        print("Powiedz coś...")
        audio = recognizer.listen(source)
        text = recognizer.recognize_google(audio, language="pl-PL")
        print(text)
        return text
    try:
        text = recognizer.recognize_google(audio, language="pl-PL")
        return text
    except sr.UnknownValueError:
        return "Nie udało się rozpoznać mowy."
    except sr.RequestError:
        return "Błąd usługi rozpoznawania mowy."

def recognize_speech_file(file_path):
    """
    Rozpoznaje mowę z pliku audio i zwraca rozpoznany tekst.
    """
    recognizer = sr.Recognizer()
    with sr.AudioFile(file_path) as source:
        audio_data = recognizer.record(source)
    try:
        text = recognizer.recognize_google(audio_data, language="pl-PL")
        return text
    except sr.UnknownValueError:
        return "Nie udało się rozpoznać mowy."
    except sr.RequestError:
        return "Błąd usługi rozpoznawania mowy."

def speak(text):
    engine = pyttsx3.init()
    engine.say(text)
    engine.runAndWait()

def synthesize_to_file(text, file_path):
    """
    Generuje mowę z podanego tekstu i zapisuje ją do pliku (np. .wav).
    """
    engine = pyttsx3.init()
    engine.save_to_file(text, file_path)
    engine.runAndWait()
