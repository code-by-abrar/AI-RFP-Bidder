# 🚀 Nexus Bids AI — Autonomous Multi-Agent RFP Bidder & Proposal Engine

<div align="center">

[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-009688.svg?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Python](https://img.shields.io/badge/Python-3.11+-3776AB.svg?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Groq LLaMA 3.3](https://img.shields.io/badge/LLM-Groq%20LLaMA%203.3%2070B-F55036.svg?style=for-the-badge&logo=groq&logoColor=white)](https://groq.com)
[![ChromaDB](https://img.shields.io/badge/Vector_DB-ChromaDB-FC521F.svg?style=for-the-badge)](https://www.trychroma.com)
[![Docker](https://img.shields.io/badge/Docker-Enabled-2496ED.svg?style=for-the-badge&logo=docker&logoColor=white)](https://www.docker.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge)](LICENSE)

<br/>

**Transform complex Request for Proposals (RFPs) into winning, enterprise-grade technical proposals in minutes instead of weeks.**

[🎬 Watch Live Video Demo on LinkedIn](https://lnkd.in/p/dJiyAv-5) • [Key Features](#-key-features) • [Multi-Agent Architecture](#-multi-agent-orchestration-pipeline) • [Quick Start](#-quick-start) • [API Documentation](#-api-endpoints)

</div>

---

## 🌟 Live Demo & Presentation

> 💡 **See Nexus Bids AI in action!** Watch the complete end-to-end walkthrough showing real-time RFP parsing, Go/No-Go evaluation, RAG search, estimation, and automated document generation:
>
> 🔗 **[Click here to watch the demo on LinkedIn](https://lnkd.in/p/dJiyAv-5)**

---

## 📌 Overview

**Nexus Bids AI** is an enterprise-grade, autonomous **Multi-Agent AI System** designed to automate the entire RFP lifecycle for software development firms, IT consultancies, and digital agencies. 

By coordinating an ensemble of specialized AI agents powered by **Groq LLaMA 3.3 (70B)** and a domain-specific **RAG (Retrieval-Augmented Generation)** knowledge base, Nexus Bids AI extracts requirements, calculates win-probability, retrieves institutional knowledge, drafts technical architectures, computes realistic cost/timeline estimates, assesses legal liabilities, and compiles ready-to-send **Microsoft Word (.docx)** proposals.

```
                      ┌─────────────────────────────────────────┐
                      │             Incoming RFP Document       │
                      │               (PDF / DOCX / TXT)        │
                      └────────────────────┬────────────────────┘
                                           │
                                           ▼
                      ┌─────────────────────────────────────────┐
                      │       Phase 1: Parse & Feasibility       │
                      │  [Agent 1: Parser] ──► [Agent 0: Go/No-Go]│
                      └────────────────────┬────────────────────┘
                                           │ (Decision: GO)
                                           ▼
                      ┌─────────────────────────────────────────┐
                      │       Phase 2: Proposal Synthesis       │
                      │  ┌───────────────────────────────────┐  │
                      │  │ Agent 2: RAG Knowledge Retriever  │  │
                      │  │ Agent 3: Technical Proposal Gen   │  │
                      │  │ Agent 4: Cost & Effort Estimator  │  │
                      │  │ Agent 5: Legal & Compliance Audit │  │
                      │  │ Agent 6: Team Allocation Engine   │  │
                      │  └───────────────────────────────────┘  │
                      └────────────────────┬────────────────────┘
                                           │
                                           ▼
                      ┌─────────────────────────────────────────┐
                      │    Output: Professional Proposal (.docx)│
                      │  + Interactive Analytics Dashboard & UI │
                      └─────────────────────────────────────────┘
```

---

## 🤖 Multi-Agent Orchestration Pipeline

The core intelligence is powered by an orchestrator managing **8 specialized AI agents**:

| Agent | Name | Role & Functionality |
| :--- | :--- | :--- |
| **Agent 0** | **Go / No-Go Decision Engine** | Analyzes budget feasibility, timeline realism, technical alignment, and risk factors to calculate a win-probability score before committing company resources. |
| **Agent 1** | **Deep RFP Parser** | Ingests complex multi-page PDFs/DOCX files, extracting structured project scope, must-have/nice-to-have features, tech requirements, and constraints into validated schemas. |
| **Agent 2** | **RAG Historical Retriever** | Embeds queries using `Sentence Transformers` and searches ChromaDB for past winning bids, past project case studies, velocity metrics, and historical challenges. |
| **Agent 3** | **Technical Proposal Generator** | Synthesizes system architecture, recommended tech stacks, database design, API integrations, and development methodologies tailored specifically to the client's RFP. |
| **Agent 4** | **Cost & Effort Estimator** | Breaks projects down into phases (Discovery, Design, Implementation, QA, Deployment), calculating granular work hours, milestones, team costs, and contingency margins. |
| **Agent 5** | **Legal & Compliance Auditor** | Flags legal liabilities, SLA penalties, IP ownership conflicts, GDPR/HIPAA/SOC2 compliance mandates, and drafted standard vendor warranties. |
| **Agent 6** | **Team & Resource Allocator** | Maps project tech stack to available internal engineer profiles, balancing seniority levels, hourly rates, and capacity to form the optimal project squad. |
| **Agent 7** | **Questionnaire Auto-Filler** | Automatically answers vendor qualification questionnaires, security compliance checklists, and RFP tabular question sheets using knowledge base embeddings. |

---

## ⚡ Key Features

- **🚀 Real-Time Streaming Execution (`NDJSON`)**: The frontend streams live status updates, thought steps, and intermediate agent decisions as they happen.
- **⚡ Ultra-Fast Inference with Groq Cloud**: Employs `llama-3.3-70b-versatile` running on Groq LPUs for near-instant response generation.
- **📚 Institutional Knowledge Base (RAG)**: Integrates ChromaDB vector store so your bids automatically reference past company wins, case studies, and engineering capabilities.
- **📄 Instant One-Click Word (.docx) Export**: Formats all generated sections into an executive-ready proposal document complete with tables, scope, architecture, and team rosters.
- **📊 Modern Web UI & Dashboard**: Clean interface equipped with dark/light themes, RFP upload widget, analytics, and interactive win-rate tracking.
- **🐳 Enterprise Containerization**: Production-ready `Dockerfile` and `docker-compose.yml` supporting FastAPI, PostgreSQL, Redis, and Celery workers.

---

## 🛠️ Technology Stack

- **Backend**: Python 3.11, [FastAPI](https://fastapi.tiangolo.com/), Pydantic v2, Uvicorn
- **AI & LLM**: [Groq Cloud SDK](https://groq.com/) (`llama-3.3-70b-versatile`), [LangChain](https://www.langchain.com/)
- **Vector Search & RAG**: [ChromaDB](https://www.trychroma.com/), [Sentence Transformers](https://sbert.net/) (`all-MiniLM-L6-v2`)
- **Database & Storage**: PostgreSQL 15, SQLAlchemy 2.0 (Async), Alembic
- **Async Queue & Cache**: Redis 7, Celery 5.3
- **Document Processing**: `pdfplumber`, `pypdf`, `python-docx`, `openpyxl`
- **Frontend**: Vanilla HTML5, Modern CSS Design System (Dark/Light mode), JavaScript (ES6+), FontAwesome

---

## 📂 Project Structure

```text
RFP-Bidder/
├── backend/
│   ├── app/
│   │   ├── agents/               # 8 Autonomous AI Agents & Orchestrator
│   │   │   ├── agent0_go_no_go.py
│   │   │   ├── agent1_rfp_parser.py
│   │   │   ├── agent2_rag_search.py
│   │   │   ├── agent3_tech_proposal.py
│   │   │   ├── agent4_estimation.py
│   │   │   ├── agent5_legal_compliance.py
│   │   │   ├── agent6_team_allocation.py
│   │   │   ├── agent7_questionnaire_filler.py
│   │   │   └── orchestrator.py
│   │   ├── middleware/           # Auth and security handlers
│   │   ├── models/               # SQLAlchemy ORM models (Bid, User, Company, etc.)
│   │   ├── routes/               # API endpoints (RFP, Bid, Analytics, Knowledge)
│   │   ├── services/             # LLM (Groq), Database, and Document Export services
│   │   ├── utils/                # Prompts & system templates
│   │   └── tasks.py              # Celery background workers
│   ├── scripts/                  # DB seeders and testing pipelines
│   └── main.py                   # FastAPI server entry point
├── frontend/                     # Modern responsive dashboard & UI
│   ├── index.html                # Main Dashboard
│   ├── analyze.html              # RFP Upload & Live Streaming Analysis
│   ├── bid.html                  # Bid Review & Word Export
│   ├── dashboard.html            # Analytics & Performance Metrics
│   ├── knowledge.html            # Knowledge Base Management
│   ├── style.css                 # Design System & Theme Engine
│   └── main.js                   # Client-side API & Streaming Controller
├── .env.example                  # Template for environment variables
├── .gitignore                    # Git ignore file
├── docker-compose.yml            # Multi-container orchestration (FastAPI + Postgres + Redis + Celery)
├── dockerfile                    # Docker build specifications
├── requirements.txt              # Pinned & categorized Python dependencies
└── README.md                     # Comprehensive project documentation
```

---

## 🚀 Quick Start

### Option 1: Docker Compose (Recommended)

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/<your-username>/<your-repo-name>.git
   cd <your-repo-name>
   ```

2. **Configure Environment**:
   ```bash
   cp .env.example .env
   ```
   Open `.env` and insert your **Groq API Key** ([get a free key here](https://console.groq.com/keys)):
   ```env
   GROQ_API_KEY=gsk_your_actual_groq_api_key
   ```

3. **Launch the Application**:
   ```bash
   docker-compose up --build
   ```

4. **Access the Application**:
   - 🌐 **Web Dashboard**: `http://localhost:8000`
   - 📖 **Interactive API Docs (Swagger)**: `http://localhost:8000/docs`

---

### Option 2: Local Python Setup (Without Docker)

1. **Create and Activate Virtual Environment**:
   ```bash
   # Windows
   python -m venv venv
   .\venv\Scripts\activate

   # macOS / Linux
   python3 -m venv venv
   source venv/bin/activate
   ```

2. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure `.env`**:
   Create a `.env` file in the project root:
   ```env
   GROQ_API_KEY=your_groq_api_key_here
   DATABASE_URL=postgresql://rfp_user:secure_password@localhost:5432/rfp_bidder
   REDIS_URL=redis://localhost:6379/0
   CELERY_BROKER_URL=redis://localhost:6379/1
   CELERY_RESULT_BACKEND=redis://localhost:6379/2
   CHROMA_DB_PATH=./chroma_db
   ```

4. **Start the FastAPI Server**:
   ```bash
   uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
   ```

5. **Open in Browser**:
   Visit [http://localhost:8000](http://localhost:8000) to start analyzing RFPs.

---

## 📡 API Endpoints

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/api/rfp/analyze` | Uploads RFP PDF/DOCX and streams real-time multi-agent processing (`x-ndjson`). |
| `GET` | `/api/rfp/analysis/{bid_id}` | Retrieves full stored analysis and status of a bid. |
| `POST` | `/api/rfp/continue/{bid_id}` | Continues Phase 2 generation for a project with user confirmation. |
| `GET` | `/api/bids` | Lists all historical and ongoing proposals with filtering. |
| `GET` | `/api/bids/{bid_id}/export/docx` | Generates and downloads the final Microsoft Word proposal. |
| `POST` | `/api/knowledge/upload` | Ingests company case studies and credentials into ChromaDB vector store. |
| `GET` | `/api/analytics/dashboard` | Returns win/loss rates, margin estimates, and agent performance KPIs. |
| `POST` | `/api/questionnaire/fill` | Automatically populates vendor qualification questionnaires. |

---

## 🎯 How to Use

1. **Navigate to Analyze Page**: Go to `/analyze.html` or click **"New Analysis"** in the top navigation.
2. **Upload RFP Document**: Drag and drop your client's RFP file (PDF or DOCX).
3. **Watch Multi-Agent Processing**: Observe live agent status updates as Agent 1 parses requirements and Agent 0 evaluates feasibility.
4. **Review Go / No-Go Decision**: If viable, Phase 2 runs automatically to generate architecture, budget estimates, and team squads.
5. **Download Final Proposal**: Click **"Export Word Document"** to download the polished proposal ready for delivery!

---

## 🤝 Contributing

Contributions, feedback, and feature suggestions are welcome!
1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📄 License

Distributed under the **MIT License**. See `LICENSE` for more information.

---

<div align="center">

Made with ❤️ for AI Engineers, Agency Founders, and Bid Managers.

**[🎬 Check Out the Live Demo on LinkedIn](https://lnkd.in/p/dJiyAv-5)**

</div>
