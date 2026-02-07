# Mati - Quick Start Guide
## AstroNexus Platform Setup

---

## Prerequisites

Before you begin, ensure you have:

1. **Python 3.9+** installed
   ```bash
   python --version  # Should be 3.9 or higher
   ```

2. **Anthropic API Key**
   - Sign up at: https://console.anthropic.com/
   - Get your API key from the dashboard

3. **Swiss Ephemeris Data**
   - Download from: https://www.astro.com/ftp/swisseph/ephe/
   - Download these files:
     - `seas_18.se1` (main ephemeris)
     - `semo_18.se1` (moon)
     - `sepl_18.se1` (planets)
   - Place in `/usr/share/ephe/` or custom directory

4. **Git** (for version control)
   ```bash
   git --version
   ```

---

## Installation Steps

### Step 1: Clone or Create Project Directory

```bash
mkdir astro-nexus
cd astro-nexus
```

### Step 2: Create Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate it
# On macOS/Linux:
source venv/bin/activate
# On Windows:
venv\Scripts\activate
```

### Step 3: Install Dependencies

```bash
# Install all required packages
pip install -r requirements.txt

# Verify pyswisseph installation
python -c "import swisseph as swe; print('Swiss Ephemeris OK')"
```

### Step 4: Set Up Environment Variables

Create a `.env` file in your project root:

```bash
# .env file
ANTHROPIC_API_KEY=your_api_key_here
EPHEMERIS_PATH=/usr/share/ephe
DATABASE_URL=postgresql://user:password@localhost:5432/astronexus
REDIS_URL=redis://localhost:6379
SECRET_KEY=your_secret_key_here_change_in_production
```

### Step 5: Download Swiss Ephemeris Data

```bash
# Create ephemeris directory
sudo mkdir -p /usr/share/ephe

# Download ephemeris files (Linux/Mac)
cd /usr/share/ephe
sudo wget https://www.astro.com/ftp/swisseph/ephe/seas_18.se1
sudo wget https://www.astro.com/ftp/swisseph/ephe/semo_18.se1
sudo wget https://www.astro.com/ftp/swisseph/ephe/sepl_18.se1

# Or use custom path and update EPHEMERIS_PATH in .env
```

---

## Running the Application

### Option 1: Development Mode (with auto-reload)

```bash
# Make sure you're in the project directory with virtual environment activated
python mati_api.py
```

The API will be available at: `http://localhost:8000`

### Option 2: Production Mode (with Gunicorn)

```bash
gunicorn -w 4 -k uvicorn.workers.UvicornWorker mati_api:app --bind 0.0.0.0:8000
```

---

## Testing the API

### 1. Health Check

```bash
curl http://localhost:8000/health
```

### 2. Calculate Birth Chart

```bash
curl -X POST http://localhost:8000/api/v1/chart/calculate \
  -H "Content-Type: application/json" \
  -d '{
    "birth_data": {
      "date": "1990-05-15",
      "time": "14:30",
      "latitude": 28.6139,
      "longitude": 77.2090,
      "timezone_offset": 5.5,
      "location_name": "New Delhi, India"
    },
    "include_analysis": true,
    "include_yogas": true
  }'
```

### 3. Generate Birth Chart Report

```bash
curl -X POST http://localhost:8000/api/v1/report/generate \
  -H "Content-Type: application/json" \
  -d '{
    "birth_data": {
      "date": "1990-05-15",
      "time": "14:30",
      "latitude": 28.6139,
      "longitude": 77.2090,
      "timezone_offset": 5.5,
      "location_name": "New Delhi, India"
    },
    "report_type": "birth_chart",
    "user_name": "Ashish",
    "language": "english"
  }'
```

### 4. Ask a Life Question

```bash
curl -X POST http://localhost:8000/api/v1/guidance/ask \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Should I start my own business this year?",
    "birth_data": {
      "date": "1990-05-15",
      "time": "14:30",
      "latitude": 28.6139,
      "longitude": 77.2090,
      "timezone_offset": 5.5
    },
    "context": "I have been working in IT for 5 years and want to pursue my passion for astrology"
  }'
```

---

## API Documentation

Once the server is running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

These provide interactive API documentation.

---

## Project Structure

```
astro-nexus/
├── mati_api.py                    # Main FastAPI application
├── mati_birth_chart_calculator.py # Chart calculation engine
├── mati_ai_engine.py              # AI report generation
├── requirements.txt               # Python dependencies
├── .env                           # Environment variables (create this)
├── README.md                      # Project documentation
└── venv/                          # Virtual environment (created by you)
```

---

## Common Issues & Solutions

### Issue 1: Swiss Ephemeris Not Found

**Error**: `SwissephError: can't open file`

**Solution**:
```bash
# Verify ephemeris files exist
ls /usr/share/ephe

# If not, download them or update EPHEMERIS_PATH in .env
```

### Issue 2: Anthropic API Error

**Error**: `Authentication error` or `Invalid API key`

**Solution**:
```bash
# Verify API key in .env file
cat .env | grep ANTHROPIC_API_KEY

# Test API key
python -c "from anthropic import Anthropic; client = Anthropic(); print('API Key OK')"
```

### Issue 3: Import Errors

**Error**: `ModuleNotFoundError: No module named 'xxx'`

**Solution**:
```bash
# Ensure virtual environment is activated
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Reinstall dependencies
pip install -r requirements.txt
```

### Issue 4: Port Already in Use

**Error**: `Address already in use`

**Solution**:
```bash
# Find and kill process using port 8000
# On macOS/Linux:
lsof -ti:8000 | xargs kill -9

# On Windows:
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# Or use different port
uvicorn mati_api:app --port 8001
```

---

## Next Steps

### For Development:

1. **Set up Database**
   ```bash
   # Install PostgreSQL
   # Create database
   createdb astronexus
   
   # Run migrations (when you create them)
   alembic upgrade head
   ```

2. **Set up Redis**
   ```bash
   # Install Redis
   # On macOS: brew install redis
   # On Ubuntu: sudo apt-get install redis-server
   
   # Start Redis
   redis-server
   ```

3. **Create Database Models**
   - User model
   - Chart model
   - Report model
   - Subscription model

4. **Implement Authentication**
   - JWT token generation
   - User registration/login
   - Protected routes

### For Production:

1. **Security**
   - Use strong SECRET_KEY
   - Enable HTTPS
   - Configure CORS properly
   - Set up rate limiting

2. **Deployment**
   - Choose cloud provider (AWS, GCP, Azure, Heroku)
   - Set up CI/CD pipeline
   - Configure environment variables
   - Set up monitoring (Sentry, DataDog)

3. **Scaling**
   - Database connection pooling
   - Redis caching strategy
   - Load balancing
   - API rate limiting

---

## Development Workflow

### Daily Development:

```bash
# 1. Activate virtual environment
source venv/bin/activate

# 2. Pull latest changes (if using git)
git pull

# 3. Install any new dependencies
pip install -r requirements.txt

# 4. Run development server
python mati_api.py

# 5. Test your changes
pytest

# 6. Format code
black .

# 7. Check for issues
flake8 .
```

### Before Committing:

```bash
# Format code
black *.py

# Run linter
flake8 *.py

# Run tests
pytest

# Commit changes
git add .
git commit -m "Your commit message"
git push
```

---

## Testing Examples

### Using Python Requests:

```python
import requests
import json

# Base URL
BASE_URL = "http://localhost:8000/api/v1"

# Test birth chart calculation
birth_data = {
    "birth_data": {
        "date": "1990-05-15",
        "time": "14:30",
        "latitude": 28.6139,
        "longitude": 77.2090,
        "timezone_offset": 5.5,
        "location_name": "New Delhi, India"
    },
    "include_analysis": True,
    "include_yogas": True
}

response = requests.post(f"{BASE_URL}/chart/calculate", json=birth_data)
print(json.dumps(response.json(), indent=2))
```

### Using httpie:

```bash
# Install httpie
pip install httpie

# Make requests
http POST localhost:8000/api/v1/chart/calculate \
  birth_data:='{"date":"1990-05-15","time":"14:30","latitude":28.6139,"longitude":77.2090,"timezone_offset":5.5}' \
  include_analysis:=true \
  include_yogas:=true
```

---

## Resources

### Documentation:
- **FastAPI**: https://fastapi.tiangolo.com/
- **Swiss Ephemeris**: https://www.astro.com/swisseph/
- **Anthropic API**: https://docs.anthropic.com/
- **Pydantic**: https://docs.pydantic.dev/

### Learning:
- **Vedic Astrology**: "Light on Life" by Hart de Fouw
- **Western Astrology**: "The Inner Sky" by Steven Forrest
- **API Design**: "Designing Web APIs" by Brenda Jin

### Tools:
- **API Testing**: Postman (https://www.postman.com/)
- **Database GUI**: pgAdmin (https://www.pgadmin.org/)
- **Redis GUI**: Redis Commander

---

## Support

If you encounter issues:

1. Check this guide first
2. Review API documentation at `/docs`
3. Check the error logs
4. Search for similar issues online

For Mati development questions, create detailed issue reports including:
- What you were trying to do
- What you expected to happen
- What actually happened
- Error messages (full stack trace)
- Your environment (OS, Python version)

---

## License

This is proprietary software for AstroNexus. All rights reserved.

---

**Happy Coding! 🌟**

Remember: You're building something that will help people understand themselves and navigate life better. That's meaningful work!
