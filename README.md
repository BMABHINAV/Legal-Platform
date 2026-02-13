# Legal Platform - Django Project

A Django-based legal services platform that connects citizens with verified legal professionals across India.

## Features

- **Provider Directory**: Browse and connect with verified advocates, mediators, notaries, and legal experts
- **Document Analyzer**: AI-powered document analysis using Google Gemini AI
- **AI Legal Assistant**: Chat with an AI assistant for legal guidance
- **Legal Triage**: Smart questionnaire to match users with the right legal experts
- **Incentive Program**: Gamified rewards system for providers
- **Leaderboard**: Ranking of top legal service providers

## Prerequisites

- Python 3.10 or higher
- pip (Python package manager)

## Setup Instructions

### 1. Navigate to the Django project directory

```bash
cd django_project
```

### 2. Create a virtual environment

```bash
python -m venv venv
```

### 3. Activate the virtual environment

**Windows:**
```bash
venv\Scripts\activate
```

**macOS/Linux:**
```bash
source venv/bin/activate
```

### 4. Install dependencies

```bash
pip install -r requirements.txt
```

### 5. Configure environment variables

Create a `.env` file based on the example:

```bash
copy .env.example .env
```

Edit the `.env` file and add your settings:
- `DJANGO_SECRET_KEY`: A secure random string for Django
- `GEMINI_API_KEY`: Your Google Gemini API key (required for AI features)

### 6. Run database migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

### 7. Create a superuser (optional)

```bash
python manage.py createsuperuser
```

### 8. Collect static files

```bash
python manage.py collectstatic --noinput
```

### 9. Run the development server

```bash
python manage.py runserver
```

The application will be available at `http://127.0.0.1:8000`

## Project Structure

```
django_project/
├── legal_platform/          # Project settings
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── core/                    # Main application
│   ├── models.py           # Database models
│   ├── views.py            # View functions
│   ├── urls.py             # URL routing
│   ├── forms.py            # Form definitions
│   ├── admin.py            # Admin configuration
│   ├── mock_data.py        # Sample data
│   ├── incentive_rules.py  # Incentive system
│   └── gemini_service.py   # AI integration
├── templates/               # HTML templates
│   ├── base.html
│   └── core/
├── static/                  # Static files (CSS, JS, images)
│   └── css/
├── manage.py
├── requirements.txt
└── README.md
```

## Key URLs

- `/` - Home page
- `/providers/` - Browse legal providers
- `/document-analyzer/` - AI document analysis
- `/ai-assistant/` - Legal AI chatbot
- `/triage/` - Legal needs questionnaire
- `/leaderboard/` - Provider rankings
- `/incentives/` - Incentive program info
- `/become-provider/` - Provider registration
- `/admin/` - Django admin panel

## Technologies Used

- **Backend**: Django 4.2
- **Frontend**: Tailwind CSS (via CDN), Alpine.js
- **AI**: Google Gemini AI (gemini-1.5-flash)
- **Database**: SQLite (default), PostgreSQL ready
- **File Processing**: PyPDF2, python-docx, mammoth

## Getting a Gemini API Key

1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Create a new API key
3. Add it to your `.env` file as `GEMINI_API_KEY`

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

This project is for educational purposes.
