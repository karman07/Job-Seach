# How the Job Matching API Works

This document provides a high-level overview of the architecture, data flow, and core logic of the Job Matching Backend application.

## 🏗️ Architecture Overview

The system follows a **Three-Layer Architecture** designed for scalability and maintainability:

1.  **Presentation Layer (FastAPI)**: Exposes RESTful endpoints for matching resumes, listing jobs, and administrative tasks.
2.  **Business Logic Layer (Services)**: Handles the core logic for job syncing, resume parsing, and AI matching.
3.  **Data Access Layer (Integrations & DB)**: Manages connections to MongoDB Atlas, Adzuna API, and Google Cloud Talent Solution (CTS).

---

## 🔄 Core Workflows

### 1. Job Sourcing & Syncing (The "Daily Refresh")
The application maintains a fresh database of jobs through an automated pipeline:
- **Trigger**: `APScheduler` triggers a sync every day at **3:00 AM UTC**.
- **Fetch**: The `AdzunaClient` pulls the latest job listings (defaulting to the last 30 days) from the Adzuna API.
- **Process**: 
    - Jobs are identified by a unique `adzuna_id`.
    - New jobs are created; existing jobs are updated with fresh details.
    - Jobs older than 30 days are automatically marked as `expired`.
- **Cloud Sync**: Jobs are also uploaded to **Google Cloud Talent Solution** to enable high-quality AI matching.

### 2. AI-Powered Resume Matching
When a user uploads a resume, the system employs a dual-strategy matching engine:

#### **Layer A: Google Cloud Talent Solution (Primary)**
- Uses Google's industry-leading AI to perform semantic searches.
- Understands context, seniority, and related job titles.
- Maps the resume against thousands of jobs in milliseconds.

#### **Layer B: Local RAG Matcher (Fallback)**
If the CTS API is unreachable or rate-limited, the system falls back to a custom **Retrieval-Augmented Generation (RAG)** approach:
- **Keyword Extraction**: Identifies the most important terms in the resume.
- **Skill Matching**: Specifically scans for 100+ technical skills (Python, Cloud, React, etc.).
- **Scoring**: Calculates a relevance score (0.0 to 1.0) based on title match, skill overlap, and overall text similarity.

---

## ⚡ Performance Features

### **Smart Caching**
To reduce API costs and latency:
- Every search is hashed using **SHA256** (based on resume text + filters).
- Results are stored in the `resume_search_cache` collection for **24 hours**.
- Repeat searches for the same resume return results in ~50ms instead of 500ms+.

### **Asynchronous I/O**
- Built entirely on `async/await`.
- Uses `Motor` (async MongoDB driver) to handle high concurrency without blocking the server.

---

## 📁 Key Components

| File Path | Description |
| :--- | :--- |
| `app/main.py` | Application entry point and lifecycle management. |
| `app/api/jobs.py` | API endpoints for search, match, and listing. |
| `app/services/matching_service_mongo.py` | The "Brain"—contains the CTS integration and Local RAG logic. |
| `app/services/job_service_mongo.py` | Manages job CRUD and the Adzuna sync process. |
| `app/integrations/` | Client wrappers for external APIs (Adzuna, Google CTS). |

---

## 🛠️ Tech Stack Recap
- **Backend**: FastAPI (Python)
- **Database**: MongoDB Atlas (NoSQL)
- **AI Matching**: Google Cloud Talent Solution
- **Data Source**: Adzuna API
- **Task Scheduling**: APScheduler
- **Containerization**: Docker & Docker Compose
