# Railway Deployment Fix

## The "Not Found" Error

If you see Railway's "Not Found" page, it means the service isn't starting correctly.

## Quick Fixes

### 1. Check Railway Logs
- Go to Railway dashboard
- Click on your service
- Go to **Deployments** tab
- Click on the latest deployment
- Click **View Logs**
- Look for error messages

### 2. Common Issues & Solutions

#### Issue: "Module not found" or Import errors
**Fix**: Make sure `requirements.txt` includes all dependencies:
```txt
fastapi==0.128.3
uvicorn==0.40.0
mysql-connector-python==9.5.0
pydantic==2.12.5
```

#### Issue: Database connection errors
**Fix**: Verify environment variables are set:
- Railway → Your Service → Variables
- Make sure all DB_* variables are set
- Use Railway's MySQL service variables:
  ```
  DB_HOST=${{MySQL.MYSQLHOST}}
  DB_PORT=${{MySQL.MYSQLPORT}}
  DB_USER=${{MySQL.MYSQLUSER}}
  DB_PASSWORD=${{MySQL.MYSQLPASSWORD}}
  DB_NAME=${{MySQL.MYSQLDATABASE}}
  ```

#### Issue: Port binding errors
**Fix**: Make sure start command uses `$PORT`:
```
uvicorn api:app --host 0.0.0.0 --port $PORT
```

#### Issue: Service crashes on startup
**Fix**: Check if database tables exist:
- Connect to Railway MySQL
- Run SQL from `DEPLOYMENT.md` to create tables

### 3. Manual Start Command Test

In Railway, try setting a custom start command:
- Service → Settings → Deploy
- Start Command: `uvicorn api:app --host 0.0.0.0 --port $PORT`

### 4. Verify Files Are Pushed

Make sure these files are in your GitHub repo:
- ✅ `api.py`
- ✅ `db.py`
- ✅ `requirements.txt`
- ✅ `Procfile` or `railway.toml`

### 5. Re-deploy

After fixing issues:
1. Push changes to GitHub
2. Railway will auto-redeploy
3. Or manually trigger: Service → Deployments → Redeploy

## Test Your Deployment

Once deployed, test:
```
https://your-app.up.railway.app/
```
Should return: `{"status":"ok","message":"API is running"}`

## Still Not Working?

1. Check Railway logs (most important!)
2. Verify all environment variables
3. Test database connection
4. Make sure Python version matches (3.13)
5. Check if `api.py` has syntax errors
