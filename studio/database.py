import sqlite3
import os
import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

# Allow overriding via env var for Docker
DB_PATH = os.environ.get("DB_PATH")
if not DB_PATH:
    DB_PATH = str(PROJECT_ROOT / "data" / "story_studio.db")
else:
    # Ensure directory exists if custom path used
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    c = conn.cursor()
    

    # New robust table for Sprint 2
    c.execute('''
        CREATE TABLE IF NOT EXISTS generated_images (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            scene_index INTEGER,
            story_name TEXT,
            prompt TEXT,
            seed INTEGER,
            status TEXT DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            completed_at TIMESTAMP,
            generation_duration REAL,
            filename TEXT,
            narration_text TEXT,
            audio_file TEXT
        )
    ''')

    # Migration for existing databases
    try:
        c.execute('ALTER TABLE generated_images ADD COLUMN narration_text TEXT')
    except: pass
    try:
        c.execute('ALTER TABLE generated_images ADD COLUMN audio_file TEXT')
    except: pass

    # New table for Video Gallery
    c.execute('''
        CREATE TABLE IF NOT EXISTS generated_videos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            story_name TEXT,
            filename TEXT,
            transition TEXT,
            duration REAL,
            status TEXT DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            completed_at TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()


# --- Sprint 2 New Functions ---

def create_generation_record(scene_index, story_name, prompt, seed, filename=None):
    conn = get_db_connection()
    c = conn.cursor()
    now = datetime.datetime.now()
    c.execute(
        '''INSERT INTO generated_images 
           (scene_index, story_name, prompt, seed, status, created_at, filename) 
           VALUES (?, ?, ?, ?, 'pending', ?, ?)''',
        (scene_index, story_name, prompt, seed, now, filename)
    )
    new_id = c.lastrowid
    conn.commit()
    conn.close()
    return new_id

def update_generation_record(run_id, filename, duration):
    conn = get_db_connection()
    c = conn.cursor()
    now = datetime.datetime.now()
    c.execute(
        '''UPDATE generated_images 
           SET status='completed', filename=?, completed_at=?, generation_duration=? 
           WHERE id=?''',
        (filename, now, duration, run_id)
    )
    conn.commit()
    conn.close()

def update_scene_narration(story_name, scene_index, narration_text, audio_file=None):
    conn = get_db_connection()
    c = conn.cursor()
    if audio_file:
        c.execute(
            '''UPDATE generated_images 
               SET narration_text=?, audio_file=? 
               WHERE story_name=? AND scene_index=?''',
            (narration_text, audio_file, story_name, scene_index)
        )
    else:
        c.execute(
            '''UPDATE generated_images 
               SET narration_text=? 
               WHERE story_name=? AND scene_index=?''',
            (narration_text, story_name, scene_index)
        )
    conn.commit()
    conn.close()

def get_generation_stats():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('''
        SELECT 
            COUNT(*) as total_count, 
            AVG(generation_duration) as avg_time, 
            SUM(generation_duration) as total_time 
        FROM generated_images 
        WHERE status='completed'
    ''')
    row = c.fetchone()
    conn.close()
    return {
        "count": row['total_count'] or 0,
        "avg_time": round(row['avg_time'] or 0, 2),
        "total_time": round(row['total_time'] or 0, 2)
    }

def get_recent_generations(limit=10):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('SELECT * FROM generated_images ORDER BY id DESC LIMIT ?', (limit,))
    rows = c.fetchall()
    conn.close()
    return rows

def get_image_id_by_filename(filename):
    conn = get_db_connection()
    c = conn.cursor()
    # Handle cases where filename might be full path or just name
    base_name = os.path.basename(filename)
    c.execute('SELECT id FROM generated_images WHERE filename LIKE ?', ('%' + base_name,))
    row = c.fetchone()
    conn.close()
    return row['id'] if row else None

def get_dashboard_stats():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('''
        SELECT 
            story_name,
            COUNT(*) as total_scenes,
            SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed_scenes
        FROM generated_images
        GROUP BY story_name
    ''')
    rows = c.fetchall()
    conn.close()
    
    stats = []
    for row in rows:
        status = "completed" if row['total_scenes'] == row['completed_scenes'] else "in_progress"
        stats.append({
            "story_name": row['story_name'],
            "total_scenes": row['total_scenes'],
            "completed_scenes": row['completed_scenes'],
            "status": status
        })
    return stats

def delete_story_generations(story_name):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('DELETE FROM generated_images WHERE story_name = ?', (story_name,))
    conn.commit()
    conn.close()

# --- Video Generation Functions ---

def create_video_record(story_name, transition, duration):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute(
        '''INSERT INTO generated_videos 
           (story_name, transition, duration, status) 
           VALUES (?, ?, ?, 'pending')''',
        (story_name, transition, duration)
    )
    new_id = c.lastrowid
    conn.commit()
    conn.close()
    return new_id

def update_video_record(video_id, filename, status='completed'):
    conn = get_db_connection()
    c = conn.cursor()
    now = datetime.datetime.now()
    c.execute(
        '''UPDATE generated_videos 
           SET status=?, filename=?, completed_at=? 
           WHERE id=?''',
        (status, filename, now, video_id)
    )
    conn.commit()
    conn.close()

def get_all_videos():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('SELECT * FROM generated_videos WHERE status="completed" ORDER BY id DESC')
    rows = c.fetchall()
    conn.close()
    return rows

def delete_video_record(video_id):
    conn = get_db_connection()
    c = conn.cursor()
    # First get the filename to delete from disk? 
    # (Protocol says management actions include delete)
    c.execute('SELECT story_name, filename FROM generated_videos WHERE id = ?', (video_id,))
    row = c.fetchone()
    if row:
        video_path = os.path.join(str(PROJECT_ROOT / "output"), row['story_name'], "videos", row['filename'])
        if os.path.exists(video_path):
            os.remove(video_path)
    
    c.execute('DELETE FROM generated_videos WHERE id = ?', (video_id,))
    conn.commit()
    conn.close()
