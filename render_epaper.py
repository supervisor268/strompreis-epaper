#!/usr/bin/env python3
"""Rendert die Ostrom-Wochenprognose als 800x480 1-Bit-PNG fuer 7,5" Mono-E-Ink.

Aufruf: python3 render_epaper.py daten.json ausgabe.png
JSON: {"kw": 47, "start": "2026-11-16", "preise": [..7 Werte oder null..],
       "geschaetzt": [bool x7], "avg": 31.2, "avg_vorwoche": 33.0,
       "stand": "16.11.2026"}
"""
import json, sys, datetime as dt
from PIL import Image, ImageDraw, ImageFont

W, H = 800, 480
F = "/usr/share/fonts/truetype/dejavu/DejaVuSans{}.ttf"
def font(size, bold=False):
    return ImageFont.truetype(F.format("-Bold" if bold else ""), size)

TAGE = ["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"]

def dashed_hline(d, x0, x1, y, dash=8, gap=6, width=2):
    x = x0
    while x < x1:
        d.line([(x, y), (min(x + dash, x1), y)], fill=0, width=width)
        x += dash + gap

def dashed_line(d, p0, p1, dash=8, gap=6, width=3):
    (x0, y0), (x1, y1) = p0, p1
    length = ((x1 - x0) ** 2 + (y1 - y0) ** 2) ** 0.5
    n = max(1, int(length // (dash + gap)))
    for i in range(n + 1):
        t0 = i * (dash + gap) / length
        t1 = min(1, (i * (dash + gap) + dash) / length)
        if t0 >= 1: break
        d.line([(x0 + (x1 - x0) * t0, y0 + (y1 - y0) * t0),
                (x0 + (x1 - x0) * t1, y0 + (y1 - y0) * t1)], fill=0, width=width)

def fmt(v):
    return f"{v:.1f}".replace(".", ",")

def render(data, out):
    img = Image.new("1", (W, H), 1)
    d = ImageDraw.Draw(img)
    d.fontmode = "1"  # keine Kantenglaettung -> sauberes 1-Bit

    start = dt.date.fromisoformat(data["start"])
    ende = start + dt.timedelta(days=6)
    preise = data["preise"]
    gesch = data.get("geschaetzt", [False] * 7)

    # Kopfzeile (schwarzer Balken, weisse Schrift)
    d.rectangle([0, 0, W, 56], fill=0)
    d.text((20, 10), f"Strompreis KW {data['kw']}", font=font(30, True), fill=1)
    d.text((W - 20, 18), f"{start:%d.%m.} – {ende:%d.%m.%Y}", font=font(22), fill=1, anchor="ra")

    # Kennzahlen
    avg, vor = data.get("avg"), data.get("avg_vorwoche")
    y = 70
    if avg is not None:
        d.text((20, y), "Ø Woche", font=font(18), fill=0)
        d.text((20, y + 22), f"{fmt(avg)} ct", font=font(34, True), fill=0)
    if vor is not None:
        d.text((230, y), "Ø Vorwoche", font=font(18), fill=0)
        d.text((230, y + 22), f"{fmt(vor)} ct", font=font(34, True), fill=0)
        if avg is not None:
            diff = avg - vor
            pfeil = "▼" if diff < 0 else ("▲" if diff > 0 else "=")
            d.text((440, y + 26), f"{pfeil} {fmt(abs(diff))} ct", font=font(26, True), fill=0)

    gueltig = [(i, p) for i, p in enumerate(preise) if p is not None]
    imin = min(gueltig, key=lambda t: t[1])[0]
    imax = max(gueltig, key=lambda t: t[1])[0]
    d.text((W - 20, y), f"günstig: {TAGE[imin]} {fmt(preise[imin])}", font=font(18, True), fill=0, anchor="ra")
    d.text((W - 20, y + 28), f"teuer: {TAGE[imax]} {fmt(preise[imax])}", font=font(18), fill=0, anchor="ra")

    # Diagrammbereich
    L, R, T, B = 70, W - 30, 158, H - 78
    vals = [p for _, p in gueltig] + [v for v in (avg, vor) if v is not None]
    lo, hi = min(vals), max(vals)
    pad = max(1.0, (hi - lo) * 0.25)
    lo, hi = lo - pad, hi + pad
    sy = lambda v: B - (v - lo) / (hi - lo) * (B - T)
    sx = lambda i: L + 30 + i * (R - L - 60) / 6

    # Y-Achse mit 3-4 Ticks
    step = max(1, round((hi - lo) / 4))
    t = int(lo) + 1
    while t < hi:
        yy = sy(t)
        d.line([(L - 6, yy), (L, yy)], fill=0, width=2)
        d.text((L - 10, yy), str(t), font=font(16), fill=0, anchor="rm")
        for x in range(L, R, 12):
            d.point((x, yy), fill=0)
        t += step
    d.line([(L, T), (L, B)], fill=0, width=2)
    d.line([(L, B), (R, B)], fill=0, width=2)
    d.text((L + 6, T - 2), "ct/kWh", font=font(14), fill=0, anchor="lb")

    # Durchschnittslinie
    if avg is not None:
        dashed_hline(d, L, R, sy(avg), width=2)
        d.text((R, sy(avg) - 4), "Ø", font=font(16, True), fill=0, anchor="rb")

    # Preislinie
    pts = [(sx(i), sy(p)) for i, p in gueltig]
    for k in range(len(pts) - 1):
        i_a, i_b = gueltig[k][0], gueltig[k + 1][0]
        if gesch[i_a] or gesch[i_b]:
            dashed_line(d, pts[k], pts[k + 1], width=4)
        else:
            d.line([pts[k], pts[k + 1]], fill=0, width=4)

    # Punkte + Wertbeschriftung + X-Achse
    for i in range(7):
        x = sx(i)
        datum = start + dt.timedelta(days=i)
        lbl_font = font(20, True) if i in (imin, imax) else font(20)
        d.text((x, B + 8), TAGE[i], font=lbl_font, fill=0, anchor="ma")
        d.text((x, B + 32), f"{datum:%d.%m.}", font=font(14), fill=0, anchor="ma")
        p = preise[i]
        if p is None:
            continue
        y0 = sy(p)
        r = 9 if i in (imin, imax) else 6
        if gesch[i]:
            d.ellipse([x - r, y0 - r, x + r, y0 + r], fill=1, outline=0, width=3)
        else:
            d.ellipse([x - r, y0 - r, x + r, y0 + r], fill=0)
        if i == imin:   # Minimum: Kasten um den Wert, unterhalb
            txt = fmt(p)
            bb = d.textbbox((x, y0 + 16), txt, font=font(20, True), anchor="ma")
            d.rectangle([bb[0] - 5, bb[1] - 3, bb[2] + 5, bb[3] + 3], fill=0)
            d.text((x, y0 + 16), txt, font=font(20, True), fill=1, anchor="ma")
        else:
            f_ = font(20, True) if i == imax else font(18)
            d.text((x, y0 - 14), fmt(p), font=f_, fill=0, anchor="mb")

    stand = data.get("stand", dt.date.today().strftime("%d.%m.%Y"))
    d.text((W - 10, H - 4), f"Quelle: Ostrom-Prognose · Stand {stand}", font=font(12), fill=0, anchor="rb")
    img.save(out, optimize=True)

if __name__ == "__main__":
    render(json.load(open(sys.argv[1])), sys.argv[2])
