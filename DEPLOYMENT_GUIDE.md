# Deployment Guide

This guide outlines the steps to deploy your application using a hybrid approach: **Vercel** for the Frontend and **Render** for the Backend.

> [!IMPORTANT]
> **Why Hybrid?**
> The backend uses heavy AI libraries (PyTorch, Transformers) which exceed Vercel's 250MB serverless function limit. Render is better suited for these heavy workloads.

## 1. Backend Deployment (Render)

1.  **Push your code** to GitHub.
2.  Log in to [Render](https://render.com/).
3.  Click **New +** -> **Web Service**.
4.  Connect your GitHub repository.
5.  **Configuration**:
    *   **Name**: `your-app-name`
    *   **Region**: Choose one close to you.
    *   **Branch**: `main` (or your working branch)
    *   **Root Directory**: `.` (leave empty)
    *   **Runtime**: `Python 3`
    *   **Build Command**: `pip install -r requirements.txt`
    *   **Start Command**: `gunicorn wsgi:app`
6.  **Environment Variables**:
    Add the following variables in the "Environment" tab:
    *   `PYTHON_VERSION`: `3.11.0` (or your local version)
    *   `GOOGLE_API_KEY`: (Your Google API Key)
    *   `OPENAI_API_KEY`: (Your OpenAI API Key)
    *   `SMTP_SERVER`: `smtp.gmail.com`
    *   `SMTP_PORT`: `587`
    *   `SENDER_EMAIL`: (Your email)
    *   `SENDER_PASSWORD`: (Your app password)
    *   `GOOGLE_CLIENT_ID`: (For OAuth)
    *   `GOOGLE_CLIENT_SECRET`: (For OAuth)
    *   `GOOGLE_CREDENTIALS_JSON`: (Content of your `credentials.json` if needed)
    *   `GOOGLE_TOKEN_JSON`: (Content of your `token.json` if needed)

7.  Click **Create Web Service**.
8.  **Wait for deployment**. Once live, copy your **Render URL** (e.g., `https://your-app.onrender.com`).

## 2. Frontend Deployment (Vercel)

1.  Log in to [Vercel](https://vercel.com/).
2.  Click **Add New...** -> **Project**.
3.  Import your GitHub repository.
4.  **Configure Project**:
    *   **Framework Preset**: Vite (should be auto-detected).
    *   **Root Directory**: Click `Edit` and select `front`.
5.  **Environment Variables**:
    Add the following variables, replacing `https://your-app.onrender.com` with your actual Render URL:
    
    | Variable Name | Value |
    | :--- | :--- |
    | `VITE_API_URL` | `https://your-app.onrender.com` |
    | `VITE_SHORTLISTING_API_URL` | `https://your-app.onrender.com` |
    | `VITE_INTERVIEW_API_URL` | `https://your-app.onrender.com` |
    | `VITE_SETTINGS_API_URL` | `https://your-app.onrender.com` |
    | `VITE_CORE_API_BASE_URL` | `https://your-app.onrender.com` |

6.  Click **Deploy**.

## 3. Troubleshooting

### CORS Errors / 404 Not Found
If you see CORS errors or 404 errors for `/notifications` or `/tests`:
1.  **Redeploy the Frontend** on Vercel. I have updated the code (`apiConfig.js`) to automatically handle the API path prefixes.
2.  Ensure you have redeployed the **Backend** on Render after the latest code changes.
3.  The backend is now configured to allow requests from any origin (`*`) with all headers allowed.

## 4. Verification

1.  Open your Vercel URL.
2.  Try logging in or performing an action.
3.  Check the Network tab in Developer Tools to ensure requests are going to your Render URL.
