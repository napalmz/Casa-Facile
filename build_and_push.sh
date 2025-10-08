#!/bin/bash

set -e  # Interrompe l'esecuzione in caso di errore

# Ottiene la versione dell'App dal file "Casa Facile.pyw"
APP_VERSION=$(grep '^VERSION' "Casa Facile.pyw" | sed -E 's/^[^"]*"([^"]*)".*/\1/' || echo "dev")

echo "Ultima versione dell'App: $APP_VERSION"

# Esportiamo la versione come variabile globale per essere usata nei Dockerfile
export APP_VERSION=$APP_VERSION

# Variabili per i tag
APP_TAG_BASE="napalmzrpi/casa-facile-pro"
APP_TAG_VERSION="$APP_TAG_BASE:$APP_VERSION"
APP_TAG_LATEST="$APP_TAG_BASE:latest"

# Funzione per chiedere conferma
ask_confirmation() {
  local prompt="$1 [Y/N] (default: N): "
  local response
  read -r -p "$prompt" response
  response=$(echo "$response" | tr '[:upper:]' '[:lower:]')  # Convertire in minuscolo

  if [[ "$response" == "y" ]]; then
    return 0  # Vero, esegui l'operazione
  else
    return 1  # Falso, salta l'operazione
  fi
}

# Chiedere se costruire l'immagine per Backend
if ask_confirmation "Vuoi costruire l'immagine per l'App?"; then

  PLATFORMS="linux/amd64,linux/arm64"

  echo "Costruzione dell'immagine per App $PLATFORMS..."
  docker buildx build --platform $PLATFORMS --build-arg APP_VERSION=$APP_VERSION \
    -t $APP_TAG_VERSION \
    -t $APP_TAG_LATEST \
    -f Dockerfile . --push
else
  echo "Costruzione dell'immagine per App saltato."
fi