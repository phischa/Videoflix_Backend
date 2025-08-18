#!/bin/bash
cd /opt/django-videoflix

# nginx stoppen
docker compose stop nginx

# Zertifikat erneuern
certbot renew --quiet

# Neue Zertifikate kopieren
cp /etc/letsencrypt/live/api-videoflix.duckdns.org/fullchain.pem /etc/ssl/videoflix/
cp /etc/letsencrypt/live/api-videoflix.duckdns.org/privkey.pem /etc/ssl/videoflix/
#cp /etc/letsencrypt/live/api-videoflix.duckdns.org/fullchain.pem /opt/django-videoflix/deploy/ssl/
#cp /etc/letsencrypt/live/api-videoflix.duckdns.org/privkey.pem /opt/django-videoflix/deploy/ssl/

# nginx starten
docker compose start nginx

echo "SSL certificates renewed successfully"
