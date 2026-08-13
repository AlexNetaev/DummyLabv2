"""Merges temperature and fluorescence measurements into a single CSV."""
import csv
from pathlib import Path
from typing import List, Tuple

from .csv_writer import write_csv_atomic


def _linear_interpolate(x: int, points: List[Tuple[int, float]]) -> float:
    """
    Führt lineare Interpolation für einen x-Wert basierend auf einer Liste von (x, y)-Punkten durch.
    Punkte müssen nach x sortiert sein.
    Bei Werten außerhalb des Bereichs wird der nächste Randwert verwendet (clamp).
    """
    if not points:
        raise ValueError("Keine Punkte zur Interpolation verfügbar.")
    
    # Sortieren sicherstellen
    points_sorted = sorted(points, key=lambda p: p[0])
    
    # Edge Cases: Vor dem ersten Punkt
    if x <= points_sorted[0][0]:
        return points_sorted[0][1]
    
    # Edge Cases: Nach dem letzten Punkt
    if x >= points_sorted[-1][0]:
        return points_sorted[-1][1]
    
    # Suche das Intervall
    for i in range(len(points_sorted) - 1):
        x0, y0 = points_sorted[i]
        x1, y1 = points_sorted[i + 1]
        
        if x0 <= x <= x1:
            # Vermeide Division durch Null (obwohl durch Sortierung und Checks unwahrscheinlich)
            if x1 == x0:
                return y0
            # Lineare Interpolation
            ratio = (x - x0) / (x1 - x0)
            return y0 + ratio * (y1 - y0)
    
    # Sollte nicht erreicht werden
    return points_sorted[-1][1]


def merge_measurements(output_dir: Path) -> int:
    """
    Liest station3_temperature.csv und station4_fluorescence.csv.
    Interpoliert Temperaturwerte auf die Zeitachse der Fluoreszenzdaten.
    Schreibt das Ergebnis als measurement.csv.
    
    Gibt die Anzahl der geschriebenen Zeilen zurück.
    Wirft FileNotFoundError, wenn eine der Quelldateien fehlt.
    """
    temp_file = output_dir / "station3_temperature.csv"
    fluo_file = output_dir / "station4_fluorescence.csv"
    out_file = output_dir / "measurement.csv"
    
    if not temp_file.exists():
        raise FileNotFoundError(f"Temperaturdatei nicht gefunden: {temp_file}")
    if not fluo_file.exists():
        raise FileNotFoundError(f"Fluoreszenzdatei nicht gefunden: {fluo_file}")
    
    # Temperaturdaten lesen
    temp_points: List[Tuple[int, float]] = []
    with open(temp_file, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            t_ms = int(row["time_ms"])
            t_val = float(row["temp_c"])
            temp_points.append((t_ms, t_val))
    
    # Fluoreszenzdaten lesen (Master-Achse)
    fluo_points: List[Tuple[int, float]] = []
    with open(fluo_file, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            t_ms = int(row["time_ms"])
            f_val = float(row["fluorescence_raw_au"])
            fluo_points.append((t_ms, f_val))
    
    if not fluo_points:
        # Wenn keine Fluoreszenzdaten da sind, schreiben wir eine leere Datei mit Header
        write_csv_atomic(out_file, ["time_ms", "temp_c", "fluorescence_raw_au"], [])
        return 0
    
    # Merge durchführen
    merged_rows = []
    for t_ms, f_val in fluo_points:
        # Temperatur interpolieren
        t_val = _linear_interpolate(t_ms, temp_points)
        merged_rows.append([t_ms, round(t_val, 3), round(f_val, 3)])
    
    # Schreiben
    write_csv_atomic(out_file, ["time_ms", "temp_c", "fluorescence_raw_au"], merged_rows)
    
    return len(merged_rows)
