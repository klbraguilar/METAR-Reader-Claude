# METAR Weather Reader

A Flask web application that translates aviation weather reports (METARs) into plain English. Type any ICAO airport code and get a friendly, human-readable weather summary — no aviation knowledge required.

**Example output for KMCI (Kansas City International):**
> Partly cloudy, 79°F, from the south at 10 mph, gusting to 17 mph.

---

## What is a METAR?

A METAR is a standardized weather observation issued by airports around the world. They look like this:

```
KMCI 031552Z 22005KT 10SM FEW250 27/14 A2998 RMK AO2 SLP152
```

This app decodes that into:
- Temperature in °F and °C
- Wind direction (compass) and speed in mph
- Visibility in miles
- Sky conditions (clear, scattered, overcast, etc.)
- Dewpoint and barometric pressure
- Active weather (rain, snow, fog, thunderstorms, etc.)

---

## Requirements

- Python 3.8+
- An internet connection (live data is fetched from [aviationweather.gov](https://aviationweather.gov))

---

## Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/klbraguilar/METAR-Reader-Claude.git
   cd METAR-Reader-Claude
   ```

2. **Create and activate a virtual environment** (recommended)
   ```bash
   python -m venv venv

   # macOS / Linux
   source venv/bin/activate

   # Windows
   venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

---

## Running the App

```bash
python app.py
```

Then open your browser to `http://localhost:5000`.

For a production-style run using the Flask CLI:
```bash
flask run
```

---

## Usage

1. Enter a 4-character ICAO airport code (e.g. `KMCI`, `KJFK`, `KLAX`) into the search box.
2. Click **Get Weather**.
3. Read the plain-English weather report.

> **Tip:** ICAO codes for US airports start with `K`. International examples: `EGLL` (London Heathrow), `YSSY` (Sydney), `RJTT` (Tokyo Haneda).

---

## Project Structure

```
├── app.py              # Flask application and routing
├── metar_parser.py     # METAR decoding logic
├── templates/
│   └── index.html      # Front-end (single-page, no JS framework)
├── requirements.txt
└── README.md
```

---

## Data Source

Live METAR data is provided by the [Aviation Weather Center API](https://aviationweather.gov/api/data/metar) operated by NOAA. No API key is required.
