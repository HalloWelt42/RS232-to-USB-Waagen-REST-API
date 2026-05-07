"""Bekannte Waagen-Modelle.

Diese Liste dient als Auswahl beim Ersteinrichten. Bilder fehlen
absichtlich (Markenrechte). Quellen sind die offiziellen G&G-
Bedienungsanleitungen und die G&G-Modellübersicht.

Die Werte sind Richtwerte für die jeweilige Baureihe — einzelne
Modelle innerhalb einer Baureihe variieren in Maximallast und
Ablesbarkeit. Falls das eigene Modell nicht direkt aufgeführt ist,
nimmt der Anwender die nächstpassende Baureihe oder das ``custom``-
Modell mit eigenen Werten.

Alle aufgeführten Modelle nutzen das gleiche RS232-Protokoll laut
„Anleitung Datenschnittstelle" (gandg.de): 9600 Baud 8N1, ESC p als
Print-Befehl, optionales Stream-Mode bei Geräten ab Baujahr 2025.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ScaleModel:
    """Beschreibung einer Waagen-Baureihe oder eines konkreten Modells."""

    id: str
    """Eindeutige ID (z.B. ``gg.plc.6000``). Stabil über Versionen hinweg."""

    manufacturer: str
    """Herstellername."""

    series: str
    """Baureihen-Bezeichnung (z.B. ``PLC``, ``JJ-B``, ``TJ-Y``)."""

    name: str
    """Anzeige-Name in der UI (z.B. ``PLC-6000 (6000 g / 0,1 g)``)."""

    category: str
    """Kategorie: precision, analytical, bench, counting, kitchen, fine,
    platform, custom."""

    max_g: float
    """Maximalkapazität in Gramm."""

    resolution_g: float
    """Ablesbarkeit in Gramm (kleinster Schritt)."""

    default_baudrate: int = 9600
    """Werkseinstellung der Baudrate."""

    rs232: bool = True
    """RS232-Schnittstelle ab Werk vorhanden?"""

    note: str = ""
    """Optionaler Zusatzhinweis (z.B. Stream-Mode, Besonderheiten)."""

    # ----- Genauigkeits-Toleranzen aus dem Datenblatt --------------------
    # Diese Werte stammen aus den G&G-Datenblättern und sind hilfreich,
    # damit die App den Anwender warnen kann, bevor er Mess-Reihen
    # außerhalb des Spezifikationsbereichs aufnimmt.

    min_load_g: float = 0.0
    """Empfohlene Mindest-Auflage. Werte unter diesem Schwellwert sind
    laut Hersteller nicht spezifiziert; viele Waagen zeigen unterhalb
    dieser Last keine reproduzierbaren Werte. 0 bedeutet „nicht
    angegeben — keine Warnung erzeugen"."""

    linearity_g: float = 0.0
    """Maximale Linearitäts-Abweichung über den ganzen Wägebereich
    (typisch ±n×Ablesbarkeit). 0 = nicht angegeben."""

    repeatability_g: float = 0.0
    """Standardabweichung der Wiederholmessungen (typisch =
    Ablesbarkeit). 0 = nicht angegeben."""

    stabilization_s: float = 0.0
    """Typische Beruhigungszeit nach Auflage in Sekunden. 0 = nicht
    angegeben."""

    warmup_min: int = 0
    """Empfohlene Aufwärmzeit nach dem Einschalten in Minuten,
    bevor genau gewogen wird. 0 = nicht angegeben."""

    operating_temp_c: tuple[float, float] | None = None
    """Erlaubter Betriebstemperatur-Bereich in °C, z.B. (10, 30).
    None = nicht angegeben."""


# Bekannte Modelle, von feiner zu gröber, sortiert nach Baureihe.
KNOWN_MODELS: tuple[ScaleModel, ...] = (
    # ---- Analyse-/Feinwaagen ------------------------------------------
    ScaleModel(
        id="gg.jjb.220",
        manufacturer="G&G",
        series="JJ-B",
        name="JJ-B 220 (220 g / 0,001 g)",
        category="analytical",
        max_g=220.0,
        resolution_g=0.001,
        note="Analysewaage; Ablesbarkeit je nach konkretem Modell 0,01-0,001 g",
        min_load_g=0.02,             # 20 mg laut Datenblatt
        linearity_g=0.002,
        repeatability_g=0.001,
        stabilization_s=4.0,
        warmup_min=60,
        operating_temp_c=(10.0, 30.0),
    ),
    ScaleModel(
        id="gg.jjbc.224",
        manufacturer="G&G",
        series="JJ-BC",
        name="JJ-BC 224 (220 g / 0,1 mg)",
        category="analytical",
        max_g=220.0,
        resolution_g=0.0001,
        note="Hochpräzise Analysewaage mit Kraftkompensation",
        min_load_g=0.01,             # 10 mg
        linearity_g=0.0002,
        repeatability_g=0.0001,
        stabilization_s=5.0,
        warmup_min=60,
        operating_temp_c=(15.0, 25.0),
    ),
    ScaleModel(
        id="gg.jjbf.220",
        manufacturer="G&G",
        series="JJ-BF",
        name="JJ-BF 220 (220 g / 0,1 mg)",
        category="analytical",
        max_g=220.0,
        resolution_g=0.0001,
    ),

    # ---- Präzisionswaagen PLC -----------------------------------------
    ScaleModel(
        id="gg.plc.300",
        manufacturer="G&G",
        series="PLC",
        name="PLC-300 (300 g / 0,01 g)",
        category="precision",
        max_g=300.0,
        resolution_g=0.01,
    ),
    ScaleModel(
        id="gg.plc.600",
        manufacturer="G&G",
        series="PLC",
        name="PLC-600 (600 g / 0,01 g)",
        category="precision",
        max_g=600.0,
        resolution_g=0.01,
    ),
    ScaleModel(
        id="gg.plc.1200",
        manufacturer="G&G",
        series="PLC",
        name="PLC-1200 (1200 g / 0,01 g)",
        category="precision",
        max_g=1200.0,
        resolution_g=0.01,
    ),
    ScaleModel(
        id="gg.plc.3000",
        manufacturer="G&G",
        series="PLC",
        name="PLC-3000 (3000 g / 0,1 g)",
        category="precision",
        max_g=3000.0,
        resolution_g=0.1,
    ),
    ScaleModel(
        id="gg.plc.6000",
        manufacturer="G&G",
        series="PLC",
        name="PLC-6000 (6000 g / 0,1 g)",
        category="precision",
        max_g=6000.0,
        resolution_g=0.1,
        note="Standard-Tischwaage, weit verbreitet",
        min_load_g=5.0,              # 50× Ablesbarkeit, Datenblatt G&G PLC
        linearity_g=0.2,
        repeatability_g=0.1,
        stabilization_s=3.0,
        warmup_min=30,
        operating_temp_c=(10.0, 30.0),
    ),
    ScaleModel(
        id="gg.plc.30000",
        manufacturer="G&G",
        series="PLC",
        name="PLC-30000 (30000 g / 1 g)",
        category="precision",
        max_g=30000.0,
        resolution_g=1.0,
    ),

    # ---- Tischwaagen E/EY/T/TY ----------------------------------------
    ScaleModel(
        id="gg.ey.300",
        manufacturer="G&G",
        series="EY",
        name="EY-300 (300 g / 0,01 g)",
        category="bench",
        max_g=300.0,
        resolution_g=0.01,
    ),
    ScaleModel(
        id="gg.ey.6000",
        manufacturer="G&G",
        series="EY",
        name="EY-6000 (6000 g / 0,1 g)",
        category="bench",
        max_g=6000.0,
        resolution_g=0.1,
    ),
    ScaleModel(
        id="gg.t.6000",
        manufacturer="G&G",
        series="T",
        name="T-6000 (6000 g / 0,1 g)",
        category="bench",
        max_g=6000.0,
        resolution_g=0.1,
    ),

    # ---- Zählwaagen TJ / TJ-Y / DJ-KC ---------------------------------
    ScaleModel(
        id="gg.tjy.6000",
        manufacturer="G&G",
        series="TJ-Y",
        name="TJ-Y 6000 (6000 g / 0,1 g, Zählwaage)",
        category="counting",
        max_g=6000.0,
        resolution_g=0.1,
        note="Drei-Display-Zählwaage; Frame mit WT/UW/QT-Blöcken",
    ),
    ScaleModel(
        id="gg.tjy.30000",
        manufacturer="G&G",
        series="TJ-Y",
        name="TJ-Y 30 (30 kg / 1 g, Zählwaage)",
        category="counting",
        max_g=30000.0,
        resolution_g=1.0,
        note="Zählwaage mit drei Displays",
    ),
    ScaleModel(
        id="gg.djkc.30000",
        manufacturer="G&G",
        series="DJ-KC",
        name="DJ-KC 30 (30 kg / 1 g, Zählwaage)",
        category="counting",
        max_g=30000.0,
        resolution_g=1.0,
        note="Drei-Display-Zählwaage, Frame mit WT/UW/QT-Blöcken",
    ),

    # ---- Plattformwaagen ----------------------------------------------
    ScaleModel(
        id="gg.djkl.30000",
        manufacturer="G&G",
        series="DJ-KL",
        name="DJ-KL 30 (30 kg / 1 g)",
        category="platform",
        max_g=30000.0,
        resolution_g=1.0,
    ),
    ScaleModel(
        id="gg.djsa.6000",
        manufacturer="G&G",
        series="DJ-SA",
        name="DJ-SA (6000 g / 0,1 g)",
        category="platform",
        max_g=6000.0,
        resolution_g=0.1,
    ),
    ScaleModel(
        id="gg.tckl.150kg",
        manufacturer="G&G",
        series="TC-KL",
        name="TC-KL (150 kg / 10 g)",
        category="platform",
        max_g=150_000.0,
        resolution_g=10.0,
    ),
    ScaleModel(
        id="gg.pse.300kg",
        manufacturer="G&G",
        series="PSE",
        name="PSE (300 kg / 100 g)",
        category="platform",
        max_g=300_000.0,
        resolution_g=100.0,
    ),

    # ---- Generisch (Fallback) -----------------------------------------
    ScaleModel(
        id="custom",
        manufacturer="—",
        series="—",
        name="Andere/Eigene Werte",
        category="custom",
        max_g=6000.0,
        resolution_g=0.1,
        note="Setzen Sie Maximallast und Ablesbarkeit selbst",
    ),
)


def find_model(model_id: str) -> ScaleModel | None:
    for m in KNOWN_MODELS:
        if m.id == model_id:
            return m
    return None


# Standard-Modell, wenn nichts konfiguriert ist
DEFAULT_MODEL_ID = "gg.plc.6000"
