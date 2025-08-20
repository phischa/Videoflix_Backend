#!/bin/bash
cd /opt/django-videoflix

# nginx stoppen
docker compose stop nginx

# Zertifikat erneuern (neue Domain)
certbot renew --quiet

# nginx starten (letsencrypt mount funktioniert automatisch)
docker compose start nginx

echo "SSL certificates renewed successfully for api.philip-schaper.de"
