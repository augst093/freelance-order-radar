import sqlite3
import config

def migrate():
    db_path = "freelance_radar.db"
    print(f"Connecting to database at {db_path}...")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 1. Clear old keywords
    print("Clearing old keywords...")
    cursor.execute("DELETE FROM keywords")
    
    # 2. Insert new high priority keywords
    print(f"Inserting {len(config.DEFAULT_HIGH_PRIORITY_KEYWORDS)} Vibe Coding priority keywords...")
    for kw in config.DEFAULT_HIGH_PRIORITY_KEYWORDS:
        cursor.execute("INSERT OR IGNORE INTO keywords (keyword, is_negative) VALUES (?, 0)", (kw,))
        
    # 3. Insert new negative keywords
    print(f"Inserting {len(config.DEFAULT_NEGATIVE_KEYWORDS)} Vibe Coding negative keywords...")
    for kw in config.DEFAULT_NEGATIVE_KEYWORDS:
        cursor.execute("INSERT OR IGNORE INTO keywords (keyword, is_negative) VALUES (?, 1)", (kw,))
        
    conn.commit()
    conn.close()
    print("Migration completed successfully!")

if __name__ == "__main__":
    migrate()
