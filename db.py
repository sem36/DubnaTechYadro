import sqlite3

DB_PATH = r'E:\Projects\DubnaTechYadro-Dima-A\animals_ads.db'

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            photo BLOB,
            description TEXT,
            location TEXT,
            breed TEXT,
            user_telegram_id TEXT
        )
    ''')
    conn.commit()
    conn.close()

def save_ad_to_db(description, photo_path, location=None, breed=None, user_telegram_id=None):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    with open(photo_path, 'rb') as file:
        photo_data = file.read()
    cursor.execute('INSERT INTO ads (description, photo, location, breed, user_telegram_id) VALUES (?, ?, ?, ?, ?)', 
                   (description, photo_data, location, breed, user_telegram_id))
    conn.commit()
    conn.close()

def get_all_ads():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT description, photo, location, breed, user_telegram_id FROM ads')
    ads = cursor.fetchall()
    conn.close()
    return ads

def get_breeds():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT DISTINCT breed FROM ads')
    breeds = cursor.fetchall()
    conn.close()
    return [breed[0] for breed in breeds]

def update_ad_with_telegram(update_user_id, ad_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('UPDATE ads SET user_telegram_id = ? WHERE id = ?', (update_user_id, ad_id))
    conn.commit()
    conn.close()