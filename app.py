"""
Flask web application that fetches live METAR data and decodes it into
plain-English weather reports for a given ICAO airport code.
"""

from flask import Flask, render_template, request
import requests
from metar_parser import parse_metar

app = Flask(__name__)

METAR_API_URL = 'https://aviationweather.gov/api/data/metar'


@app.route('/', methods=['GET', 'POST'])
def index():
    """Render the main page and handle airport weather lookups.

    GET  — displays the empty search form.
    POST — fetches the METAR for the submitted airport code, parses it,
           and re-renders the page with the decoded weather report.
    """
    report = None
    error = None
    airport = ''

    if request.method == 'POST':
        airport = request.form.get('airport', '').upper().strip()

        if not airport:
            error = 'Please enter an airport code.'
        else:
            try:
                resp = requests.get(
                    METAR_API_URL,
                    params={'ids': airport},
                    timeout=10,
                )
                raw = resp.text.strip()

                if resp.status_code == 200 and raw:
                    report = parse_metar(raw)
                    # A valid METAR always contains a station ID; if it's
                    # missing, the API returned something we can't decode.
                    if not report['station']:
                        error = f"No METAR data found for '{airport}'. Check the airport code and try again."
                        report = None
                else:
                    error = f"No METAR data found for '{airport}'. Check the airport code and try again."

            except requests.RequestException:
                error = 'Unable to connect to the weather service. Please try again.'

    return render_template('index.html', report=report, error=error, airport=airport)


if __name__ == '__main__':
    app.run(debug=True)
