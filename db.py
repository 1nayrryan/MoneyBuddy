# database layer for sql queries
import sqlite3
from datetime import date

DB_PATH = "finance.db"

#opening connection to sql database
def get_connection():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row # rows behave like dicts
    return conn


#creating tables if they dont already exist, done when app starts
def init_db():
    conn = get_connection()
    conn.executescript(""" 
        CREATE TABLE IF NOT EXISTS lessons(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT NOT NULL, -- 'personal finance' | 'investing & markets' | 'macro' | 'frontier' | 'wealth strategy'
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TEXT DEFAULT (date('now'))             
        );

        CREATE TABLE IF NOT EXISTS bookmarks(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            lesson_id INTEGER NOT NULL REFERENCES lessons(id),
            saved_at TEXT DEFAULT (datetime('now'))
        );
                       
        CREATE TABLE IF NOT EXISTS streak (
            id INTEGER PRIMARY KEY CHECK (id = 1), -- only one row, single user streak log
            last_visit TEXT,
            days INTEGER DEFAULT 0
        );
                       
        INSERT OR IGNORE INTO streak (id, last_visit, days) VALUES (1, NULL, 0);
    """)
    conn.commit()
    conn.close()


def save_lesson(category, title, content):
    """inserting a new lesson. then returns new row's id"""
    conn = get_connection()
    cursor = conn.execute("INSERT INTO lessons(category, title, content) VALUES (?, ?, ?)", (category, title, content))
    conn.commit()
    lesson_id = cursor.lastrowid
    conn.close()
    return lesson_id

#getting the recently uploaded lessons, first 10
#allows for filtering by category
def get_lessons(category=None, limit= 10):
    conn = get_connection()
    if category:
        rows = conn.execute("SELECT * FROM lessons WHERE category = ? ORDER BY id DESC LIMIT ?", (category, limit)).fetchall()
    else:
        rows = conn.execute("SELECT * FROM lessons ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def toggle_bookmark(lesson_id):
    """removing and adding bookmarks"""
    conn = get_connection()
    existing = conn.execute("SELECT id FROM bookmarks WHERE lesson_id = ?", (lesson_id,)).fetchone()

    if existing:
        conn.execute("DELETE FROM bookmarks WHERE lesson_id = ?", (lesson_id,))
        conn.commit()
        conn.close()
        return False
    else:
        conn.execute("INSERT INTO bookmarks (lesson_id) VALUES (?)", (lesson_id,))
        conn.commit()
        conn.close()
        return True
    

def get_bookmarks():
    """returning all bookmarked lessons"""
    conn = get_connection()
    rows = conn.execute("""SELECT lessons.*, bookmarks.saved_at 
                        FROM bookmarks 
                        JOIN lessons ON lessons.id = bookmarks.lesson_id ORDER BY bookmarks.saved_at DESC""").fetchall()
    conn.close()
    return [dict(row) for row in rows]

def get_recent_titles(category, limit=20):
    """fetching titles of most recent lessons"""
    conn = get_connection()
    rows = conn.execute(
        "SELECT title FROM lessons WHERE category = ? ORDER BY id DESC LIMIT ?", (category, limit)).fetchall()
    conn.close()
    return [row["title"] for row in rows] # return a plain list of strings

def update_streak():
    from datetime import timedelta
    conn = get_connection()
    today = str(date.today())
    row = conn.execute("SELECT * FROM streak WHERE id = 1").fetchone()

    if row["last_visit"] == today:
        conn.close()
        return row["days"]
    
    yesterday = str(date.today() - timedelta(days=1))
    
    if row["last_visit"] == yesterday:
        new_days = row["days"] + 1  # continue the streak
    else:
        new_days = 1
        
    conn.execute("UPDATE streak SET last_visit = ?, days = ? WHERE id = 1", (today, new_days))
    conn.commit()
    conn.close()
    return new_days