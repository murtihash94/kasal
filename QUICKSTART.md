# Kasal Quick Start Guide - Mac Setup

Get Kasal running on your Mac in just a few minutes! This guide provides the simplest path to running Kasal locally for development and testing.

## Prerequisites

### Required
- **Python 3.9+** - Check your version: `python3 --version`
  - If you need to install or upgrade Python: [python.org/downloads](https://www.python.org/downloads/)

### Optional (for Frontend UI)
- **Node.js 16+** - Check your version: `node --version`
  - If you need Node.js: [nodejs.org](https://nodejs.org/)
- **npm** - Usually comes with Node.js: `npm --version`

> **Note**: The backend can run without Node.js, but you'll need it to build the frontend UI.

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/murtihash94/kasal.git
cd kasal
```

### 2. Run Kasal

That's it! Just run:

```bash
python3 run.py
```

This single command will:
- ✅ Check your Python version
- ✅ Install backend dependencies
- ✅ Build the frontend (if Node.js is available)
- ✅ Start the server

**First Run**: The first time you run this, it will take 3-5 minutes to:
- Install Python packages (FastAPI, SQLAlchemy, CrewAI, etc.)
- Install Node.js packages (React, Material-UI, etc.)
- Build the frontend React application
- Initialize the database

**Subsequent Runs**: After the first run, you can use `--skip-deps` to start faster:
```bash
python3 run.py --skip-deps
```

## Access Kasal

Once started, access Kasal at:

- **Web Interface**: http://127.0.0.1:8000
- **API Documentation**: http://127.0.0.1:8000/api-docs
- **Health Check**: http://127.0.0.1:8000/health

### What Gets Created

When you run Kasal for the first time, it creates:
- `src/backend/app.db` - SQLite database with your workflows and data
- `src/backend/logs/` - Application logs
- `src/frontend_static/` - Built frontend files (if Node.js is available)

These files/directories are already in `.gitignore` and won't be committed.

## Common Options

### Development Mode (Auto-reload on code changes)

```bash
python3 run.py --reload
```

### Run on a Different Port

```bash
python3 run.py --port 9000
```

### Skip Dependency Installation (After First Run)

```bash
python3 run.py --skip-deps
```

### Rebuild Frontend

```bash
python3 run.py --rebuild
```

### Use PostgreSQL Instead of SQLite

```bash
python3 run.py --db-type postgres --db-url "postgresql://user:password@localhost/kasal"
```

## Troubleshooting

### Issue: "Command not found: python3"

**Solution**: Install Python 3.9+ from [python.org](https://www.python.org/downloads/)

### Issue: "Node.js not found"

**Solution**: Either:
- Install Node.js from [nodejs.org](https://nodejs.org/) to get the full UI
- Or continue without it - the backend API will still work

### Issue: Port 8000 is already in use

**Solution**: Use a different port:

```bash
python3 run.py --port 9000
```

### Issue: Permission denied

**Solution**: Make the script executable:

```bash
chmod +x run.py
./run.py
```

### Issue: Dependencies fail to install

**Solution**: Try upgrading pip first:

```bash
python3 -m pip install --upgrade pip
python3 run.py
```

## Next Steps

### 1. Explore the Documentation

- [Complete Documentation](src/docs/) - Architecture, API reference, and guides
- [Getting Started](src/docs/GETTING_STARTED.md) - Detailed setup guide
- [Best Practices](src/docs/BEST_PRACTICES.md) - Development guidelines

### 2. Create Your First Workflow

1. Open the web interface at http://127.0.0.1:8000
2. Click "New Workflow"
3. Drag agents onto the canvas
4. Connect them to create a workflow
5. Configure agent roles and tasks
6. Hit "Run" and watch your AI agents collaborate!

### 3. Configure LLM Providers

Kasal supports multiple LLM providers:
- Databricks (recommended for production)
- OpenAI
- Anthropic
- Local models

See [LLM Manager Documentation](src/docs/LLM_MANAGER.md) for configuration details.

## Advanced Usage

### Custom Database Location

```bash
python3 run.py --db-path /path/to/my/database.db
```

### Skip Frontend Build

```bash
python3 run.py --skip-build
```

### See All Options

```bash
python3 run.py --help
```

## Getting Help

- **Issues**: [GitHub Issues](https://github.com/murtihash94/kasal/issues)
- **Documentation**: [src/docs/](src/docs/)
- **Security**: [SECURITY.md](SECURITY.md)

## Quick Reference

| Command | Description |
|---------|-------------|
| `python3 run.py` | Start Kasal with default settings |
| `python3 run.py --reload` | Start with auto-reload for development |
| `python3 run.py --port 9000` | Start on port 9000 |
| `python3 run.py --skip-deps` | Skip dependency installation |
| `python3 run.py --rebuild` | Force rebuild frontend |
| `python3 run.py --help` | Show all available options |

---

**That's it!** You now have Kasal running locally on your Mac. Start building intelligent AI agent workflows! 🚀
