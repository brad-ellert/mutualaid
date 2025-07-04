# MutualAid

Give what you can and get what you need.

## 🚀 Tech Stack

- **Backend**: FastAPI (Python 3.9+)
- **Frontend**: Bootstrap 5 + Vite
- **Database**: PostgreSQL
- **Web Server**: Nginx
- **Containerization**: Docker
- **CI/CD**: GitHub Actions

## 🛠️ Development Setup

### Prerequisites

- Python 3.9+
- Node.js 16+
- Docker & Docker Compose
- PostgreSQL (for local development without Docker)

### Quick Start with Docker (Recommended)

1. **Clone the repository**
   ```bash
   git clone https://github.com/brad-ellert/mutualaid.git
   cd mutualaid
   ```

2. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration if needed
   ```

3. **Start the development environment**
   ```bash
   docker-compose up --build
   ```

4. **Access the application**
   - Frontend: http://localhost:3000
   - API Docs: http://localhost:8000/docs
   - Admin User: admin@example.com / admin

### Manual Setup (without Docker)

1. **Set up Python environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: .\venv\Scripts\activate
   pip install -r backend/requirements/dev.txt
   ```

2. **Set up Node.js**
   ```bash
   cd frontend
   npm install
   cd ..
   ```

3. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your database and other settings
   ```

4. **Initialize the database**
   ```bash
   cd backend
   python -m scripts.init_db
   cd ..
   ```

5. **Run the development servers**
   - Backend (in one terminal):
     ```bash
     cd backend
     uvicorn app.main:app --reload
     ```
   - Frontend (in another terminal):
     ```bash
     cd frontend
     npm run dev
     ```

## 🏗️ Project Structure

```
mutualaid/
├── backend/                 # FastAPI application
│   ├── app/                # Application package
│   │   ├── api/            # API routes
│   │   ├── core/           # Core functionality
│   │   ├── crud/           # Database operations
│   │   ├── db/             # Database configuration
│   │   ├── models/         # SQLAlchemy models
│   │   ├── schemas/        # Pydantic models
│   │   └── main.py         # Application entry point
│   ├── scripts/            # Utility scripts
│   └── requirements/       # Python dependencies
│
├── frontend/               # Frontend application
│   ├── public/             # Static files
│   ├── src/                # Source files
│   │   ├── js/             # JavaScript files
│   │   ├── scss/           # Styles
│   │   └── main.js         # Entry point
│   ├── index.html          # Main HTML
│   └── package.json        # Frontend dependencies
│
├── nginx/                  # Nginx configuration
├── scripts/                # Utility scripts
├── .env.example            # Environment variables template
├── docker-compose.yml      # Development environment
└── README.md               # This file
```

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Workflow

- Run tests: `pytest`
- Format code: `black . && isort .`
- Lint code: `flake8`
- Run frontend dev server: `cd frontend && npm run dev`
- Run backend dev server: `uvicorn app.main:app --reload`

## 📄 License

This project is licensed under the [WTFPL](LICENSE) (Do What The Fuck You Want To Public License).
