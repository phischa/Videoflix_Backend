# Videoflix Backend API

![Videoflix Logo](media/assets/logo_icon.svg)

Dieses Projekt ist ein vollständiges **Django REST Framework Backend** für eine HLS-basierte Video-Streaming-Plattform. Es wurde entwickelt, um moderne Backend-Entwicklung mit **Django**, **PostgreSQL**, **Redis** und **Docker** zu demonstrieren.

---

## Technologie-Stack

- **Django 5.2.4** - Web Framework
- **Django REST Framework** - API Development
- **PostgreSQL** - Hauptdatenbank
- **Redis** - Caching & Task Queue
- **Django RQ** - Background Task Processing
- **JWT Authentication** - Cookie-basierte Authentifizierung
- **Docker & Docker Compose** - Containerisierung
- **pytest** - Testing Framework mit 88%+ Coverage

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
# Die env.templates Datei als Vorlage verwenden
cp env.templates .env

# .env Datei nach Bedarf anpassen
# Alle nötigen Variablen sind bereits in env.templates vordefiniert
```

### 3. Docker Container starten
```bash
# Alle Services starten
docker-compose up --build

# Im Hintergrund starten
docker-compose up -d --build
```

### 4. Datenbank migrieren
```bash
# In den Web-Container einloggen
docker-compose exec web /bin/sh

# Migrationen ausführen
python manage.py migrate

# Superuser erstellen (optional)
python manage.py createsuperuser
```

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

#### **Video Streaming**
- `GET /api/video/` - Video-Liste
- `GET /api/video/<id>/<resolution>/index.m3u8` - HLS Manifest
- `GET /api/video/<id>/<resolution>/<segment>/` - HLS Video-Segmente

### **Admin Interface**
Verfügbar unter `http://localhost:8000/admin/` (nach Superuser-Erstellung)

### **API Dokumentation**
Die vollständige API-Dokumentation findest du in `docs/api-documentation.pdf`

---

## Entwicklung

### **Tests ausführen**
```bash
# In den Container einloggen
docker-compose exec web /bin/sh

# Alle Tests ausführen
pytest

# Mit Coverage Report
pytest --cov=auth_app --cov=video_app --cov-report=html

# Nur auth_app Tests
pytest auth_app/tests/

# Nur video_app Tests  
pytest video_app/tests/
```

### **Datenbank zurücksetzen**
```bash
# Container stoppen
docker-compose down

# Volumes löschen (ACHTUNG: Alle Daten gehen verloren!)
docker-compose down -v

# Neu starten
docker-compose up --build
```

### **Logs anzeigen**
```bash
# Alle Services
docker-compose logs

# Nur Web-Service
docker-compose logs web

# Live Logs
docker-compose logs -f web
```

---

## Projektstruktur

```
videoflix-backend/
├── auth_app/                 # Authentifizierung & User Management
│   ├── api/                  # API Views, Serializers, URLs
│   ├── services/             # Email & Token Services
│   ├── tests/                # 88%+ Test Coverage
│   └── authentication.py    # Custom JWT Cookie Authentication
├── video_app/                # Video Management & HLS Streaming
│   ├── api/                  # Video API Endpoints
│   ├── models.py             # Video Model
│   ├── services/             # Video Processing Services
│   └── tests/                # Comprehensive Tests
├── core/                     # Django Settings & Main Config
├── templates/                # Email Templates
├── static/                   # Static Files
├── media/                    # User Uploads & HLS Files
├── docker-compose.yml        # Docker Services Configuration
├── Dockerfile               # Web Container Configuration
├── requirements.txt         # Python Dependencies
├── env.templates            # Environment Variables Template
└── pytest.ini              # Test Configuration
```

---

## Features

### **🔐 Authentifizierung**
- Cookie-basierte JWT-Authentifizierung
- Email-Aktivierung mit Templates
- Password Reset Funktionalität
- Sichere Token-Rotation

### **🎥 Video Streaming**
- HLS (HTTP Live Streaming) Support
- Multi-Resolution Video Delivery
- Authenticierte Video-Segmente
- Efficient File Serving

### **📧 Email System**
- HTML Email Templates
- Activation & Password Reset Emails
- Development & Production Email Backends
- Queue-basierte Email Verarbeitung

### **🧪 Testing**
- **88%+ Test Coverage**
- pytest mit Django Integration
- Fixtures für realistische Test-Daten
- Mock-basierte Service Tests

### **🐳 Docker Integration**
- Multi-Container Setup
- PostgreSQL & Redis Services
- Development & Production Ready
- Volume Persistence

---

## Ziel des Projekts

Dieses Backend wurde entwickelt, um folgende **moderne Backend-Konzepte** zu demonstrieren:

- **RESTful API Design** mit Django REST Framework
- **Microservices-ähnliche Architektur** mit separaten Apps
- **Cookie-basierte JWT-Authentifizierung** für Web-Sicherheit
- **Video-Streaming-Technologien** mit HLS
- **Containerisierung** mit Docker
- **Test-Driven Development** mit hoher Coverage
- **Email-Integration** für User-Onboarding
- **Background Task Processing** mit Redis Queue

---

## Deployment

### **Production Setup**
```bash
# Production Environment Variables setzen
export DEBUG=False
export DATABASE_URL=your_production_db
export REDIS_URL=your_production_redis

# Mit Production Settings starten
docker-compose -f docker-compose.prod.yml up --build
```

### **Environment Variables**
- `DEBUG` - Django Debug Mode
- `SECRET_KEY` - Django Secret Key
- `DATABASE_URL` - PostgreSQL Connection String
- `REDIS_URL` - Redis Connection String
- `EMAIL_HOST_USER` - SMTP Email Configuration
- `FRONTEND_URL` - Frontend URL for CORS

---

## Support & Dokumentation

- **API Dokumentation**: `docs/api-documentation.pdf`
- **Code Coverage Report**: Nach Test-Ausführung in `htmlcov/index.html`
- **Django Admin**: `http://localhost:8000/admin/`
- **Container Logs**: `docker-compose logs -f`

---

## Hinweis

Dieses Backend ist darauf ausgelegt, **nur zusammen mit dem Videoflix Frontend** zu funktionieren und demonstriert professionelle Backend-Entwicklung mit modernen Tools und Best Practices.

