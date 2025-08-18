# Videoflix Backend API

![Videoflix Logo](assets/logo_icon.svg)

Dieses Projekt ist ein vollständiges **Django REST Framework Backend** für eine HLS-basierte Video-Streaming-Plattform. Es wurde entwickelt, um moderne Backend-Entwicklung mit **Django**, **PostgreSQL**, **Redis** und **Docker** zu demonstrieren.

---

## Technologie-Stack

- **Django 5.2.4** - Web Framework
- **Django REST Framework 3.16.0** - API Development
- **PostgreSQL 17** - Hauptdatenbank
- **Redis Latest** - Caching & Task Queue
- **Django RQ 3.0.1** - Background Task Processing
- **JWT Authentication** - Cookie-basierte Authentifizierung
- **Docker & Docker Compose** - Containerisierung
- **pytest 8.4.1** - Testing Framework
- **FFmpeg** - Video Processing für HLS
- **Python 3.12-Alpine** - Runtime Environment

---

## Voraussetzungen

- **Docker Desktop** installiert und laufend
- **Git** für das Klonen des Repositories
- **Videoflix Frontend** - Dieses Backend ist darauf ausgelegt, **nur zusammen mit dem Videoflix Frontend** zu funktionieren
- **Postman** oder ähnliches Tool zum Testen der API (optional)

---

## Installation & Setup

### 1. Repository klonen
```bash
git clone <repository-url>
cd videoflix-backend
```

### 2. Environment-Variablen einrichten
```bash
# .env Datei aus Template erstellen
cp .env.template .env

# .env Datei nach Bedarf anpassen
nano .env  # oder mit VS Code bearbeiten
```

**Environment-Variablen aus .env.template:**
```env
# Django Superuser (wird automatisch erstellt)
DJANGO_SUPERUSER_USERNAME=admin
DJANGO_SUPERUSER_PASSWORD=adminpassword
DJANGO_SUPERUSER_EMAIL=admin@example.com

# Django Settings
SECRET_KEY="django-insecure-lp6h18zq4@z30symy*oz)+hp^uoti48r_ix^qc-m@&yfxd7&hn"
DEBUG=True
PRODUCTION=False
ALLOWED_HOSTS=localhost,127.0.0.1
CSRF_TRUSTED_ORIGINS=http://localhost:4200,http://127.0.0.1:4200

# Database Configuration
DB_NAME=your_database_name
DB_USER=your_database_user
DB_PASSWORD=your_database_password
DB_HOST=db
DB_PORT=5432

# Redis Configuration
REDIS_HOST=redis
REDIS_LOCATION=redis://redis:6379/1
REDIS_PORT=6379
REDIS_DB=0

# Email Configuration
EMAIL_HOST=smtp.example.com
EMAIL_PORT=587
EMAIL_HOST_USER=your_email_user
EMAIL_HOST_PASSWORD=your_email_user_password
EMAIL_USE_TLS=True
EMAIL_USE_SSL=False
DEFAULT_FROM_EMAIL=default_from_email
```

**Wichtige Anpassungen für die Entwicklung:**
- Ersetze `your_database_*` mit deinen gewünschten DB-Credentials
- Konfiguriere Email-Settings für dein SMTP-Provider.
- Für Production: Ändere `SECRET_KEY`, `DEBUG=False `, `PRODUCTION=True`

### 3. Docker Container starten
```bash
# Alle Services starten
docker-compose up --build

# Im Hintergrund starten
docker-compose up -d --build
```

Das System startet automatisch:
- **PostgreSQL** auf `videoflix_database` Container
- **Redis** auf `videoflix_redis` Container  
- **Django Backend** auf `videoflix_backend` Container (Port 8000)
- **RQ Worker** für Video-Processing (läuft im Backend-Container)

### 4. Automatische Setup-Schritte
Das `backend.entrypoint.sh` Script führt automatisch aus:
- Warten auf PostgreSQL-Verfügbarkeit
- Static Files sammeln
- Datenbank-Migrationen erstellen und ausführen
- Superuser erstellen (basierend auf Environment-Variablen)
- RQ Worker für Background Tasks starten

---

## Nutzung

### **API Endpoints**

Das Backend läuft standardmäßig auf `http://localhost:8000`

#### **Authentication**
- `POST /api/register/` - Benutzerregistrierung
- `POST /api/login/` - Login (Cookie-basiert)
- `POST /api/logout/` - Logout
- `POST /api/token/refresh/` - Token erneuern
- `GET /api/activate/<uidb64>/<token>/` - Account aktivieren
- `POST /api/password_reset/` - Password Reset anfordern
- `POST /api/password_confirm/<uidb64>/<token>/` - Password zurücksetzen

#### **Video List and HLS Streaming**
- `GET /api/videos/` - Video-Liste (mit Category-Filter)
- `GET /api/videos/<id>/<resolution>/index.m3u8` - HLS Manifest
- `GET /api/videos/<id>/<resolution>/<segment>` - HLS Video-Segmente

**Unterstützte Auflösungen:** `360p`, `480p`, `720p`, `1080p`

### **Admin Interface**
Verfügbar unter `http://localhost:8000/admin/`
- **Username:** `admin` (oder aus ENV)
- **Password:** `adminpassword` (oder aus ENV)

### **RQ Dashboard**
Django-RQ Dashboard verfügbar unter `http://localhost:8000/django-rq/`

---

## Video Processing

Das System konvertiert hochgeladene Videos automatisch zu HLS-Format:

1. **Upload** - Video wird hochgeladen und `processing_status='pending'` gesetzt
2. **Background Processing** - RQ Worker konvertiert Video zu 4 Auflösungen
3. **HLS Output** - Segmente und Playlists werden in `media/hls/{video_id}/` gespeichert
4. **Streaming** - Videos können über HLS-Endpoints gestreamt werden

**Unterstützte Video-Formate:** `mp4`, `mov`, `avi`, `wmv`, `asf`  
**Max. Dateigröße:** 10GB

---

## Entwicklung

### **Container-Befehle**
```bash
# In Backend-Container einloggen
docker exec -it videoflix_backend sh

# Backend-Logs anzeigen
docker-compose logs -f web

# Alle Logs anzeigen
docker-compose logs -f

# Container neustarten
docker-compose restart web
```

### **Tests ausführen**
```bash
# In den Container einloggen
docker-compose exec web sh

# Alle Tests ausführen
pytest

# Mit Coverage Report
pytest --cov=auth_app --cov=video_app --cov-report=html

# Nur auth_app Tests
pytest auth_app/tests/

# Nur video_app Tests  
pytest video_app/tests/

# Oder direkt ohne Container-Login:
docker-compose exec web pytest
```

### **Video Management Commands**
```bash
# Liste aller Videos anzeigen
docker exec -it videoflix_backend python manage.py list_videos

# Video manuell verarbeiten (synchron für Tests)
docker exec -it videoflix_backend python manage.py process_video <video_id> --sync

# Fehlgeschlagene Videos bereinigen
docker exec -it videoflix_backend python manage.py cleanup_failed --delete-files
```

### **Datenbank-Operationen**
```bash
# Migrationen erstellen
docker exec -it videoflix_backend python manage.py makemigrations

# Migrationen anwenden
docker exec -it videoflix_backend python manage.py migrate

# Django Shell öffnen
docker exec -it videoflix_backend python manage.py shell

# Datenbank zurücksetzen (ACHTUNG: Datenverlust!)
docker-compose down -v
docker-compose up --build
```

---

## Features

### 🔐 **Authentifizierung**
- Cookie-basierte JWT-Authentifizierung
- Email-Aktivierung mit HTML Templates
- Password Reset Funktionalität
- Sichere Token-Rotation mit Blacklisting
- CORS-Konfiguration für Frontend-Integration

### 🎥 **Video Streaming**
- HLS (HTTP Live Streaming) Support
- Multi-Resolution Video Delivery (360p bis 1080p)
- Authentifizierte Video-Segmente
- Efficient File Serving mit StreamingHttpResponse

### 📧 **Email System**
- HTML Email Templates für Aktivierung & Password Reset
- Development & Production Email Backends
- Konfigurierbare SMTP-Settings
- Template-basierte Email-Generation

### 🔄 **Background Processing**
- Django-RQ für Video-Konvertierung
- FFmpeg-Integration für HLS-Processing
- Progress-Tracking für Video-Verarbeitung
- Error-Handling und Retry-Mechanismen

### 🐳 **Docker Integration**
- Multi-Container Setup (PostgreSQL, Redis, Django)
- Alpine-based Images für geringe Container-Größe

### 🧪 **Testing & Quality**
- pytest mit Django Integration
- Code Coverage Tracking

---

## API Dokumentation

### **Authentication und Streaming Flow**
1. **Register** → Email-Bestätigung erforderlich
2. **Activate** → Account via Email-Link aktivieren  
3. **Login** → JWT-Cookies werden gesetzt
4. **Access** → Authentifizierte API-Requests
5. **Streaming** → HLS-Playback über authentifizierte Endpoints
6. **Logout** → Token-Blacklisting

---

## Deployment

### **Production Setup**
```bash
# Production Environment Variables setzen
export DEBUG=False
export SECRET_KEY=your-production-secret
export DB_PASSWORD=secure-production-password
export EMAIL_HOST_USER=production-email@domain.com

# SSL/HTTPS Settings werden automatisch aktiviert
export PRODUCTION=True
```

---

## Troubleshooting

### **Häufige Probleme**

#### Container startet nicht
```bash
# Logs prüfen
docker-compose logs web

# Container Status prüfen
docker ps -a

# Ports prüfen
netstat -tulpn | grep :8000
```

#### Video Processing hängt
```bash
# RQ Worker Status prüfen
docker exec -it videoflix_backend python manage.py rq info

# Failed Jobs anzeigen
docker exec -it videoflix_backend python manage.py cleanup_failed
```

---

## Support & Dokumentation

- **Container Logs:** `docker-compose logs -f`
- **Django Admin:** `http://localhost:8000/admin/`
- **RQ Dashboard:** `http://localhost:8000/django-rq/`

---

## Hinweis

Dieses Backend ist darauf ausgelegt, **nur zusammen mit dem Videoflix Frontend** zu funktionieren und demonstriert professionelle Backend-Entwicklung mit modernen Tools und Best Practices.

**Entwickelt von Philip Schaper für die Developer Akademie** - Ein vollständiges Beispiel für moderne Django-Backend-Architektur.