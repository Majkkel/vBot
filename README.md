# Kolejnosc pracy nad projektem

## 1️⃣🔍 Wykrywanie intencji i numeru sali (ML – scikit-learn + spaCy)

- Trenowanie modelu do klasyfikacji intencji (zapytanie_o_sale, przywitanie itd.).
- Ekstrakcja numeru sali z tekstu (NER w spaCy).
- Testowanie bota za pomocą zwykłego tekstu!

## 2️⃣ 📂 Przechowywanie informacji o salach (JSON, później SQL)

- Tworzenie pliku z danymi
- Funkcja wyszukująca numer sali w JSONIE

## 3️⃣ 🧠 Implementacja logiki bota

- Połączenie modelu ML z bazą sal
- Obsługa odpowiedzi na różne pytania

## 4️⃣ 🛠️ Budowa API (Flask) dla komunikacji frontend-backend

- Endpoint /query do przyjmowania pytań i zwracania odpowiedzi
- JSON jako format komunikacji frontend-backend

## 5️⃣ 🎤 Dodanie przetwarzania mowy (SpeechRecognition + pyttsx3)

- Konwersja mowy na tekst (SpeechRecognition)
- Konwersja tekstu na mowę (pyttsx3)

## 6️⃣ 🎨 Budowa frontendu (JS, możliwy framework UI w stylu neumorphism)

- Proste pole tekstowe + przycisk do nagrywania
- Wyświetlanie odpowiedzi bota
- Komunikacja z API

### instalacja

- pip install -r backend/requirements.txt
