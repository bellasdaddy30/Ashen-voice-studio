#!/usr/bin/env bash
set -euo pipefail

APP_HOME="${ASHEN_VOICE_HOME:-$HOME/.local/share/ashen-voice-studio}"
VENV="$APP_HOME/venv"
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

if [ ! -d "$VENV" ]; then
  echo "Creating Ashen Voice native-engine environment..."
  python3 -m venv "$VENV"
fi

PY="$VENV/bin/python"
PIP="$VENV/bin/pip"

"$PY" -m pip install --upgrade pip setuptools wheel

# KittenTTS 0.8.1 + its CPU runtime.
"$PIP" install "https://github.com/KittenML/KittenTTS/releases/download/0.8.1/kittentts-0.8.1-py3-none-any.whl"

# Piper's current local Python package. Keep its models outside the repo.
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
echo "Environment: $VENV"
echo "Piper voices: $PIPER_DIR"
if [ "$WITH_LUX" -eq 1 ]; then
  echo "LuxTTS: $LUX_DIR"
fi
