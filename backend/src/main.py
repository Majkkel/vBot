import os
import json
import re

from intent_classifier import predict_intent
from responses import get_random_response  # Bazowe odpowiedzi z intents.json
from bot_logic import get_room_info
from speech import speak

bot_name = "Bocik"
def get_major_plan_dynamic(user_input):
    """
    Wczytuje dostępne kierunki z pliku plans.json (klucze obiektu).
    Następnie przeszukuje wiadomość użytkownika (po konwersji do małych liter)
    i sprawdza, czy któryś z tokenów odpowiada jednemu z dostępnych kierunków.
    Jeśli tak, zwraca plan zajęć dla danego kierunku.
    
    Dodatkowo, jeśli w wiadomości pojawi się nazwa dnia tygodnia (np. "środa"),
    zwraca plan tylko dla tego dnia, w przeciwnym razie – cały harmonogram.
    
    Zwraca krotkę (chosen_major, plan_text) lub (None, None) jeśli nie znaleziono kierunku.
    """
    # Ścieżka do pliku plans.json
    plans_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../data/plans.json")
    try:
        with open(plans_path, "r", encoding="utf-8") as f:
            plans = json.load(f)
    except Exception as e:
        return None, f"Błąd odczytu plans.json: {e}"
    
    # Pobieramy dostępne kierunki dynamicznie – klucze z plans.json
    available_majors = set(plans.keys())
    inp = user_input.lower()
    tokens = re.findall(r'\w+', inp)
    
    chosen_major = None
    for token in tokens:
        if token in available_majors:
            chosen_major = token
            break
    if not chosen_major:
        return None, None

    schedule = plans.get(chosen_major, {})

    # Definiujemy zbiór nazw dni
    days = {"poniedziałek", "wtorek", "środa", "czwartek", "piątek", "sobota", "niedziela"}
    chosen_day = None
    for token in tokens:
        if token in days:
            chosen_day = token
            break

    if chosen_day:
        if chosen_day in schedule:
            day_plan = schedule[chosen_day]
            # Jeśli plan jest listą (przy typowej strukturze), formatujemy każdą sesję
            if isinstance(day_plan, list):
                if len(day_plan) > 0:
                    sessions_list = [
                        f"{session['godzina']} - {session['przedmiot']} (sala {session['sala']})"
                        for session in day_plan
                    ]
                    plan_text = f"{chosen_day.capitalize()}: " + "; ".join(sessions_list)
                    return chosen_major, plan_text
                else:
                    return chosen_major, f"Brak zajęć zaplanowanych na {chosen_day}."
            else:
                # Jeśli nie jest listą (np. ciąg znaków), traktujemy to jako gotowy tekst
                if day_plan.strip():
                    plan_text = f"{chosen_day.capitalize()}: {day_plan}"
                    return chosen_major, plan_text
                else:
                    return chosen_major, f"Brak zajęć zaplanowanych na {chosen_day}."
        else:
            return chosen_major, f"Brak planu zajęć dla dnia {chosen_day}."
    else:
        # Jeśli nie wskazano konkretnego dnia, łączymy plan dla wszystkich dni
        response_lines = []
        for day, day_plan in schedule.items():
            if isinstance(day_plan, list):
                if len(day_plan) > 0:
                    sessions_list = [
                        f"{session['godzina']} - {session['przedmiot']} (sala {session['sala']})"
                        for session in day_plan
                    ]
                    response_lines.append(f"{day.capitalize()}: " + "; ".join(sessions_list))
            else:
                if day_plan.strip():
                    response_lines.append(f"{day.capitalize()}: {day_plan}")
        if response_lines:
            return chosen_major, "\n".join(response_lines)
        else:
            return chosen_major, "Brak zajęć zaplanowanych dla tego kierunku."
        
def get_room_schedule(room_number):
    """
    Odczytuje harmonogram sali z pliku rooms.json dla danej sali.
    Zwraca wartość pola "harmonogram" lub komunikat o braku danych.
    """
    current_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(current_dir, "../data")
    file_path = os.path.join(data_dir, "rooms.json")
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            rooms = json.load(f)
        room = rooms.get(room_number)
        if room and "harmonogram" in room:
            return room["harmonogram"]
        else:
            return "Brak harmonogramu dla tej sali."
    except Exception as e:
        return f"Błąd odczytu danych sal: {e}"

def format_room_schedule(schedule):
    """
    Formatuje harmonogram sali (jeśli jest obiektem typu dict) do czytelnego ciągu tekstowego.
    """
    if isinstance(schedule, dict):
        lines = []
        for day, info in schedule.items():
            if info and info.strip():
                lines.append(f"{day.capitalize()}: {info}")
        return "\n".join(lines) if lines else "Brak zajęć zaplanowanych."
    else:
        return schedule

def get_events():
    """
    Odczytuje nadchodzące wydarzenia z pliku events.json.
    """
    events_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../data/events.json")
    try:
        with open(events_path, "r", encoding="utf-8") as f:
            events_data = json.load(f)
        events_list = events_data.get("wydarzenia", [])
        if not events_list:
            return "Brak nadchodzących wydarzeń."
        return "\n".join(
            [f"{event['tytuł']} ({event['data']}): {event['opis']}" for event in events_list]
        )
    except Exception as e:
        return f"Błąd odczytu wydarzeń: {e}"

def main():
    print("Witaj w chatbotcie! (Wpisz 'exit' aby zakończyć)")
    while True:
        user_input = input("Ty: ")
        if user_input.lower() in ['exit', 'quit']:
            response = "Do widzenia!"
            print(f"{bot_name}: {response}")
            speak(response)
            break

        intent = predict_intent(user_input, threshold=0.8, margin=0.2)

        if intent == "nie_znaleziono":
            response = "Nie rozumiem pytania."
        else:
            if intent == "lokalizacja_sali":
                room_numbers = re.findall(r'\d+', user_input)
                if room_numbers:
                    room_number = room_numbers[0]
                    response = get_random_response("lokalizacja_sali")
                    response = response.replace("{number}", room_number)
                else:
                    response = "Nie podałeś numeru sali."
            elif intent == "przywitanie":
                response = get_random_response("przywitanie")
            elif intent == "pożegnanie":
                response = get_random_response("pożegnanie")
            elif intent == "podziękowanie":
                response = get_random_response("podziękowanie")
            elif intent == "plan_zajec_kierunkowy":
                major, plan = get_major_plan_dynamic(user_input)
                if plan:
                    response = get_random_response("plan_zajec_kierunkowy").replace("{kierunek}", major).replace("{plan}", plan)
                else:
                    response = ("Nie mogę znaleźć planu zajęć dla tego kierunku. "
                                "Upewnij się, że podałeś jeden z kierunków: informatyka, matematyka, fizyka, chemia.")
            elif intent == "plan_zajec_sala":
                room_numbers = re.findall(r'\d+', user_input)
                if room_numbers:
                    room_number = room_numbers[0]
                    response = get_random_response("plan_zajec_sala")
                    schedule = get_room_schedule(room_number)
                    formatted_schedule = format_room_schedule(schedule)
                    response = response.replace("{harmonogram}", formatted_schedule)
                    response = response.replace("{number}", room_number)
                else:
                    response = "Nie podałeś numeru sali."
            elif intent == "informacja_o_wydarzeniach":
                response = get_random_response("informacja_o_wydarzeniach")
                events = get_events()
                response = response.replace("{wydarzenia}", events)
            elif intent == "kontakt_administracji":
                response = get_random_response("kontakt_administracji")
            else:
                response = "Nie rozumiem pytania."

        print(f"{bot_name}: {response}")
        speak(response)

if __name__ == "__main__":
    main()
