# Mockups — historischer Snapshot

> **Achtung:** dieses Verzeichnis enthält einen archivierten visuellen
> Stand der App aus der **v0.3-Iteration (Mai 2026)** und wird **nicht**
> mit der App weiterentwickelt. Die dort angezeigten Versionsstrings
> („v0.3.0") sind absichtlich eingefroren als Snapshot-Marker.
>
> Aktuelle Version: siehe Datei [`VERSION`](../VERSION) im Repo-Wurzel
> bzw. `GET /scale/health → "version"` am laufenden Backend.

## Zweck

Die Datei `index.html` zeigt nebeneinander Dunkel- und Hell-Modus, alle
Tool-Panels, das Spende-Layout und die mobile Variante in dem Stil, der
mit v0.3 etabliert wurde — Industrial-Look mit Petrol-Akzent.

Sie diente damals zur Abstimmung mit dem Anwender vor der Implementierung
und ist seither dokumentarisch im Repo, weil der Aufwand, einen aktuellen
Mockup-Stand zu pflegen, sich neben der echten Live-App nicht lohnt.

## Wenn Sie aktuelle Screenshots brauchen

Den Live-Build benutzen — er ist bereits voll-fluessig:

```bash
# Backend
cd backend && .venv/bin/python -m waage.api &

# Frontend (Dev-Server mit HMR)
cd frontend && npm run dev
# → http://localhost:5184
```

Statisches HTML der echten App liefert `npm run build` nach
`frontend/dist/`.

## Warum nicht löschen?

Die History bleibt im Git natürlich erhalten; die Datei zu behalten ist
billig (~80 KB) und stiftet, mit dem Banner und diesem README, klar
keinen Verwirrungs-Schaden mehr. Wer in einem halben Jahr verstehen
will, woher das aktuelle Design kommt, hat hier eine direkt aufrufbare
Referenz.
