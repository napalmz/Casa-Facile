# Desktop web-native con VNC/noVNC
FROM ghcr.io/linuxserver/baseimage-selkies:debiantrixie

ARG APP_VERSION=unknown
LABEL maintainer="napalmz <https://github.com/napalmz/Casa-Facile>"
LABEL version="$APP_VERSION"

RUN echo "**** update & base deps ****" && \
    apt-get update && apt-get upgrade -y && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
      curl \
      ca-certificates \
      nano \
      tree \
      python3 \
      python3-pip \
      python3-tk \
      python3-requests \
      python3-xdg \
      locales && \
    echo "**** locales ****" && \
    sed -i 's/# *it_IT.UTF-8 UTF-8/it_IT.UTF-8 UTF-8/' /etc/locale.gen && \
    sed -i 's/# *en_US.UTF-8 UTF-8/en_US.UTF-8 UTF-8/' /etc/locale.gen && \
    locale-gen && \
    echo "**** python deps ****" && \
    pip3 install --no-cache-dir --break-system-packages tkcalendar psutil && \
    echo "**** cleanup ****" && \
    apt-get autoclean && rm -rf /var/lib/apt/lists/* /var/tmp/* /tmp/*

RUN echo "**** get app ****" && \
    mkdir -p /opt/app && \
    curl -fSL -o /opt/app/Casa-Facile.pyw \
      "https://raw.githubusercontent.com/Renato-4132/Casa-Facile/main/Casa%20Facile.pyw"

RUN echo "**** stage defaults (not in /config at build time) ****" && \
    mkdir -p /defaults/casa-facile /etc/cont-init.d && \
    cp /opt/app/Casa-Facile.pyw "/defaults/casa-facile/Casa Facile.pyw" && \
    printf '%s\n' \
      '#!/usr/bin/with-contenv bash' \
      'set -e' \
      'mkdir -p /config/casa-facile' \
      'if [ ! -f "/config/casa-facile/Casa Facile.pyw" ]; then' \
      '  cp "/defaults/casa-facile/Casa Facile.pyw" "/config/casa-facile/Casa Facile.pyw"' \
      'fi' \
      'chown -R abc:abc /config' \
      > /etc/cont-init.d/30-casafacile && \
    chmod +x /etc/cont-init.d/30-casafacile && \
    printf '%s\n' \
      '#!/bin/bash' \
      'set -e' \
      'export LANG=it_IT.UTF-8' \
      'export LC_ALL=it_IT.UTF-8' \
      'cd /config/casa-facile' \
      'exec python3 "Casa Facile.pyw"' \
      > /usr/local/bin/start-casafacile.sh && \
    chmod +x /usr/local/bin/start-casafacile.sh

# Globali
ENV TITLE="Casa-Facile Pro"
ENV NO_FULL=true
# Selkies sane defaults to avoid gigantic RANDR modes (use SELKIES_* envs)
ENV SELKIES_UI_TITLE="Casa-Facile"
ENV SELKIES_IS_MANUAL_RESOLUTION_MODE=true
ENV SELKIES_MANUAL_WIDTH=1600
ENV SELKIES_MANUAL_HEIGHT=900
ENV SELKIES_USE_CSS_SCALING=true
ENV SELKIES_MAX_RES=2560x1440
ENV SELKIES_SECOND_SCREEN=false
ENV SELKIES_USE_BROWSER_CURSORS=true
ENV LANG=it_IT.UTF-8 \
    LC_ALL=it_IT.UTF-8

# Porte: 3000 noVNC (web), 5901 VNC
EXPOSE 3000 3001 5901

# stage defaults provided in repo (if any)
COPY /root /

# Volume dati utente
VOLUME ["/config"]