#!/usr/bin/env bash
set -euo pipefail

APP_HOME="${ASHEN_VOICE_HOME:-$HOME/.local/share/ashen-voice-studio}"
VENV="$APP_HOME/venv"
BOOTSTRAP_VENV="$APP_HOME/bootstrap"
PIPER_DIR="$APP_HOME/piper"
LUX_DIR="$APP_HOME/LuxTTS"
WITH_LUX=0

for arg in "$@"; do
  case "$arg" in
    --with-lux) WITH_LUX=1 ;;
    *) echo "Unknown option: $arg" >&2; exit 2 ;;
  esac
done

mkdir -p "$APP_HOME" "$PIPER_DIR"

if ! command -v python3 >/dev/null 2>&1; then
  echo "python3 is required." >&2
  exit 1
fi

# KittenTTS 0.8.1 depends on misaki 0.9.4, which only supports Python < 3.13.
# Ubuntu 26.04 ships a newer Python, so install an isolated Python 3.12 in user space
# with uv when the system interpreter is too new. No sudo or system Python changes.
SYSTEM_PY="$(command -v python3)"
SYSTEM_VER="$($SYSTEM_PY -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')"

if "$SYSTEM_PY" -c 'import sys; raise SystemExit(0 if (3,8) <= sys.version_info[:2] < (3,13) else 1)'; then
  ENGINE_PY="$SYSTEM_PY"
  echo "Using system Python $SYSTEM_VER for native voice engines."
else
  echo "System Python $SYSTEM_VER is too new for KittenTTS/misaki."
  echo "Installing isolated Python 3.12 for Ashen Voice Studio only..."

  if [ ! -x "$BOOTSTRAP_VENV/bin/python" ]; then
    "$SYSTEM_PY" -m venv "$BOOTSTRAP_VENV"
  fi
  "$BOOTSTRAP_VENV/bin/python" -m pip install --upgrade pip uv
  UV="$BOOTSTRAP_VENV/bin/uv"
  "$UV" python install 3.12
  ENGINE_PY="$($UV python find 3.12)"
fi

# Replace a previously-created environment if it used Python 3.13+.
if [ -x "$VENV/bin/python" ]; then
  if ! "$VENV/bin/python" -c 'import sys; raise SystemExit(0 if (3,8) <= sys.version_info[:2] < (3,13) else 1)'; then
    echo "Replacing the incompatible Ashen voice environment..."
    rm -rf "$VENV"
  fi
fi

if [ ! -d "$VENV" ]; then
  echo "Creating Ashen Voice native-engine environment with $($ENGINE_PY --version)..."
  "$ENGINE_PY" -m venv "$VENV"
fi

PY="$VENV/bin/python"
PIP="$VENV/bin/pip"

"$PY" -m pip install --upgrade pip setuptools wheel

# KittenTTS 0.8.1. Its release metadata requires Python 3.8-3.12 because of misaki.
"$PIP" install "https://github.com/KittenML/KittenTTS/releases/download/0.8.1/kittentts-0.8.1-py3-none-any.whl"

# Piper local CPU TTS. Keep voice model files outside the repository.
"$PIP" install "piper-tts"

if [ ! -f "$PIPER_DIR/en_US-lessac-medium.onnx" ]; then
  echo "Downloading the default Piper voice (en_US-lessac-medium)..."
  (
    cd "$PIPER_DIR"
    "$PY" -m piper.download_voices en_US-lessac-medium
  )
fi

if [ "$WITH_LUX" -eq 1 ]; then
  echo "Installing LuxTTS. This is substantially heavier than Kitten/Piper."
  if [ ! -d "$LUX_DIR/.git" ]; then
    git clone https://github.com/ysharma3501/LuxTTS.git "$LUX_DIR"
  else
    git -C "$LUX_DIR" pull --ff-only
  fi
  "$PIP" install -r "$LUX_DIR/requirements.txt"
else
  echo
  echo "LuxTTS support is built into Ashen Voice Studio but was not installed yet."
  echo "Install it later with:"
  echo "  bash scripts/install-native-engines.sh --with-lux"
fi

echo
echo "Native engine install complete."
echo "Python: $($PY --version)"
echo "Environment: $VENV"
echo "Piper voices: $PIPER_DIR"
if [ "$WITH_LUX" -eq 1 ]; then
  echo "LuxTTS: $LUX_DIR"
fi
