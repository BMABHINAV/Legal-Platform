# 🚀 Running the Real-Time Legal Platform

This guide covers running the Django Legal Platform with all real-time features including WebSockets, background tasks, and video calls.

## 📋 Prerequisites

1. **Python 3.10+** installed
2. **Redis Server** (for Channels & Celery)
3. **Google Gemini API Key** (for AI features)

## ⚡ Quick Start

### 1. Install Dependencies

```bash
cd django_project
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Create a `.env` file in the `django_project` folder:

```env
# Django
SECRET_KEY=your-secret-key-here
DEBUG=True

# Gemini AI
GOOGLE_API_KEY=your-gemini-api-key

# Redis (for Channels & Celery)
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_URL=redis://localhost:6379/0

# Celery
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
```

### 3. Install & Start Redis

**Windows (using Chocolatey):**
```bash
choco install redis-64
redis-server
```

**Windows (using Docker):**
```bash
docker run -d -p 6379:6379 --name redis redis:alpine
```

**Ubuntu/Debian:**
```bash
sudo apt install redis-server
sudo systemctl start redis
```

**macOS:**
```bash
brew install redis
brew services start redis
```

### 4. Database Setup

```bash
python manage.py makemigrations core
python manage.py migrate
python manage.py createsuperuser
```

### 5. Seed Sample Data (Optional)

```bash
python manage.py seed_data
```

---

## 🖥️ Running the Application

You need **4 terminal windows** for full functionality:

### Terminal 1: Django Development Server (HTTP + WebSocket)

```bash
cd django_project
daphne -b 0.0.0.0 -p 8000 legal_platform.asgi:application
```

**Or use Django's runserver for development:**
```bash
python manage.py runserver
```

> ⚠️ Note: Use `daphne` for WebSocket support. `runserver` works for HTTP but WebSockets may not work in development mode.

### Terminal 2: Celery Worker (Background Tasks)

```bash
cd django_project
celery -A legal_platform worker -l info -P solo
```

> The `-P solo` flag is needed for Windows. On Linux/macOS, you can omit it.

### Terminal 3: Celery Beat (Scheduled Tasks)

```bash
cd django_project
celery -A legal_platform beat -l info
```

### Terminal 4: Redis Server (if not running as service)

```bash
redis-server
```

---

## 🌐 Accessing Features

| Feature | URL |
|---------|-----|
| Home Page | http://localhost:8000/ |
| Login | http://localhost:8000/login/ |
| Signup | http://localhost:8000/signup/ |
| Find Lawyers | http://localhost:8000/providers/ |
| Document Analyzer | http://localhost:8000/document-analyzer/ |
| AI Assistant | http://localhost:8000/ai-assistant/ |
| **Real-Time Chat** | http://localhost:8000/chat/<room_id>/ |
| **Video Consultation** | http://localhost:8000/video/<room_id>/ |
| **Panic Button** | http://localhost:8000/emergency/ |
| **AI Judge Simulator** | http://localhost:8000/case-predictor/ |
| **Crowdfunding** | http://localhost:8000/crowdfunding/ |
| **Voice Input** | http://localhost:8000/voice-input/ |
| Admin Panel | http://localhost:8000/admin/ |

---

## 🛠️ Feature Details

### 1. Real-Time Chat (WebSocket)
- Navigate to `/chat/<room_id>/` 
- Two users can join the same room for instant messaging
- Features: Typing indicators, read receipts, message status

### 2. Video Consultation (WebRTC)
- Navigate to `/video/<room_id>/`
- Peer-to-peer video calling with signaling via WebSocket
- Features: Mute/unmute, camera toggle, shared whiteboard

### 3. Panic Button (Emergency SOS)
- Navigate to `/emergency/`
- One-tap emergency alert with geolocation
- Broadcasts to nearby lawyers with notifications

### 4. AI Judge Simulator
- Navigate to `/case-predictor/`
- Enter case details for AI-powered outcome prediction
- Based on Indian legal precedents

### 5. Smart Contract Escrow
- Automatic with bookings
- Funds released after service delivery confirmation
- Auto-release after 7 days (configurable)

### 6. Crowdfunding (Pro Bono)
- Navigate to `/crowdfunding/`
- Create campaigns for legal aid
- Donors can contribute to verified cases

### 7. Voice-to-Text
- Navigate to `/voice-input/`
- Speak in regional languages (Hindi, Tamil, etc.)
- Get AI legal help in your language

---

## 📊 Background Tasks (Celery)

| Task | Schedule | Description |
|------|----------|-------------|
| Auto-release escrow | Daily @ 2 AM | Releases funds after 7 days |
| Consultation reminders | Every 5 min | Sends 15-min advance alerts |
| Cleanup emergencies | Daily @ 3 AM | Resolves stale emergencies |
| Update leaderboard | Daily @ 4 AM | Refreshes incentive points |

---

## 🔧 Troubleshooting

### WebSocket Connection Failed
1. Ensure Redis is running: `redis-cli ping` (should return PONG)
2. Use daphne instead of runserver
3. Check browser console for errors

### Celery Not Processing Tasks
1. Check Redis connection
2. Ensure worker is running with `-P solo` on Windows
3. Check `CELERY_BROKER_URL` in settings

### Video Call Not Working
1. Allow camera/microphone permissions in browser
2. Use HTTPS for production (WebRTC requirement)
3. Check STUN server connectivity

### AI Features Not Working
1. Verify `GOOGLE_API_KEY` is set
2. Check Gemini API quota/limits
3. Look for errors in console

---

## 🚀 Production Deployment

For production, use:

1. **Gunicorn + Uvicorn** for ASGI:
   ```bash
   gunicorn legal_platform.asgi:application -k uvicorn.workers.UvicornWorker
   ```

2. **Nginx** for reverse proxy with WebSocket support

3. **Redis** managed service (AWS ElastiCache, Redis Cloud)

4. **PostgreSQL** instead of SQLite

5. **SSL/HTTPS** required for WebRTC

6. **Supervisor/Systemd** for process management

---

## 📁 Project Structure (Real-Time Features)

```
django_project/
├── legal_platform/
│   ├── asgi.py          # ASGI config with Channels
│   ├── celery.py        # Celery configuration
│   └── settings.py      # Updated with Channels/Celery
├── core/
│   ├── consumers.py     # WebSocket consumers
│   ├── routing.py       # WebSocket URL patterns
│   ├── tasks.py         # Background tasks
│   ├── models.py        # New real-time models
│   ├── views.py         # Real-time feature views
│   └── urls.py          # Updated URL patterns
└── templates/core/
    ├── chat_room.html       # Real-time chat UI
    ├── video_room.html      # WebRTC video call UI
    ├── emergency.html       # Panic button UI
    ├── case_predictor.html  # AI Judge UI
    ├── crowdfunding_*.html  # Crowdfunding UIs
    └── voice_input.html     # Voice-to-text UI
```

---

## 📞 Support

For issues, check:
1. Django debug logs
2. Browser developer console
3. Redis connection: `redis-cli ping`
4. Celery worker logs

Happy coding! ⚖️✨
