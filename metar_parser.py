import re

COMPASS = [
    'North', 'North-Northeast', 'Northeast', 'East-Northeast',
    'East', 'East-Southeast', 'Southeast', 'South-Southeast',
    'South', 'South-Southwest', 'Southwest', 'West-Southwest',
    'West', 'West-Northwest', 'Northwest', 'North-Northwest',
]

WX_CODES = {
    'DZ': 'drizzle', 'RA': 'rain', 'SN': 'snow', 'SG': 'snow grains',
    'IC': 'ice crystals', 'PL': 'ice pellets', 'GR': 'hail',
    'GS': 'small hail', 'UP': 'unknown precipitation',
    'BR': 'mist', 'FG': 'fog', 'FU': 'smoke', 'VA': 'volcanic ash',
    'DU': 'dust', 'SA': 'sand', 'HZ': 'haze', 'PY': 'spray',
    'PO': 'dust whirls', 'SQ': 'squalls', 'FC': 'tornado/waterspout',
    'SS': 'sandstorm', 'DS': 'dust storm',
    'TS': 'thunderstorm', 'SH': 'shower', 'FZ': 'freezing',
    'MI': 'shallow', 'PR': 'partial', 'BC': 'patchy',
    'DR': 'drifting', 'BL': 'blowing',
}

SKY_COVERAGE = {
    'SKC': 'Clear skies',
    'CLR': 'Clear skies',
    'NSC': 'No significant clouds',
    'NCD': 'No clouds detected',
    'FEW': 'Few clouds',
    'SCT': 'Scattered clouds',
    'BKN': 'Broken cloud layer',
    'OVC': 'Overcast',
    'VV': 'Sky obscured',
}

_WX_ALL = {
    'DZ', 'RA', 'SN', 'SG', 'IC', 'PL', 'GR', 'GS', 'UP',
    'BR', 'FG', 'FU', 'VA', 'DU', 'SA', 'HZ', 'PY',
    'PO', 'SQ', 'FC', 'SS', 'DS',
    'TS', 'SH', 'FZ', 'MI', 'PR', 'BC', 'DR', 'BL',
}


def _degrees_to_compass(deg):
    return COMPASS[round(deg / 22.5) % 16]


def _c_to_f(c):
    return round(c * 9 / 5 + 32)


def _knots_to_mph(kt):
    return round(kt * 1.15078)


def _parse_temp(s):
    return -int(s[1:]) if s.startswith('M') else int(s)


def _is_wx_token(token):
    s = token
    if s.startswith(('+', '-')):
        s = s[1:]
    if s.startswith('VC'):
        s = s[2:]
    if not s or len(s) % 2 != 0:
        return False
    return all(s[j:j+2] in _WX_ALL for j in range(0, len(s), 2))


def _decode_wx(token):
    s = token
    parts = []
    if s.startswith('+'):
        parts.append('heavy')
        s = s[1:]
    elif s.startswith('-'):
        parts.append('light')
        s = s[1:]
    if s.startswith('VC'):
        parts.append('nearby')
        s = s[2:]
    for j in range(0, len(s), 2):
        parts.append(WX_CODES.get(s[j:j+2], s[j:j+2].lower()))
    return ' '.join(parts)


def parse_metar(raw):
    raw = raw.strip().split('\n')[0].strip()
    tokens = raw.split()
    n = len(tokens)
    i = 0

    d = dict(
        raw=raw, station='', time_utc='', wind='',
        visibility='', weather=[], sky=[], sky_raw=[],
        temperature='', dewpoint='', temp_c=None, temp_f=None,
        altimeter='', summary='',
    )

    if i < n and tokens[i] in ('METAR', 'SPECI'):
        i += 1

    if i < n and re.match(r'^[A-Z0-9]{4}$', tokens[i]):
        d['station'] = tokens[i]
        i += 1

    if i < n and re.match(r'^\d{6}Z$', tokens[i]):
        t = tokens[i]
        h, m = int(t[2:4]), int(t[4:6])
        d['time_utc'] = f'{h:02d}:{m:02d} UTC'
        i += 1

    if i < n and tokens[i] in ('AUTO', 'COR', 'RTD'):
        i += 1

    # Wind
    if i < n:
        wm = re.match(r'^(VRB|\d{3})(\d{2,3})(G(\d{2,3}))?(KT|MPS|KMH)$', tokens[i])
        if wm:
            dir_s, spd, gust_s, unit = wm.group(1), int(wm.group(2)), wm.group(4), wm.group(5)
            gust = int(gust_s) if gust_s else None

            if unit == 'KT':
                spd_mph = _knots_to_mph(spd)
                gust_mph = _knots_to_mph(gust) if gust else None
            elif unit == 'MPS':
                spd_mph = round(spd * 2.237)
                gust_mph = round(gust * 2.237) if gust else None
            else:
                spd_mph = round(spd * 0.621)
                gust_mph = round(gust * 0.621) if gust else None

            if spd == 0:
                d['wind'] = 'Calm'
            elif dir_s == 'VRB':
                d['wind'] = f'Variable direction at {spd_mph} mph'
            else:
                d['wind'] = f'From the {_degrees_to_compass(int(dir_s))} at {spd_mph} mph'

            if gust_mph:
                d['wind'] += f', gusting to {gust_mph} mph'

            i += 1
            if i < n and re.match(r'^\d{3}V\d{3}$', tokens[i]):
                i += 1

    # Visibility
    if i < n:
        tok = tokens[i]
        if tok == 'CAVOK':
            d['visibility'] = '10+ miles'
            i += 1
        elif re.match(r'^M?\d+(/\d+)?SM$', tok):
            less = tok.startswith('M')
            clean = tok.lstrip('M').replace('SM', '')
            if '/' in clean:
                num, den = clean.split('/')
                miles = int(num) / int(den)
            else:
                miles = float(clean)
            prefix = 'Less than ' if less else ''
            if miles >= 10:
                d['visibility'] = f'{prefix}10+ miles'
            elif miles == int(miles):
                d['visibility'] = f'{prefix}{int(miles)} miles'
            else:
                d['visibility'] = f'{prefix}{miles:.2f} miles'
            i += 1
        elif (re.match(r'^\d+$', tok) and i + 1 < n and
              re.match(r'^\d+/\d+SM$', tokens[i + 1])):
            whole = int(tok)
            frac = tokens[i + 1].replace('SM', '')
            num, den = frac.split('/')
            miles = whole + int(num) / int(den)
            d['visibility'] = f'{miles:.2f} miles'
            i += 2
        elif re.match(r'^\d{4}$', tok):
            vis_m = int(tok)
            d['visibility'] = '10+ km' if vis_m >= 9999 else f'{vis_m / 1000:.1f} km'
            i += 1

    # Remaining tokens
    while i < n and tokens[i] != 'RMK':
        tok = tokens[i]

        if tok in ('TEMPO', 'BECMG', 'NOSIG', 'PROB'):
            break

        if re.match(r'^R\d{2}[LRC]?/', tok):
            i += 1
            continue

        if _is_wx_token(tok):
            d['weather'].append(_decode_wx(tok))
            i += 1
            continue

        sky_m = re.match(r'^(SKC|CLR|NSC|NCD|FEW|SCT|BKN|OVC|VV)(\d{3})?(CB|TCU)?$', tok)
        if sky_m:
            cov, ht_s, ctype = sky_m.group(1), sky_m.group(2), sky_m.group(3)
            ht_ft = int(ht_s) * 100 if ht_s else None
            d['sky_raw'].append({'coverage': cov, 'height_ft': ht_ft})
            desc = SKY_COVERAGE.get(cov, cov)
            if ht_ft is not None:
                desc += f' at {ht_ft:,} ft'
            if ctype == 'CB':
                desc += ' (cumulonimbus — thunderstorm clouds)'
            elif ctype == 'TCU':
                desc += ' (towering cumulus)'
            d['sky'].append(desc)
            i += 1
            continue

        td_m = re.match(r'^(M?\d{2})/(M?\d{2})$', tok)
        if td_m:
            tc = _parse_temp(td_m.group(1))
            dc = _parse_temp(td_m.group(2))
            tf = _c_to_f(tc)
            df = _c_to_f(dc)
            d['temp_c'], d['temp_f'] = tc, tf
            d['temperature'] = f'{tf}°F ({tc}°C)'
            d['dewpoint'] = f'{df}°F ({dc}°C)'
            i += 1
            continue

        alt_m = re.match(r'^(A|Q)(\d{4})$', tok)
        if alt_m:
            atype, aval = alt_m.group(1), int(alt_m.group(2))
            d['altimeter'] = f'{aval / 100:.2f} inHg' if atype == 'A' else f'{aval} hPa'
            i += 1
            continue

        i += 1

    d['summary'] = _build_summary(d)
    return d


def _build_summary(d):
    parts = []

    if d['weather']:
        parts.append(' and '.join(d['weather']).capitalize())
    elif d['sky_raw']:
        cov = d['sky_raw'][0]['coverage']
        label = {
            'SKC': 'Clear', 'CLR': 'Clear', 'NSC': 'Clear', 'NCD': 'Clear',
            'FEW': 'Mostly clear', 'SCT': 'Partly cloudy',
            'BKN': 'Mostly cloudy', 'OVC': 'Overcast', 'VV': 'Sky obscured',
        }.get(cov, 'Cloudy')
        parts.append(label)
    else:
        parts.append('Clear')

    if d['temp_f'] is not None:
        parts.append(f"{d['temp_f']}°F")

    if d['wind']:
        parts.append('calm winds' if d['wind'] == 'Calm' else d['wind'].lower())

    if d['visibility'] and '10+' not in d['visibility']:
        parts.append(f"visibility {d['visibility'].lower()}")

    return ', '.join(parts) + '.'
