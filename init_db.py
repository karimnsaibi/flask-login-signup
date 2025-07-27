import sqlite3
import os

def init_db():
    # Delete old database if exists
    if os.path.exists('your_database.db'):
        os.remove('your_database.db')
    
    conn = sqlite3.connect('your_database.db')
    cur = conn.cursor()
    
    # Users table
    cur.execute('''
    CREATE TABLE users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        user_id TEXT NOT NULL UNIQUE,
        profile TEXT NOT NULL,
        password TEXT NOT NULL
    )
    ''')
    # GSM site table
    cur.execute('''
    CREATE TABLE gsm_site (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nom_site TEXT NOT NULL,
    latitude REAL,
    longitude REAL,
    region TEXT,
    gouvernorat TEXT,
    technologie TEXT CHECK(technologie IN ('2G', '3G', '4G'))
    )''')
    # Antenna config (physical + logical parameters)
    cur.execute('''
    CREATE TABLE antenna_config (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    site_id INTEGER NOT NULL,
    secteur TEXT,
    azimut INTEGER,
    pire REAL,
    tilt_mecanique REAL,
    tilt_electrique REAL,
    FOREIGN KEY(site_id) REFERENCES gsm_site(id) ON DELETE CASCADE
    )''')
    # KPI data
    cur.execute('''
    CREATE TABLE kpi_stats (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    site_id INTEGER NOT NULL,
    date DATE NOT NULL,
    taux_blocage REAL,
    taux_coupure REAL,
    taux_disponibilite REAL,
    trafic_voix_erlang REAL,
    trafic_data_go REAL,
    trafic_volte_go REAL,
    FOREIGN KEY(site_id) REFERENCES gsm_site(id) ON DELETE CASCADE
    )''')
    # Indexes
    cur.execute('''
    CREATE INDEX idx_kpi_site_date ON kpi_stats(site_id, date)
    ''')
    cur.execute('''
    CREATE INDEX idx_antenna_site ON antenna_config(site_id)
    ''')
    
    cur.execute('''
  CREATE TABLE site (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  region TEXT NOT NULL,
  code TEXT NOT NULL,
  delegation TEXT NOT NULL,
  site_name TEXT NOT NULL,
  x TEXT NOT NULL,
  y TEXT NOT NULL,
  hba TEXT NOT NULL,
  supplier TEXT NOT NULL,
  access TEXT NOT NULL,
  antenna TEXT NOT NULL,
  surface TEXT NOT NULL,
  UNIQUE(region,code,delegation)
  ) ''')
    
    # Create site_code_pools table
    cur.execute('''
  CREATE TABLE site_code_pools (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  region TEXT NOT NULL,
  start_code INTEGER NOT NULL,
  end_code INTEGER NOT NULL
  )''')

    
    conn.commit()
    conn.close()
    print("Database created with updated schema")

if __name__ == '__main__':
    init_db()
