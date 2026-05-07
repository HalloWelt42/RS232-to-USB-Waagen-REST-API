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

# VERSION aktualisieren
echo "$NEW" > VERSION

# package.json mit Python sauber rewriten (kein npm-Aufruf nötig)
python3 - <<PY
import json, pathlib
p = pathlib.Path("frontend/package.json")
data = json.loads(p.read_text())
data["version"] = "$NEW"
p.write_text(json.dumps(data, indent=2) + "\n")
PY

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

git add VERSION frontend/package.json CHANGELOG.md
git commit -m "chore(release): bump auf $NEW"
git tag -a "v$NEW" -m "Release $NEW"

echo
echo "Fertig. Commit + Tag v$NEW liegen lokal."
echo "Pushen mit:"
echo "  git push && git push --tags"
