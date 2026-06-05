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

## Testing

### Unit & integration tests (`test_app.py`)

The main test suite uses [pytest](https://pytest.org) and covers two layers:

- **Parser tests** — feed raw METAR strings directly to `parse_metar()` and assert the decoded fields (wind, visibility, weather, sky, temperature, altimeter, summary). No network calls needed.
- **Flask route tests** — exercise the `/` GET and POST routes via Flask's test client with `requests.get` mocked, so no real API calls are made.

Run the full suite:

```bash
pytest test_app.py -v
```

Test classes at a glance:

| Class | What it covers |
|---|---|
| `TestWindParsing` | Calm, directional, variable, gusts, m/s units |
| `TestVisibilityParsing` | SM fractions, CAVOK, metric (km) |
| `TestWeatherParsing` | Rain, drizzle, fog, combined phenomena |
| `TestSkyParsing` | Clear, broken, overcast, CB/TCU annotations |
| `TestTemperatureParsing` | Positive/negative °C, °F conversion, `M` prefix |
| `TestAltimeterParsing` | inHg and hPa formats |
| `TestPrefixAndFlags` | METAR/SPECI prefixes, AUTO flag, RMK section |
| `TestSummaryGeneration` | Human-readable summary string |
| `TestFlaskRoutes` | HTTP 200, empty input, API errors, network errors |

### Smoke test (`test_parser.py`)

A lightweight script that runs four representative METAR strings through the parser and prints decoded output to the terminal — useful for quick visual checks during development.

```bash
python test_parser.py
```

### Dependencies

Testing requires `pytest` (included in `requirements.txt`). Install it with the regular `pip install -r requirements.txt` step.

---

## Project Structure

```
├── app.py              # Flask application and routing
├── metar_parser.py     # METAR decoding logic
├── templates/
│   └── index.html      # Front-end (single-page, no JS framework)
├── test_app.py         # pytest unit + Flask route tests
├── test_parser.py      # Quick parser smoke test (print output)
├── requirements.txt
└── README.md
```

---

## Data Source

Live METAR data is provided by the [Aviation Weather Center API](https://aviationweather.gov/api/data/metar) operated by NOAA. No API key is required.
