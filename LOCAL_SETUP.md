# Local Testing Setup Guide

This guide will help you test the AI RFP Bidder project locally on your machine with the new Groq LLM integration (`llama-3.1-70b-versatile`).

## Prerequisites
- Python 3.11+
- Docker and Docker Compose (Desktop)
- A free [Groq API Key](https://console.groq.com/keys)

## Environment Configuration
1. Open the `.env` file in the root directory.
2. Add your Groq API key:
   ```env
   GROQ_API_KEY=your_groq_api_key_here
   ```

## Running the Application Locally (Using Docker)

The easiest way to set up the entire stack (PostgreSQL, Redis, FastAPI Backend, Celery) is using Docker Compose.

1. Open your terminal in the root project directory.
2. Run the following command:
   ```bash
   docker-compose up --build
   ```
3. The API and Web Dashboard will now be available at `http://localhost:8000`. You can also access the interactive API docs at `http://localhost:8000/docs`.

## Running the Application Locally (Without Docker)

If you only want to run the backend without setting up Docker, you'll need to run Postgres and Redis manually.

1. Navigate to the project root directory:
2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   .\venv\Scripts\activate
   ```
3. Install the dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Start the FastAPI server:
   ```bash
   uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
   ```

## Web Dashboard & Frontend
The frontend dashboard is directly mounted and served by FastAPI at `http://localhost:8000`. You can upload RFPs, watch real-time multi-agent streaming analysis, and export proposals directly from your browser.

