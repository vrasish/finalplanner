from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from datetime import date, datetime, time, timedelta
import os
from db import get_conn

app = FastAPI()

# Add CORS middleware
allowed_origins_env = os.getenv("ALLOWED_ORIGINS", "*")
if allowed_origins_env == "*":
    allowed_origins = ["*"]
else:
    allowed_origins = [origin.strip() for origin in allowed_origins_env.split(",")]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check endpoint
@app.get("/")
def health_check():
    return {"status": "ok", "message": "API is running"}

# Initialize database endpoint - creates tables if they don't exist
@app.get("/init-db")
@app.post("/init-db")
def init_database():
    """Initialize database tables - run this once after deployment"""
    try:
        conn = get_conn()
        cur = conn.cursor()
        
        # Create users table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                username VARCHAR(50) NOT NULL UNIQUE,
                password_hash VARCHAR(255) NOT NULL,
                role VARCHAR(20) DEFAULT 'user',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create tasks table
        cur.execute("""
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
            )
        """)
        
        # Create daily_plan table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS daily_plan (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                task_id INT,
                plan_date DATE,
                scheduled_time TIME,
                task_order INT,
                FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """)
        
        # Create default user
        cur.execute("""
            INSERT INTO users (id, username, password_hash) 
            VALUES (1, 'default', 'default_hash')
            ON DUPLICATE KEY UPDATE username=username
        """)
        
        conn.commit()
        cur.close()
        conn.close()
        
        return {"message": "Database initialized successfully", "tables_created": True}
    except Exception as e:
        return {"message": f"Error initializing database: {str(e)}", "tables_created": False}

# Helper function to get first available user_id
def get_default_user_id():
    try:
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("SELECT MIN(id) FROM users")
        user_id = cur.fetchone()[0]
        cur.close()
        conn.close()
        return user_id if user_id else 1
    except:
        return 1

# Helper function to check if time is during school hours
def is_school_hours(date_obj: date, time_obj: time) -> bool:
    # School is Monday-Friday, 8 AM - 4 PM
    weekday = date_obj.weekday()  # 0 = Monday, 6 = Sunday
    if weekday >= 5:  # Saturday or Sunday
        return False
    
    hour = time_obj.hour
    return hour >= 8 and hour < 16

# Helper function to find next available time slot
def find_available_slot(cur, date_obj: date, duration: int, start_hour: int = 5):
    """
    Find next available time slot for a task.
    Avoids school hours (Mon-Fri, 8 AM - 4 PM) and existing scheduled tasks.
    """
    # Available hours: 5 AM - 8 AM, 4 PM - 11 PM (avoiding school hours 8 AM - 4 PM)
    available_hours = list(range(5, 8)) + list(range(16, 24))
    
    # Try today first, then next 7 days
    for day_offset in range(8):
        check_date = date_obj + timedelta(days=day_offset)
        weekday = check_date.weekday()
        is_weekend = weekday >= 5
        
        # On weekends, all hours are available (except scheduled tasks)
        if is_weekend:
            hours_to_check = list(range(5, 24))
        else:
            # Weekdays: avoid school hours (8 AM - 4 PM)
            hours_to_check = available_hours
        
        for hour in hours_to_check:
            for minute in [0, 30]:  # Try :00 and :30
                start_time = time(hour, minute)
                start_datetime = datetime.combine(check_date, start_time)
                end_datetime = start_datetime + timedelta(minutes=duration)
                end_time = end_datetime.time()
                
                # Check if this time conflicts with school hours
                if not is_weekend and is_school_hours(check_date, start_time):
                    continue
                
                # Check if end time goes into school hours
                if not is_weekend and is_school_hours(check_date, end_time):
                    continue
                
                # Check if this time conflicts with existing scheduled tasks
                cur.execute("""
                    SELECT d.scheduled_time, t.duration_minutes 
                    FROM daily_plan d
                    JOIN tasks t ON t.id = d.task_id
                    WHERE d.plan_date = %s AND d.scheduled_time IS NOT NULL
                """, (check_date,))
                
                conflicts = False
                for existing_start, existing_duration in cur.fetchall():
                    existing_start_time = existing_start if isinstance(existing_start, time) else datetime.strptime(str(existing_start), '%H:%M:%S').time()
                    existing_start_dt = datetime.combine(check_date, existing_start_time)
                    existing_end_dt = existing_start_dt + timedelta(minutes=existing_duration)
                    
                    # Check for overlap
                    if (start_datetime < existing_end_dt and end_datetime > existing_start_dt):
                        conflicts = True
                        break
                
                if not conflicts:
                    return check_date, start_time
        
        # If we've checked today and it's a weekday, start from 4 PM tomorrow
        if day_offset == 0 and weekday < 5:
            continue
    
    return None, None

# Auto-schedule a task
def auto_schedule_task(cur, conn, task_id: int, user_id: int, due_date_str: str, duration: int, target_date: str = None):
    """Automatically schedule a task in the next available time slot"""
    try:
        due_date = datetime.strptime(due_date_str, '%Y-%m-%d').date()
        today = date.today()
        
        # If target_date is provided, try to schedule on that specific date
        if target_date:
            try:
                target_date_obj = datetime.strptime(target_date, '%Y-%m-%d').date()
                schedule_date, schedule_time = find_available_slot(cur, target_date_obj, duration)
                if schedule_date and schedule_time:
                    # Successfully scheduled on target date
                    cur.execute("DELETE FROM daily_plan WHERE task_id = %s", (task_id,))
                    cur.execute("""
                        INSERT INTO daily_plan (user_id, task_id, plan_date, scheduled_time, task_order) 
                        VALUES (%s, %s, %s, %s, 1)
                    """, (user_id, task_id, schedule_date, schedule_time))
                    conn.commit()
                    return {
                        "scheduled": True,
                        "schedule_date": str(schedule_date),
                        "schedule_time": schedule_time.strftime('%H:%M')
                    }
                else:
                    # Couldn't schedule on target date, fall through to auto-schedule
                    pass
            except:
                # Invalid target date, fall through to auto-schedule
                pass
        
        # Auto-schedule: Start looking from today, but prefer scheduling before due date
        start_date = max(today, due_date - timedelta(days=7)) if due_date > today else today
        
        schedule_date, schedule_time = find_available_slot(cur, start_date, duration)
        
        if schedule_date and schedule_time:
            # Delete any existing schedule for this task
            cur.execute("DELETE FROM daily_plan WHERE task_id = %s", (task_id,))
            
            # Insert new schedule
            cur.execute("""
                INSERT INTO daily_plan (user_id, task_id, plan_date, scheduled_time, task_order) 
                VALUES (%s, %s, %s, %s, 1)
            """, (user_id, task_id, schedule_date, schedule_time))
            
            conn.commit()
            return {
                "scheduled": True,
                "schedule_date": str(schedule_date),
                "schedule_time": schedule_time.strftime('%H:%M')
            }
        else:
            return {"scheduled": False, "message": "No available time slot found"}
    except Exception as e:
        return {"scheduled": False, "message": f"Error scheduling: {str(e)}"}

# Add task (just task name, duration, due date - no scheduling yet)
@app.post("/tasks")
def add_task(title: str, duration: int, due_date: str, schedule_date: str = None, user_id: int = None):
    try:
        if user_id is None:
            user_id = get_default_user_id()
        
        # Parse due date
        try:
            if '/' in due_date:
                parts = due_date.split('/')
                if len(parts) == 3:
                    month, day, year = parts
                    if len(year) == 2:
                        year = '20' + year if int(year) < 50 else '19' + year
                    due_date_str = f"{year}-{month.zfill(2)}-{day.zfill(2)}"
                else:
                    raise ValueError("Invalid date format")
            else:
                due_date_str = due_date
            
            datetime.strptime(due_date_str, '%Y-%m-%d')
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid date format: {due_date}. Use M/D/YY or YYYY-MM-DD")
        
        conn = get_conn()
        cur = conn.cursor()

        cur.execute("SELECT id FROM users WHERE id = %s", (user_id,))
        if not cur.fetchone():
            raise HTTPException(status_code=400, detail=f"User with id {user_id} does not exist")

        cur.execute(
            "INSERT INTO tasks (user_id, title, deadline, duration_minutes, priority, status) VALUES (%s,%s,%s,%s,%s,%s)",
            (user_id, title, due_date_str, duration, 1, 'pending')
        )

        conn.commit()
        task_id = cur.lastrowid
        
        # Parse schedule_date if provided
        target_schedule_date = None
        if schedule_date:
            try:
                if '/' in schedule_date:
                    parts = schedule_date.split('/')
                    if len(parts) == 3:
                        month, day, year = parts
                        if len(year) == 2:
                            year = '20' + year if int(year) < 50 else '19' + year
                        target_schedule_date = f"{year}-{month.zfill(2)}-{day.zfill(2)}"
                    else:
                        target_schedule_date = schedule_date
                else:
                    target_schedule_date = schedule_date
                datetime.strptime(target_schedule_date, '%Y-%m-%d')
            except:
                target_schedule_date = None  # Invalid date, use auto-schedule
        
        # Automatically schedule the task (to specific date if provided)
        schedule_result = auto_schedule_task(cur, conn, task_id, user_id, due_date_str, duration, target_schedule_date)
        
        cur.close()
        conn.close()

        return {
            "message": "Task added and scheduled successfully", 
            "task_id": task_id, 
            "title": title, 
            "duration": duration, 
            "due_date": due_date_str,
            "scheduled": schedule_result["scheduled"],
            "schedule_date": schedule_result.get("schedule_date"),
            "schedule_time": schedule_result.get("schedule_time")
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error adding task: {str(e)}")

# Get all tasks
@app.get("/tasks")
def get_tasks():
    try:
        conn = get_conn()
        cur = conn.cursor()

        cur.execute("SELECT id, title, deadline, duration_minutes, status FROM tasks ORDER BY deadline ASC")
        tasks = cur.fetchall()

        result = []
        for task in tasks:
            result.append({
                "id": task[0],
                "title": task[1],
                "due_date": str(task[2]),
                "duration": task[3],
                "status": task[4]
            })

        cur.close()
        conn.close()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching tasks: {str(e)}")

# Schedule a task to a specific time slot
@app.post("/schedule")
def schedule_task(task_id: int, schedule_date: str, start_time: str):
    try:
        # Parse date and time
        try:
            if '/' in schedule_date:
                parts = schedule_date.split('/')
                if len(parts) == 3:
                    month, day, year = parts
                    if len(year) == 2:
                        year = '20' + year if int(year) < 50 else '19' + year
                    schedule_date_str = f"{year}-{month.zfill(2)}-{day.zfill(2)}"
                else:
                    raise ValueError("Invalid date format")
            else:
                schedule_date_str = schedule_date
            
            schedule_date_obj = datetime.strptime(schedule_date_str, '%Y-%m-%d').date()
            start_time_obj = datetime.strptime(start_time, '%H:%M').time()
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid date/time format: {str(e)}")
        
        conn = get_conn()
        cur = conn.cursor()

        # Check if task exists and get duration
        cur.execute("SELECT id, duration_minutes, user_id FROM tasks WHERE id = %s", (task_id,))
        task = cur.fetchone()
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        
        duration = task[1]
        user_id = task[2]
        
        # Calculate end time
        start_datetime = datetime.combine(schedule_date_obj, start_time_obj)
        end_datetime = start_datetime + timedelta(minutes=duration)
        end_time_obj = end_datetime.time()
        
        # Check for conflicts - get all scheduled tasks for this date
        cur.execute("""
            SELECT d.scheduled_time, t.duration_minutes 
            FROM daily_plan d
            JOIN tasks t ON t.id = d.task_id
            WHERE d.plan_date = %s AND d.scheduled_time IS NOT NULL
        """, (schedule_date_obj,))
        
        existing_schedules = cur.fetchall()
        has_conflict = False
        
        for existing_start, existing_duration in existing_schedules:
            existing_start_time = existing_start if isinstance(existing_start, time) else datetime.strptime(str(existing_start), '%H:%M:%S').time()
            existing_start_dt = datetime.combine(schedule_date_obj, existing_start_time)
            existing_end_dt = existing_start_dt + timedelta(minutes=existing_duration)
            existing_end_time = existing_end_dt.time()
            
            # Check if new task overlaps with existing task
            start_dt = datetime.combine(schedule_date_obj, start_time_obj)
            end_dt = datetime.combine(schedule_date_obj, end_time_obj)
            
            if (start_dt < existing_end_dt and end_dt > existing_start_dt):
                has_conflict = True
                break
        
        if has_conflict:
            raise HTTPException(status_code=400, detail="Time slot conflicts with existing schedule")
        
        # Delete existing schedule for this task if any
        cur.execute("DELETE FROM daily_plan WHERE task_id = %s", (task_id,))
        
        # Insert new schedule
        cur.execute("""
            INSERT INTO daily_plan (user_id, task_id, plan_date, scheduled_time, task_order) 
            VALUES (%s, %s, %s, %s, 1)
        """, (user_id, task_id, schedule_date_obj, start_time_obj))

        conn.commit()
        cur.close()
        conn.close()

        return {"message": "Task scheduled successfully", "start_time": start_time, "end_time": end_time_obj.strftime('%H:%M')}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error scheduling task: {str(e)}")

# Get schedule for a specific date
@app.get("/schedule/{schedule_date}")
def get_schedule(schedule_date: str):
    try:
        try:
            if '/' in schedule_date:
                parts = schedule_date.split('/')
                if len(parts) == 3:
                    month, day, year = parts
                    if len(year) == 2:
                        year = '20' + year if int(year) < 50 else '19' + year
                    schedule_date_str = f"{year}-{month.zfill(2)}-{day.zfill(2)}"
                else:
                    raise ValueError("Invalid date format")
            else:
                schedule_date_str = schedule_date
            
            schedule_date_obj = datetime.strptime(schedule_date_str, '%Y-%m-%d').date()
        except:
            raise HTTPException(status_code=400, detail="Invalid date format. Use M/D/YY or YYYY-MM-DD")
        
        conn = get_conn()
        cur = conn.cursor()

        cur.execute("""
            SELECT t.id, t.title, d.scheduled_time, t.duration_minutes, t.deadline
            FROM daily_plan d
            JOIN tasks t ON t.id = d.task_id
            WHERE d.plan_date = %s AND d.scheduled_time IS NOT NULL
            ORDER BY d.scheduled_time ASC
        """, (schedule_date_obj,))

        scheduled_tasks = cur.fetchall()
        
        result = []
        for task in scheduled_tasks:
            task_id, title, start_time, duration, deadline = task
            start_time_obj = start_time if isinstance(start_time, time) else datetime.strptime(str(start_time), '%H:%M:%S').time()
            start_datetime = datetime.combine(schedule_date_obj, start_time_obj)
            end_datetime = start_datetime + timedelta(minutes=duration)
            end_time_obj = end_datetime.time()
            
            result.append({
                "task_id": task_id,
                "title": title,
                "start_time": start_time_obj.strftime('%H:%M'),
                "end_time": end_time_obj.strftime('%H:%M'),
                "duration": duration,
                "due_date": str(deadline)
            })

        cur.close()
        conn.close()

        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching schedule: {str(e)}")

# Get weekly schedule
@app.get("/schedule/week/{week_start}")
def get_weekly_schedule(week_start: str):
    try:
        try:
            if '/' in week_start:
                parts = week_start.split('/')
                if len(parts) == 3:
                    month, day, year = parts
                    if len(year) == 2:
                        year = '20' + year if int(year) < 50 else '19' + year
                    week_start_str = f"{year}-{month.zfill(2)}-{day.zfill(2)}"
                else:
                    raise ValueError("Invalid date format")
            else:
                week_start_str = week_start
            
            week_start_obj = datetime.strptime(week_start_str, '%Y-%m-%d').date()
            # Adjust to Monday
            days_since_monday = week_start_obj.weekday()
            monday = week_start_obj - timedelta(days=days_since_monday)
        except:
            raise HTTPException(status_code=400, detail="Invalid date format")
        
        conn = get_conn()
        cur = conn.cursor()

        week_end = monday + timedelta(days=6)
        
        cur.execute("""
            SELECT d.plan_date, t.id, t.title, d.scheduled_time, t.duration_minutes, t.deadline
            FROM daily_plan d
            JOIN tasks t ON t.id = d.task_id
            WHERE d.plan_date >= %s AND d.plan_date <= %s AND d.scheduled_time IS NOT NULL
            ORDER BY d.plan_date ASC, d.scheduled_time ASC
        """, (monday, week_end))

        scheduled_tasks = cur.fetchall()
        
        # Organize by day
        week_schedule = {}
        current_date = monday
        for i in range(7):
            week_schedule[str(current_date)] = []
            current_date += timedelta(days=1)
        
        for task in scheduled_tasks:
            plan_date, task_id, title, start_time, duration, deadline = task
            date_str = str(plan_date)
            
            start_time_obj = start_time if isinstance(start_time, time) else datetime.strptime(str(start_time), '%H:%M:%S').time()
            start_datetime = datetime.combine(plan_date, start_time_obj)
            end_datetime = start_datetime + timedelta(minutes=duration)
            end_time_obj = end_datetime.time()
            
            if date_str in week_schedule:
                week_schedule[date_str].append({
                    "task_id": task_id,
                    "title": title,
                    "start_time": start_time_obj.strftime('%H:%M'),
                    "end_time": end_time_obj.strftime('%H:%M'),
                    "duration": duration,
                    "due_date": str(deadline)
                })

        cur.close()
        conn.close()

        return week_schedule
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching weekly schedule: {str(e)}")

# Delete task
@app.delete("/tasks/{task_id}")
def delete_task(task_id: int):
    try:
        conn = get_conn()
        cur = conn.cursor()

        cur.execute("SELECT id FROM tasks WHERE id = %s", (task_id,))
        if not cur.fetchone():
            raise HTTPException(status_code=404, detail="Task not found")

        cur.execute("DELETE FROM daily_plan WHERE task_id = %s", (task_id,))
        cur.execute("DELETE FROM tasks WHERE id = %s", (task_id,))

        conn.commit()
        cur.close()
        conn.close()

        return {"message": "Task deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting task: {str(e)}")

# Unschedule a task (remove from schedule but keep task)
@app.delete("/schedule/{task_id}")
def unschedule_task(task_id: int):
    try:
        conn = get_conn()
        cur = conn.cursor()

        cur.execute("DELETE FROM daily_plan WHERE task_id = %s", (task_id,))
        conn.commit()
        
        if cur.rowcount == 0:
            raise HTTPException(status_code=404, detail="Task not found in schedule")

        cur.close()
        conn.close()

        return {"message": "Task unscheduled successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error unscheduling task: {str(e)}")
