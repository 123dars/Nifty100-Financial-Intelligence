<div align="center">
  <img src="frontend/public/village-login-bg.png" alt="Village API Platform" width="100%" style="max-height: 300px; object-fit: cover; border-radius: 12px; margin-bottom: 20px;">
  
  <h1>🌟 Village API Platform</h1>
  <p><strong>A unified B2B platform providing structured Indian village and administrative-location data through secure REST APIs and an administrator dashboard.</strong></p>
  
  <p>
    <a href="https://village-api-platform-psi.vercel.app"><strong>🔗 Live Admin Dashboard</strong></a> |
    <a href="https://village-api-backend-07b0.onrender.com/docs"><strong>🔗 Live API Documentation (Swagger)</strong></a>
  </p>
</div>

---

## 🚀 Project Overview

**Village API** is a full-stack platform serving over **564,000+ villages**, 580+ districts, and 30+ states across India. 

The platform combines a **FastAPI** backend, a beautiful **React + TypeScript + Vite** frontend, a scalable **Neon PostgreSQL** database, and secure **Serverless Proxy** routing to provide seamless data access, analytics, and team management tools.

---

## ✨ Key Features

### 📍 Location Hierarchy & Quick Search
- **Navigation:** State -> District -> Sub-district -> Village.
- **Search:** Instant multi-level search across village names/codes, districts, and states.

### 📊 Admin Analytics Dashboard
- Monitor total platform metrics, active users, API request volume, and average response times.
- View real-time "Top States" leaderboards and API request trends.

### 👥 User & API Key Management
- Admins can manage users (approve, suspend, delete) and issue secure API Keys (pk_live_... & sk_live_...).
- Complete rate-limiting, usage tracking, and API secret rotation support.

### 📝 Global Request Logging
- Every programmatic API request made with an API Key is tracked, showing endpoint, status code, execution time (in ms), and IP metadata for billing and security.

---

## 🏗️ Architecture

`mermaid
flowchart TD
    User([Browser Client]) -->|JWT Auth| Vercel(Vercel Frontend)
    Vercel -->|Serverless Proxy + X-API-Key| Render(Render FastAPI Backend)
    Render <-->|SQLAlchemy| DB[(Neon PostgreSQL)]
    Render <-->|Upstash| Redis[(Redis Cache)]
`

> **Security Note:** To prevent exposing the Master API Key in the browser, the React frontend makes requests to a secure **Vercel Serverless Function** (/api/proxy). This proxy attaches the sensitive X-API-Key and X-API-Secret headers before securely forwarding the request to the Render backend!

---

## 🛠️ Technology Stack

| Layer | Technologies |
| --- | --- |
| **Frontend** | React, TypeScript, Vite, Tailwind CSS, Recharts, TanStack Query |
| **Backend** | Python, FastAPI, SQLAlchemy, Uvicorn |
| **Database** | PostgreSQL (NeonDB), Alembic Migrations |
| **Caching/State** | Upstash Redis |
| **Hosting** | Vercel (Frontend + Proxy), Render (Backend) |

---

## 💻 Local Development Setup

### 1. Backend Setup
`ash
cd backend
uv venv
# Windows: .venv\Scripts\activate | Mac/Linux: source .venv/bin/activate
uv sync
`
Create ackend/.env:
`env
DATABASE_URL=postgresql://user:password@host:5432/dbname?sslmode=require
REDIS_URL=rediss://default:password@host:6379
JWT_SECRET=your_jwt_secret_key
`
Run migrations and start:
`ash
alembic upgrade head
uvicorn main:app --reload --port 8000
`

### 2. Frontend Setup
`ash
cd frontend
npm install
`
Create rontend/.env:
`env
VITE_API_BASE_URL=http://localhost:8000/api/v1
VITE_DEMO_EMAIL=admin123@example.com
VITE_DEMO_PASSWORD=admin@123
`
*(In development, the frontend connects directly to localhost:8000. In production on Vercel, it routes through the secure serverless proxy).*

Start the frontend:
`ash
npm run dev
`

---

## ☁️ Production Deployment Checklist

This project is fully configured for cloud deployment. Ensure the following environment variables are set in **Vercel**:
- VILLAGE_API_BASE_URL: The URL of your deployed Render backend (e.g., https://.../api/v1).
- VILLAGE_API_KEY: The Master API Key (generated in the dashboard).
- VILLAGE_API_SECRET: The Master API Secret (generated in the dashboard).

*(If you receive a status 500 error on login in production, verify these three variables are set in Vercel and the deployment has been refreshed!)*

---

## 👥 Team

This project was developed collaboratively:
- **Priya Singh**: Backend development, FastAPI, REST APIs, authentication, backend integration
- **Vinay**: Database & Data engineering, village data preparation/import, PostgreSQL/NeonDB
- **Darshan B**: Frontend development, React dashboard, UI/UX, frontend-backend integration

---

<p align="center"><strong>Village API</strong><br>Rural Data • Secure APIs • Real Impact</p>
