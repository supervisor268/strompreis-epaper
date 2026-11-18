# strompreis-epaper

Wöchentliche Ostrom-Strompreisprognose als 800×480 1-Bit-PNG für ein 7,5"-Mono-E-Ink (XIAO ePaper Display Board EE04) über SenseCraft HMI.

- Bild-URL für SenseCraft (Image-Widget): `https://raw.githubusercontent.com/supervisor268/strompreis-epaper/main/epaper.png`
- `data/latest.json`: Eingabedaten der aktuellen Woche
- `render_epaper.py`: `python3 render_epaper.py data/latest.json epaper.png`

Wird sonntags/montags von einer Claude-Wochenaufgabe aktualisiert.
