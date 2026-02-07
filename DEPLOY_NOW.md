# 🚀 Deploy to Production - Quick Guide

## Step 1: Deploy Backend to Railway (5 minutes)

1. **Go to Railway**: https://railway.app
2. **Sign up/Login** (free tier available)
3. **New Project** → **Deploy from GitHub repo**
   - Connect your GitHub account
   - Select your repository
   - Railway will auto-detect Python

4. **Add MySQL Database**:
   - In Railway dashboard → **New** → **Database** → **MySQL**
   - Railway will create a MySQL instance

5. **Set Environment Variables**:
   - Go to your service → **Variables** tab
   - Add these (Railway provides DB values automatically):
     ```
     DB_HOST=${{MySQL.MYSQLHOST}}
     DB_PORT=${{MySQL.MYSQLPORT}}
     DB_USER=${{MySQL.MYSQLUSER}}
     DB_PASSWORD=${{MySQL.MYSQLPASSWORD}}
     DB_NAME=${{MySQL.MYSQLDATABASE}}
     ALLOWED_ORIGINS=*
     PORT=8000
     ```

6. **Deploy**:
   - Railway auto-deploys when you push to GitHub
   - Or click **Deploy** button
   - Wait for deployment (2-3 minutes)

7. **Get Your Backend URL**:
   - Railway gives you a URL like: `https://your-app-name.up.railway.app`
   - Copy this URL! You'll need it for the frontend

8. **Setup Database**:
   - Go to Railway → Your MySQL service → **Connect**
   - Use the connection details to connect via DBeaver or Railway's web console
   - Run the SQL from `DEPLOYMENT.md` to create tables

## Step 2: Deploy Frontend to Vercel (3 minutes)

1. **Update config.js**:
   - Open `public/config.js`
   - Set your Railway URL:
     ```javascript
     window.API_BASE_URL = 'https://your-app-name.up.railway.app';
     ```
   - Save and commit to GitHub

2. **Go to Vercel**: https://vercel.com
3. **Sign up/Login** (free tier available)
4. **New Project** → **Import Git Repository**
   - Connect GitHub
   - Select your repository
   - Vercel auto-detects settings

5. **Configure**:
   - **Root Directory**: `smartplanner` (if repo is in subfolder)
   - **Build Command**: (leave empty - static site)
   - **Output Directory**: `public`

6. **Deploy**:
   - Click **Deploy**
   - Wait 1-2 minutes
   - Vercel gives you a URL like: `https://your-app.vercel.app`

7. **Update CORS in Railway**:
   - Go back to Railway → Your service → Variables
   - Update `ALLOWED_ORIGINS`:
     ```
     ALLOWED_ORIGINS=https://your-app.vercel.app
     ```
   - Railway will auto-redeploy

## Step 3: Test Your Live Site! 🎉

1. Open your Vercel URL: `https://your-app.vercel.app`
2. Try adding a task
3. Check the schedule
4. Share the URL with anyone in the world!

## Important Files Structure

```
smartplanner/
├── public/
│   ├── index.html      # Main app (for Vercel)
│   └── config.js       # API URL config
├── api.py              # Backend (for Railway)
├── db.py               # Database connection
├── requirements.txt    # Python dependencies
├── Procfile            # Railway start command
└── vercel.json         # Vercel config
```

## Troubleshooting

### Backend not working?
- Check Railway logs: Service → **Deployments** → Click latest → **View Logs**
- Verify environment variables are set
- Test API: `https://your-app.up.railway.app/` should return `{"status":"ok"}`

### Frontend can't connect?
- Check browser console (F12) for errors
- Verify `config.js` has correct Railway URL
- Check CORS: `ALLOWED_ORIGINS` in Railway should include Vercel URL

### Database issues?
- Verify tables exist (run SQL from DEPLOYMENT.md)
- Check connection string in Railway variables
- Test connection from Railway's database console

## Your URLs

After deployment, you'll have:
- **Frontend**: `https://your-app.vercel.app` (public, shareable)
- **Backend**: `https://your-app.up.railway.app` (API only)

Both are accessible from anywhere in the world! 🌍
