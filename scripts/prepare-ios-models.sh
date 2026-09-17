#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
MODELS="$ROOT/ios-native/Resources/Models"
TMP="$ROOT/.ios-model-cache"
mkdir -p "$MODELS" "$TMP"

fetch_unpack() {
  local name="$1"
  local url="$2"
  local expected="$MODELS/$name"
  if [ -d "$expected" ]; then
    echo "iOS model already prepared: $name"
    return
  fi
  local archive="$TMP/$name.tar.bz2"
  if [ ! -f "$archive" ]; then
    echo "Downloading $name..."
    curl -fL --retry 4 --retry-delay 2 "$url" -o "$archive"
  fi
  echo "Extracting $name..."
  tar -xjf "$archive" -C "$MODELS"
}

# Smallest modern Kitten v0.8 package exposed by sherpa-onnx. This is the default
# character engine on iPhone and runs through native ONNX, not WebKit/WASM.
fetch_unpack \
  "kitten-nano-en-v0_8-int8" \
  "https://github.com/k2-fsa/sherpa-onnx/releases/download/tts-models/kitten-nano-en-v0_8-int8.tar.bz2"

# Reliable Piper/VITS fallback voice.
fetch_unpack \
  "vits-piper-en_US-lessac-medium" \
  "https://github.com/k2-fsa/sherpa-onnx/releases/download/tts-models/vits-piper-en_US-lessac-medium.tar.bz2"

# On-device zero-shot cloning. Ashen's cross-platform schema continues to call the
# clone route `lux`; the iOS bridge implements that route with ZipVoice locally.
fetch_unpack \
  "sherpa-onnx-zipvoice-distill-int8-zh-en-emilia" \
  "https://github.com/k2-fsa/sherpa-onnx/releases/download/tts-models/sherpa-onnx-zipvoice-distill-int8-zh-en-emilia.tar.bz2"

if [ ! -f "$MODELS/vocos_24khz.onnx" ]; then
  echo "Downloading ZipVoice vocoder..."
  curl -fL --retry 4 --retry-delay 2 \
    "https://github.com/k2-fsa/sherpa-onnx/releases/download/vocoder-models/vocos_24khz.onnx" \
    -o "$MODELS/vocos_24khz.onnx"
fi

echo "Prepared iPhone-local Kitten, Piper and ZipVoice model resources in $MODELS"
