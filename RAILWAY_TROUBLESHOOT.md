# Railway "Not Found" Error - Troubleshooting

## Immediate Steps

### 1. Check Railway Logs (MOST IMPORTANT!)
1. Go to Railway dashboard
2. Click on your **API service** (not MySQL)
3. Click **Deployments** tab
4. Click on the **latest deployment**
5. Click **View Logs**
6. **Look for red error messages**

Common errors you might see:
- `ModuleNotFoundError` → Missing dependency
- `Connection refused` → Database not connected
- `Table doesn't exist` → Database tables not created
- `Port already in use` → Port conflict

### 2. Verify Environment Variables

Go to your **API service** → **Variables** tab

**Required variables:**
```
DB_HOST=${{MySQL.MYSQLHOST}}
DB_PORT=${{MySQL.MYSQLPORT}}
DB_USER=${{MySQL.MYSQLUSER}}
DB_PASSWORD=${{MySQL.MYSQLPASSWORD}}
DB_NAME=${{MySQL.MYSQLDATABASE}}
ALLOWED_ORIGINS=*
PORT=8000
```

**How to add:**
1. Click "+ New Variable"
2. For database vars, use "Shared Variable" button (two arrows)
3. Select MySQL service
4. Choose the variable (e.g., MYSQLHOST)
5. Name it as `DB_HOST` (not MYSQLHOST)

### 3. Check Start Command

Railway → Your API Service → Settings → Deploy

**Start Command should be:**
```
python -m uvicorn api:app --host 0.0.0.0 --port $PORT
```

Or Railway should auto-detect from `Procfile`.

### 4. Verify Database Tables Exist

1. Go to Railway → MySQL service
2. Click **Connect** or use Railway's database console
3. Run this SQL:

```sql
CREATE DATABASE IF NOT EXISTS smartplanner;
USE smartplanner;

CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(20) DEFAULT 'user',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

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

-- Create default user
INSERT INTO users (id, username, password_hash) 
VALUES (1, 'default', 'default_hash')
ON DUPLICATE KEY UPDATE username=username;
```

### 5. Test Database Connection

In Railway logs, you should see the API starting. If you see database errors, the connection string is wrong.

### 6. Common Fixes

**If logs show "Module not found":**
- Make sure `requirements.txt` is in the repo
- Railway should auto-install dependencies

**If logs show database connection errors:**
- Verify all DB_* variables are set
- Check variable names match (DB_HOST not MYSQLHOST)
- Test connection from Railway's database console

**If service keeps crashing:**
- Check if tables exist in database
- Verify default user exists (id=1)
- Check Railway logs for specific error

### 7. Manual Redeploy

After fixing variables:
1. Railway → Your Service → Deployments
2. Click **Redeploy** button
3. Wait 2-3 minutes
4. Check logs again

## Quick Test

Once deployed, test:
```
https://your-app.up.railway.app/
```

Should return: `{"status":"ok","message":"API is running"}`

If you still get "Not Found", check the logs - they will tell you exactly what's wrong!
