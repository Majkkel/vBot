# backend/src/bot_logic.py
import os
import json

def load_room_data():
    """
    Wczytuje dane sal z pliku rooms.json znajdującego się w folderze data.
    """
    current_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(current_dir, "../data")
    file_path = os.path.join(data_dir, "rooms.json") 
    with open(file_path, "r", encoding="utf-8") as file:
        return json.load(file)

def get_room_info(room_number):
    """
    Zwraca sformatowaną informację o sali na podstawie numeru.
    """
    rooms = load_room_data()
    room = rooms.get(room_number)
    if room is None:
        return "Nie znaleziono takiej sali."
    
    info = (
        f"Sala {room['numer']} znajduje się w budynku {room['budynek']} "
        f"na {room['piętro']} piętrze. Opis: {room['lokalizacja']}. "
        f"Pojemność: {room['pojemność']} miejsc. "
        f"Dostępny sprzęt: {', '.join(room['sprzęt'])}."
    )
    return info
