#!/usr/bin/env bash
#
# Versions-Bump-Skript: erhöht VERSION, package.json und legt einen Git-Tag an.
#
#   ./scripts/bump.sh patch    # 0.2.0 -> 0.2.1
#   ./scripts/bump.sh minor    # 0.2.1 -> 0.3.0
#   ./scripts/bump.sh major    # 0.3.0 -> 1.0.0
#   ./scripts/bump.sh 1.2.3    # explizit auf 1.2.3 setzen
#
# Erfordert sauberes Working-Directory (außer den editierten Dateien selbst)
# und schreibt einen annotierten Tag v<version>. Der Push muss separat
# erfolgen — dieses Skript pushed bewusst nicht selbst.

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if [[ $# -ne 1 ]]; then
  echo "Aufruf: $0 [patch|minor|major|<x.y.z>]" >&2
  exit 1
fi

ARG="$1"
CURRENT="$(cat VERSION)"

# Prüfung: Working Directory sauber?
if [[ -n "$(git status --porcelain)" ]]; then
  echo "Fehler: Working Directory ist nicht sauber." >&2
  echo "Bitte vorher committen oder stashen." >&2
  git status --short >&2
  exit 1
fi

# Neue Version errechnen
case "$ARG" in
  patch|minor|major)
    IFS='.' read -r MAJOR MINOR PATCH <<< "$CURRENT"
    case "$ARG" in
      patch) PATCH=$((PATCH + 1)) ;;
      minor) MINOR=$((MINOR + 1)); PATCH=0 ;;
      major) MAJOR=$((MAJOR + 1)); MINOR=0; PATCH=0 ;;
    esac
    NEW="${MAJOR}.${MINOR}.${PATCH}"
    ;;
  [0-9]*.[0-9]*.[0-9]*)
    NEW="$ARG"
    ;;
  *)
    echo "Fehler: Argument muss patch|minor|major oder x.y.z sein." >&2
    exit 1
    ;;
esac

echo "Bump:  $CURRENT  ->  $NEW"

# VERSION an beiden Stellen aktualisieren — keine Symlinks.
# - Repo-Wurzel: VERSION (Single Source of Truth, von Vite + bump gelesen)
# - backend/VERSION: kopierte Datei für setuptools dynamic version
#   (setuptools liest nur Pfade innerhalb der Paket-Wurzel)
echo "$NEW" > VERSION
echo "$NEW" > backend/VERSION

# package.json mit Python sauber rewriten (kein npm-Aufruf nötig)
python3 - <<PY
import json, pathlib
p = pathlib.Path("frontend/package.json")
data = json.loads(p.read_text())
data["version"] = "$NEW"
p.write_text(json.dumps(data, indent=2) + "\n")
PY

# frontend/public/version.json — wird vom Footer beim Page-Load mit
# Cache-Buster gefetcht und ist daher IMMER aktuell, ohne dass das
# Frontend-Bundle neu gebaut werden muss. Vite-Dev-Server serviert
# das aus public/ direkt; bei `npm run build` landet es 1:1 in dist/.
python3 - <<PY
import json, pathlib, datetime
p = pathlib.Path("frontend/public/version.json")
p.parent.mkdir(parents=True, exist_ok=True)
p.write_text(json.dumps({
    "version": "$NEW",
    "bumped_at": datetime.datetime.now().isoformat(timespec="seconds"),
}, indent=2) + "\n")
PY

# Frontend-Bundle automatisch neu bauen, damit auch die zur Build-Zeit
# eingefrorene `__APP_VERSION__`-Konstante den aktuellen Wert hat.
# Falls npm nicht da ist (z.B. auf einem reinen Backend-Host), wird
# der Build übersprungen — der Bump läuft trotzdem durch, der nächste
# manuelle `npm run build` zieht den Stand dann nach.
if command -v npm >/dev/null 2>&1 && [[ -d frontend/node_modules ]]; then
  echo "Frontend-Build …"
  if (cd frontend && npm run build --silent 2>&1 | tail -5); then
    echo "  ok"
  else
    echo "  WARNUNG: Frontend-Build fehlgeschlagen — manuell prüfen." >&2
  fi
else
  echo "Frontend-Build übersprungen (kein npm bzw. keine node_modules)."
fi

# CHANGELOG-Eintrag-Vorlage anlegen (sofern oben noch keiner existiert)
if ! grep -q "^## \[$NEW\]" CHANGELOG.md; then
  TODAY="$(date +%F)"
  TMP="$(mktemp)"
  awk -v ver="$NEW" -v date="$TODAY" '
    NR == 1 { print; next }
    !done && /^## \[/ {
      print "## [" ver "] — " date "\n\n### Hinweise\n- (bitte ergänzen)\n"
      done = 1
    }
    { print }
  ' CHANGELOG.md > "$TMP"
  mv "$TMP" CHANGELOG.md
  echo "CHANGELOG.md: Vorlage für $NEW eingefügt — bitte ergänzen."
fi

git add VERSION backend/VERSION frontend/package.json frontend/public/version.json CHANGELOG.md
git commit -m "chore(release): bump auf $NEW"
git tag -a "v$NEW" -m "Release $NEW"

echo
echo "Fertig. Commit + Tag v$NEW liegen lokal."
echo "Pushen mit:"
echo "  git push && git push --tags"
