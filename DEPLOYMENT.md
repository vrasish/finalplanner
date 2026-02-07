# Deployment Guide

## Backend Deployment (Railway)

### Prerequisites
1. Railway account (https://railway.app)
2. MySQL database (can use Railway's MySQL service or external)

### Steps

1. **Install Railway CLI** (optional):
   ```bash
   npm i -g @railway/cli
   railway login
   ```

2. **Create a new Railway project**:
   - Go to https://railway.app
   - Click "New Project"
   - Select "Deploy from GitHub repo" or "Empty Project"

3. **Add MySQL Database**:
   - In Railway dashboard, click "New" → "Database" → "MySQL"
   - Railway will provide connection details

4. **Set Environment Variables** in Railway:
   - Go to your service → Variables
   - Add these variables:
     ```
     DB_HOST=<your-mysql-host>
     DB_PORT=3306
     DB_USER=<your-mysql-user>
     DB_PASSWORD=<your-mysql-password>
     DB_NAME=smartplanner
     ALLOWED_ORIGINS=https://your-vercel-app.vercel.app
     PORT=8000
     ```

5. **Deploy**:
   - If using GitHub: Push your code, Railway auto-deploys
   - If using CLI:
     ```bash
     railway init
     railway up
     ```

6. **Get your Railway URL**:
   - Railway will provide a URL like: `https://your-app.up.railway.app`
   - Copy this URL for frontend configuration

### Database Setup on Railway

1. Connect to your Railway MySQL database
2. Run these SQL commands:
   ```sql
   CREATE DATABASE IF NOT EXISTS smartplanner;
   USE smartplanner;
   
   CREATE TABLE IF NOT EXISTS tasks (
       id INT AUTO_INCREMENT PRIMARY KEY,
       user_id INT NOT NULL,
       title TEXT,
       deadline DATE,
       duration_minutes INT,
       priority INT,
       status TEXT DEFAULT 'pending',
       created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
       category VARCHAR(50) DEFAULT 'General',
       completed_at TIMESTAMP NULL,
       FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
   );
   
   CREATE TABLE IF NOT EXISTS daily_plan (
       id INT AUTO_INCREMENT PRIMARY KEY,
       user_id INT NOT NULL,
       task_id INT,
       plan_date DATE,
       scheduled_time TIME,
       task_order INT,
       FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE,
       FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
   );
   
   CREATE TABLE IF NOT EXISTS users (
       id INT AUTO_INCREMENT PRIMARY KEY,
       username VARCHAR(50) NOT NULL UNIQUE,
       password_hash VARCHAR(255) NOT NULL,
       role VARCHAR(20) DEFAULT 'user',
       created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
   );
   
   -- Create a default user
   INSERT INTO users (id, username, password_hash) 
   VALUES (1, 'default', 'default_hash')
   ON DUPLICATE KEY UPDATE username=username;
   ```

## Frontend Deployment (Vercel)

### Prerequisites
1. Vercel account (https://vercel.com)
2. GitHub account (recommended)

### Steps

1. **Prepare your code**:
   - Make sure `index.html` is in the root
   - The `vercel.json` is already configured

2. **Update API URL**:
   - Create a file `config.js` in the root:
   ```javascript
   window.API_BASE_URL = 'https://your-railway-app.up.railway.app';
   ```
   - Add this before the main script in `index.html`:
   ```html
   <script src="config.js"></script>
   ```

3. **Deploy to Vercel**:
   - Option A: Via GitHub
     - Push code to GitHub
     - Go to https://vercel.com
     - Click "New Project"
     - Import your GitHub repo
     - Vercel will auto-detect and deploy
   
   - Option B: Via Vercel CLI
     ```bash
     npm i -g vercel
     vercel login
     vercel
     ```

4. **Set Environment Variables** (if needed):
   - In Vercel dashboard → Project Settings → Environment Variables
   - Add: `API_BASE_URL=https://your-railway-app.up.railway.app`

5. **Update CORS in Railway**:
   - Go back to Railway
   - Update `ALLOWED_ORIGINS` to include your Vercel URL:
     ```
     ALLOWED_ORIGINS=https://your-app.vercel.app,https://your-app.vercel.app
     ```

## Post-Deployment Checklist

- [ ] Backend is accessible at Railway URL
- [ ] Frontend is accessible at Vercel URL
- [ ] Database is connected and tables exist
- [ ] CORS is configured correctly
- [ ] Environment variables are set
- [ ] Test adding a task
- [ ] Test viewing schedule
- [ ] Test on mobile device

## Troubleshooting

### Backend Issues
- Check Railway logs: `railway logs`
- Verify environment variables are set
- Test database connection
- Check CORS settings

### Frontend Issues
- Check browser console for errors
- Verify API_BASE_URL is correct
- Check CORS errors
- Verify Vercel deployment logs

### Database Issues
- Verify connection string
- Check if tables exist
- Verify user permissions
- Test connection from Railway logs
