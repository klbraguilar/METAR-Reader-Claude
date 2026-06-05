from metar_parser import parse_metar

tests = [
    "KJFK 031552Z 05012G22KT 2SM +TSRA BKN008 OVC020 18/16 A2985",
    "KLAX 031552Z 27003KT 10SM SKC 22/08 A2998",
    "KORD 031552Z VRB05KT 1/4SM FG OVC002 M02/M04 A3010",
    "KMCI 031552Z 22005KT 10SM FEW250 27/14 A2998",
]

for t in tests:
    r = parse_metar(t)
    print(r["station"] + ": " + r["summary"])
    for label, key in [("  Wind", "wind"), ("  Visibility", "visibility"),
                       ("  Sky", "sky"), ("  Weather", "weather"),
                       ("  Temp", "temperature")]:
        val = r[key]
        if val:
            print(label + ": " + (", ".join(val) if isinstance(val, list) else val))
    print()
