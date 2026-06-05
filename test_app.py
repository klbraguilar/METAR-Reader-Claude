"""
Unit tests for the METAR reader application.

Two layers:
  1. Parser tests  — feed raw METAR strings to parse_metar() and assert
                     the returned dict (pure function, no mocking needed).
  2. Flask route tests — use the Flask test client with requests.get mocked
                         so no real HTTP calls are made.

Run with:  pytest test_app.py -v
"""

import pytest
import requests as req_module
from unittest.mock import patch, Mock

from metar_parser import parse_metar
from app import app


# ── Fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as c:
        yield c


def _mock_api(text, status=200):
    """Return a Mock that mimics a requests.Response with given text/status."""
    m = Mock()
    m.status_code = status
    m.text = text
    return m


# ── Parser: Wind ─────────────────────────────────────────────────────────────

class TestWindParsing:
    def test_calm_wind(self):
        r = parse_metar("KJFK 031552Z 00000KT 10SM SKC 20/10 A2990")
        assert r['wind'] == 'Calm'

    def test_directional_wind_knots(self):
        r = parse_metar("KLAX 031552Z 27015KT 10SM SKC 22/08 A2998")
        assert 'West' in r['wind']
        assert 'mph' in r['wind']

    def test_variable_wind(self):
        r = parse_metar("KORD 031552Z VRB05KT 10SM SKC 20/10 A2990")
        assert r['wind'].startswith('Variable direction')

    def test_gust(self):
        r = parse_metar("KJFK 031552Z 05012G22KT 10SM SKC 18/16 A2985")
        assert 'gusting' in r['wind']

    def test_wind_mps_units(self):
        r = parse_metar("EGLL 031552Z 09010MPS 10SM SKC 15/10 Q1013")
        assert 'mph' in r['wind']

    def test_wind_variable_range_skipped(self):
        r = parse_metar("KJFK 031552Z 27010KT 040V100 10SM SKC 20/10 A2990")
        assert r['wind'] != ''
        assert r['station'] == 'KJFK'


# ── Parser: Visibility ────────────────────────────────────────────────────────

class TestVisibilityParsing:
    def test_ten_or_more_sm(self):
        r = parse_metar("KJFK 031552Z 27010KT 10SM SKC 20/10 A2990")
        assert r['visibility'] == '10+ miles'

    def test_less_than_fractional_sm(self):
        r = parse_metar("KORD 031552Z VRB05KT M1/4SM FG OVC002 M02/M04 A3010")
        assert r['visibility'].startswith('Less than')

    def test_fractional_sm(self):
        r = parse_metar("KBOS 031552Z 18010KT 1/2SM RA OVC010 15/12 A2980")
        assert '0.50' in r['visibility']

    def test_whole_and_fraction_sm(self):
        r = parse_metar("KBOS 031552Z 18010KT 1 1/2SM RA OVC010 15/12 A2980")
        assert '1.50' in r['visibility']

    def test_cavok(self):
        r = parse_metar("EGLL 031552Z 09010KT CAVOK 15/10 Q1013")
        assert r['visibility'] == '10+ miles'

    def test_metric_9999(self):
        r = parse_metar("EGLL 031552Z 09010KT 9999 SKC 15/10 Q1013")
        assert r['visibility'] == '10+ km'

    def test_metric_below_max(self):
        r = parse_metar("EGLL 031552Z 09010KT 0800 FG OVC002 05/04 Q1010")
        assert r['visibility'] == '0.8 km'


# ── Parser: Present Weather ───────────────────────────────────────────────────

class TestWeatherParsing:
    def test_heavy_thunderstorm_rain(self):
        r = parse_metar("KJFK 031552Z 05012G22KT 2SM +TSRA BKN008 OVC020 18/16 A2985")
        wx = r['weather']
        assert any('heavy' in w and 'rain' in w for w in wx)

    def test_light_drizzle(self):
        r = parse_metar("KBOS 031552Z 18010KT 5SM -DZ OVC015 12/11 A2980")
        wx = r['weather']
        assert any('light' in w and 'drizzle' in w for w in wx)

    def test_fog(self):
        r = parse_metar("KORD 031552Z VRB05KT 1/4SM FG OVC002 M02/M04 A3010")
        assert any('fog' in w for w in r['weather'])

    def test_combined_phenomena(self):
        r = parse_metar("KJFK 031552Z 05012G22KT 2SM RASN OVC010 02/01 A2990")
        assert any('rain' in w and 'snow' in w for w in r['weather'])

    def test_no_weather_phenomena(self):
        r = parse_metar("KLAX 031552Z 27003KT 10SM SKC 22/08 A2998")
        assert r['weather'] == []


# ── Parser: Sky Conditions ────────────────────────────────────────────────────

class TestSkyParsing:
    def test_clear_skies(self):
        r = parse_metar("KLAX 031552Z 27003KT 10SM SKC 22/08 A2998")
        assert any('Clear' in s for s in r['sky'])

    def test_broken_layer(self):
        r = parse_metar("KJFK 031552Z 05012G22KT 2SM +TSRA BKN008 OVC020 18/16 A2985")
        assert any('Broken' in s for s in r['sky'])

    def test_overcast(self):
        r = parse_metar("KJFK 031552Z 05012G22KT 2SM +TSRA BKN008 OVC020 18/16 A2985")
        assert any('Overcast' in s for s in r['sky'])

    def test_cloud_height_in_feet(self):
        r = parse_metar("KJFK 031552Z 05012G22KT 2SM +TSRA BKN008 OVC020 18/16 A2985")
        # BKN008 → 800 ft
        assert any('800 ft' in s for s in r['sky'])

    def test_cumulonimbus_annotation(self):
        r = parse_metar("KJFK 031552Z 05012G22KT 2SM TSRA BKN010CB 18/16 A2985")
        assert any('cumulonimbus' in s for s in r['sky'])

    def test_towering_cumulus_annotation(self):
        r = parse_metar("KJFK 031552Z 05012G22KT 5SM SCT020TCU 20/15 A2990")
        assert any('towering cumulus' in s for s in r['sky'])

    def test_multiple_sky_layers(self):
        r = parse_metar("KJFK 031552Z 05012G22KT 2SM +TSRA BKN008 OVC020 18/16 A2985")
        assert len(r['sky']) == 2


# ── Parser: Temperature / Dewpoint ────────────────────────────────────────────

class TestTemperatureParsing:
    def test_positive_temperature_celsius(self):
        r = parse_metar("KLAX 031552Z 27003KT 10SM SKC 22/08 A2998")
        assert r['temp_c'] == 22

    def test_positive_temperature_fahrenheit(self):
        r = parse_metar("KLAX 031552Z 27003KT 10SM SKC 22/08 A2998")
        assert r['temp_f'] == 72  # round(22 * 9/5 + 32) = round(71.6) = 72

    def test_negative_temperature_m_prefix(self):
        r = parse_metar("KORD 031552Z VRB05KT 1/4SM FG OVC002 M02/M04 A3010")
        assert r['temp_c'] == -2

    def test_negative_temp_fahrenheit(self):
        r = parse_metar("KORD 031552Z VRB05KT 1/4SM FG OVC002 M02/M04 A3010")
        assert r['temp_f'] == 28  # round(-2 * 9/5 + 32) = round(28.4) = 28

    def test_temperature_display_format(self):
        r = parse_metar("KLAX 031552Z 27003KT 10SM SKC 22/08 A2998")
        assert '°F' in r['temperature']
        assert '°C' in r['temperature']

    def test_dewpoint_display_format(self):
        r = parse_metar("KLAX 031552Z 27003KT 10SM SKC 22/08 A2998")
        assert '8°C' in r['dewpoint']


# ── Parser: Altimeter ─────────────────────────────────────────────────────────

class TestAltimeterParsing:
    def test_inches_hg(self):
        r = parse_metar("KLAX 031552Z 27003KT 10SM SKC 22/08 A2998")
        assert r['altimeter'] == '29.98 inHg'

    def test_hectopascals(self):
        r = parse_metar("EGLL 031552Z 09010KT CAVOK 15/10 Q1013")
        assert r['altimeter'] == '1013 hPa'


# ── Parser: Prefix / Flag Handling ───────────────────────────────────────────

class TestPrefixAndFlags:
    def test_metar_prefix_stripped(self):
        r = parse_metar("METAR KJFK 031552Z 27010KT 10SM SKC 20/10 A2990")
        assert r['station'] == 'KJFK'

    def test_speci_prefix_stripped(self):
        r = parse_metar("SPECI KJFK 031552Z 27010KT 10SM SKC 20/10 A2990")
        assert r['station'] == 'KJFK'

    def test_auto_flag_skipped(self):
        r = parse_metar("KJFK 031552Z AUTO 27010KT 10SM SKC 20/10 A2990")
        assert r['station'] == 'KJFK'
        assert r['wind'] != ''

    def test_remarks_section_ignored(self):
        r = parse_metar("KJFK 031552Z 27010KT 10SM SKC 20/10 A2990 RMK AO2 SLP089")
        assert r['altimeter'] == '29.90 inHg'
        assert r['station'] == 'KJFK'

    def test_observation_time_parsed(self):
        r = parse_metar("KJFK 031552Z 27010KT 10SM SKC 20/10 A2990")
        assert r['time_utc'] == '15:52 UTC'


# ── Parser: Summary ───────────────────────────────────────────────────────────

class TestSummaryGeneration:
    def test_clear_summary(self):
        r = parse_metar("KLAX 031552Z 27003KT 10SM SKC 22/08 A2998")
        assert 'Clear' in r['summary']

    def test_weather_phenomena_in_summary(self):
        r = parse_metar("KJFK 031552Z 05012G22KT 2SM +TSRA BKN008 OVC020 18/16 A2985")
        assert 'rain' in r['summary'].lower() or 'thunderstorm' in r['summary'].lower()

    def test_temperature_in_summary(self):
        r = parse_metar("KLAX 031552Z 27003KT 10SM SKC 22/08 A2998")
        assert '°F' in r['summary']

    def test_wind_in_summary(self):
        r = parse_metar("KLAX 031552Z 27003KT 10SM SKC 22/08 A2998")
        assert 'mph' in r['summary']

    def test_low_visibility_in_summary(self):
        r = parse_metar("KORD 031552Z VRB05KT 1/4SM FG OVC002 M02/M04 A3010")
        assert 'visibility' in r['summary'].lower()

    def test_summary_ends_with_period(self):
        r = parse_metar("KLAX 031552Z 27003KT 10SM SKC 22/08 A2998")
        assert r['summary'].endswith('.')


# ── Flask Route Tests ─────────────────────────────────────────────────────────

class TestFlaskRoutes:
    def test_get_returns_200(self, client):
        resp = client.get('/')
        assert resp.status_code == 200

    def test_get_shows_search_form(self, client):
        resp = client.get('/')
        assert b'name="airport"' in resp.data

    def test_post_empty_airport_shows_error(self, client):
        resp = client.post('/', data={'airport': ''})
        assert b'Please enter an airport code' in resp.data

    def test_post_whitespace_airport_shows_error(self, client):
        resp = client.post('/', data={'airport': '   '})
        assert b'Please enter an airport code' in resp.data

    def test_post_valid_metar_shows_station(self, client):
        with patch('app.requests.get', return_value=_mock_api(
            "KLAX 031552Z 27003KT 10SM SKC 22/08 A2998"
        )):
            resp = client.post('/', data={'airport': 'KLAX'})
        assert resp.status_code == 200
        assert b'KLAX' in resp.data

    def test_post_airport_input_lowercased_is_uppercased(self, client):
        """Input 'klax' must be uppercased to 'KLAX' before the API call."""
        with patch('app.requests.get', return_value=_mock_api(
            "KLAX 031552Z 27003KT 10SM SKC 22/08 A2998"
        )) as mock_get:
            client.post('/', data={'airport': 'klax'})
        _, kwargs = mock_get.call_args
        assert kwargs['params']['ids'] == 'KLAX'

    def test_post_empty_api_response_shows_error(self, client):
        with patch('app.requests.get', return_value=_mock_api('', status=200)):
            resp = client.post('/', data={'airport': 'ZZZZ'})
        assert b'No METAR data found' in resp.data

    def test_post_api_non_200_shows_error(self, client):
        with patch('app.requests.get', return_value=_mock_api('', status=404)):
            resp = client.post('/', data={'airport': 'XXXX'})
        assert b'No METAR data found' in resp.data

    def test_post_network_error_shows_error(self, client):
        with patch('app.requests.get', side_effect=req_module.RequestException):
            resp = client.post('/', data={'airport': 'KJFK'})
        assert b'Unable to connect' in resp.data

    def test_post_unparseable_api_response_shows_error(self, client):
        """API returns 200 but the text doesn't decode to a valid METAR station."""
        with patch('app.requests.get', return_value=_mock_api('No data found')):
            resp = client.post('/', data={'airport': 'ZZZZ'})
        assert b'No METAR data found' in resp.data

    def test_post_shows_weather_details(self, client):
        """A successful POST should render temperature and wind details."""
        with patch('app.requests.get', return_value=_mock_api(
            "KJFK 031552Z 05012G22KT 2SM +TSRA BKN008 OVC020 18/16 A2985"
        )):
            resp = client.post('/', data={'airport': 'KJFK'})
        assert b'\xc2\xb0F' in resp.data  # °F in UTF-8
        assert b'gusting' in resp.data
