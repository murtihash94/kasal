# Getting Started with Kasal

This guide will help you set up and run the Kasal platform on your local machine for development purposes.

## Quick Start

**The fastest way to get started:**

```bash
git clone https://github.com/yourusername/kasal.git
cd kasal
python3 run.py
```

That's it! The script will automatically:
- Check prerequisites
- Install dependencies
- Build the frontend
- Start the server

See [QUICKSTART.md](../../QUICKSTART.md) in the root directory for more details.

## Prerequisites

- **Python 3.9 or higher** for the backend
- **Node.js 16 or higher** for the frontend (optional, only needed to build UI)

## Project Setup

### Method 1: Simple Python Script (Recommended for Mac/Linux)

Use the `run.py` script in the root directory:

```bash
# Start with default settings (SQLite)
python3 run.py

# Start with auto-reload for development
python3 run.py --reload

# Use a different port
python3 run.py --port 9000

# Use PostgreSQL instead of SQLite
python3 run.py --db-type postgres --db-url "postgresql://user:password@localhost/kasal"

# See all options
python3 run.py --help
```

The application will be available at http://localhost:8000 (or your specified port).

### Method 2: Manual Setup (Original Method)

#### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/kasal.git
cd kasal
```

#### 2. Start the Backend

```bash
cd src/backend
./run.sh
```

#### Database Options

```bash
# For SQLite database (default for development)
./run.sh sqlite

# For PostgreSQL database
./run.sh postgres
```

#### Environment Configuration

Create a `.env` file in the backend directory if needed for custom settings:

- Database settings (SQLite by default for development)
- API keys for any integrated LLM services
- Other environment-specific settings

The backend API will be available at http://localhost:8000.

#### 3. Build and Serve Frontend (Optional - Alternative to Method 1)

If you want to build the production frontend and serve it through the backend:

```bash
# From the root directory
cd src
python3 build.py
```

This builds the frontend and copies it to `frontend_static/`. The backend will automatically serve these static files.

### Method 3: Frontend Development Server (For UI Development)

If you're actively developing the frontend UI, you can run the frontend separately:

```bash
cd src/frontend
npm install
npm start
```

The frontend will be available at http://localhost:3000 and will proxy API requests to http://localhost:8000.

## Documentation

Documentation files are written in Markdown and located in the `docs/` directory.

### Accessing Documentation

- **Project Documentation**: Available in the `docs/` directory

### Editing Documentation

1. Edit any `.md` file in the `docs/` directory
2. Documentation is available both locally and when deployed

## Accessing the Application

Once the backend is running, you can access:

- **Web Interface**: http://localhost:3000 (if frontend is running)
- **Health Check**: http://localhost:8000/health

## Project Structure

### Backend (FastAPI + SQLAlchemy)

```
backend/
├── src/                 # Application source code
│   ├── api/             # API routes and controllers
│   ├── core/            # Core functionality and base classes
│   ├── db/              # Database configuration and models
│   ├── models/          # SQLAlchemy data models
│   ├── repositories/    # Data access layer
│   ├── schemas/         # Pydantic models for validation
│   ├── services/        # Business logic services
│   ├── engines/         # CrewAI integration
│   ├── seeds/           # Database seeders
│   ├── config/          # Configuration management
│   ├── utils/           # Utility functions
│   ├── main.py          # Application entry point
└── tests/               # Test suite
```

### Frontend (for UI deployment only)

```
frontend/
├── src/                 # React application source
│   ├── components/      # UI components
│   ├── api/             # API client services
│   └── ...              # Other frontend files
└── public/              # Static assets
```

## Using Kasal

### Creating Your First Agent Workflow

Use the REST API to create AI agent workflows:

1. Create agents via `POST /api/v1/agents`
2. Define tasks via `POST /api/v1/tasks`
3. Build crews via `POST /api/v1/crews`
4. Configure LLM models and tools

### Running Your Workflow

1. Execute crews via `POST /api/v1/executions`
2. Monitor execution status via `GET /api/v1/executions/{id}`
3. View logs and traces via execution endpoints
4. Access results through the API

## Development Guidelines

- **Backend Development**: Follow the clean architecture pattern with clear separation between layers
- **API Design**: Use RESTful principles for all endpoints
- **Database Changes**: Create migrations using Alembic for any model changes
- **Testing**: Write tests for all new features

## Troubleshooting

### Common Issues

- **Database Errors**: Verify your database configuration in `.env`
- **Connection Refused**: Ensure backend server is running
- **Authentication Errors**: Check API keys and credentials in `.env`
- **API Errors**: Check logs in `backend/logs/` for detailed error information

### Getting Help

If you encounter issues:

1. Check the logs in `backend/logs/`
2. Consult the documentation in the `docs/` directory
3. Check the health endpoint at http://localhost:8000/health

## Next Steps

- Learn about [Kasal Architecture](ARCHITECTURE.md)
- Explore the [CrewAI Engine](CREWAI_ENGINE.md) integration 