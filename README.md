# XOCOA — The AI Chocolate Sommelier

[![XOCOA CI](https://github.com/hrishi-alikatte/xocoa---prototype-/actions/workflows/ci.yml/badge.svg)](https://github.com/hrishi-alikatte/xocoa---prototype-/actions/workflows/ci.yml)
![Docker](https://img.shields.io/badge/docker-%230db7ed.svg?style=flat&logo=docker&logoColor=white)
![Next JS](https://img.shields.io/badge/Next-black?style=flat&logo=next.js&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=flat&logo=fastapi)

**XOCOA** is a production-grade AI recommender system designed to discover artisanal chocolates. It combines deterministic filtering, semantic vector search (MPNet), and an LLM persona to provide expert-level guidance.

---

## 🏗 System Architecture

The system follows a **Distributed Containerized Architecture**:

*   **Frontend (Port 3000):** Next.js 15 application (React). Acts as the user interface and proxies API requests.
*   **Backend (Port 8000):** FastAPI (Python 3.10) service handling:
    *   **Channel A:** Deterministic Filtering (Country, Price, Dietary).
    *   **Channel B:** Semantic Search (FAISS + Embeddings).
    *   **Channel C:** LLM Contextualization (Groq/Llama 3).
*   **Infrastructure:** Docker Compose for orchestration, Nginx for ingress/reverse-proxy.

## 🚀 Quick Start (Local Dev)

### Prerequisites
*   Docker & Docker Compose
*   Groq API Key (for LLM features)

### Running the Full Stack
1.  **Clone the repository:**
    ```bash
    git clone https://github.com/hrishi-alikatte/xocoa---prototype-.git
    cd xocoa---prototype-
    ```

2.  **Configure Environment:**
    Create a `.env` file in the root:
    ```bash
    GROQ_API_KEY=your_api_key_here
    ```

3.  **Launch:**
    ```bash
    docker-compose up --build
    ```

4.  **Access:**
    *   **App:** [http://localhost:3000](http://localhost:3000)
    *   **API Docs:** [http://localhost:8000/docs](http://localhost:8000/docs)

## 🌐 Production Deployment (OVH/VPS)

This project includes a fully automated deployment strategy for VPS environments.

1.  **SSH into your server.**
2.  **Clone the repo and set `.env`.**
3.  **Run the deployment script:**
    ```bash
    chmod +x deploy.sh
    ./deploy.sh
    ```

This triggers the `docker-compose.prod.yml` stack, ensuring Nginx handles traffic on ports 80/443 while isolating the backend.

## 🤖 CI/CD Pipelines

Automated workflows via **GitHub Actions**:
*   **CI (`.github/workflows/ci.yml`):** Runs on every Push/PR.
    *   Executes Backend Unit Tests (`pytest`).
    *   Builds Docker Images to ensure compilation integrity.

## 📂 Project Structure

```text
/
├── .github/workflows/   # CI Pipelines
├── backend/             # FastAPI Application (The Brain)
├── frontend/            # Next.js Application (The Face)
├── infrastructure/      # Nginx & Cloud Configs
├── data/                # Datasets & Embeddings
├── docker-compose.yml   # Dev Orchestration
└── deploy.sh            # Production Launch Script
```

---
