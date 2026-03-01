# 🎤 SMART RECRUITER ASSISTANT

An AI-powered mock interview platform that simulates real interview environments with real-time voice interaction, resume-based questioning, and intelligent feedback.

This system helps users practice technical and behavioral interviews using AI-driven question generation and live audio communication.

---

## 📌 Table of Contents

- About
- Features
- Tech Stack
- Architecture
- Getting Started
- Environment Variables
- Folder Structure
- Future Improvements
- Contributing
- License

---

## 🔍 About

SRA is a full-stack platform that allows users to:

- Upload resumes
- Generate AI-based interview questions
- Attend real-time mock interviews
- Communicate via live audio
- Receive AI-based feedback

The goal is to simulate real-world interview scenarios and help users improve confidence, clarity, and technical knowledge.

---

## 🚀 Features

✔️ Resume-based question generation  
✔️ AI-generated technical & behavioral questions  
✔️ Real-time audio interview using LiveKit  
✔️ Secure authentication  
✔️ Interview session tracking  
✔️ Feedback generation after interview  
✔️ Modern responsive UI  

---

## ⚙️ Tech Stack

### 🖥️ Frontend
- React.js  
- Tailwind CSS  
- Axios  

### 🧠 Backend
- FastAPI  
- Python  

### 🗄️ Database
- Supabase (PostgreSQL)  

### 🎙️ Real-Time Communication
- LiveKit (WebRTC-based real-time audio/video infrastructure)

### 🤖 AI Integration
- Gemini / OpenAI API (for question generation & feedback)
- RAG (Retrieval-Augmented Generation) for resume-based questioning

---

## 🏗️ Architecture Overview
User → React Frontend → FastAPI Backend → Supabase DB
↓
AI Model (Gemini/OpenAI)
↓
LiveKit Server (Real-time audio)

- Frontend handles UI and LiveKit client connection
- Backend handles authentication, resume processing, and AI calls
- Supabase manages user data and interview records
- LiveKit manages real-time voice interaction during interview sessions

---

## 🛠️ Getting Started

### 📌 Prerequisites

Make sure you have:

- Python 3.9+
- Node.js 18+
- Supabase project
- LiveKit server (cloud or self-hosted)
- AI API key (Gemini/OpenAI)

---
🎙️ LiveKit – Real-Time Interview Engine

We use LiveKit to power real-time voice-based AI interviews in SMART Recruiter Assistant.

🔹 Why LiveKit?

WebRTC-based ultra-low latency communication

Secure token-based authentication

Scalable real-time infrastructure

Cloud-hosted or self-hosted deployment support

Seamless integration with React frontend

🔹 Role in Our System

LiveKit enables:

🎤 Real-time AI voice interviews

🔐 Secure interview room creation

👥 Candidate participation via unique access tokens

⚡ Low-latency two-way audio streaming

🔹 How It Works

Backend (FastAPI) generates a LiveKit access token.

Frontend connects using LiveKit Client SDK.

Candidate joins a secure interview room.

AI interviewer communicates in real-time.

Session data and transcripts are stored in Supabase.
