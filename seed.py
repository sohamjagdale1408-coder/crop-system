from database import get_db, init_db

def seed():
    init_db()
    conn = get_db()
    
    grains = [
        ('Rice', 120),
        ('Wheat', 110),
        ('Corn', 90),
        ('Soybeans', 100),
        ('Potatoes', 85)
    ]
    
    with conn:
        for name, days in grains:
            conn.execute('INSERT OR IGNORE INTO grain_types (name, default_days_to_harvest) VALUES (?, ?)', (name, days))
            
    print("Database seeded successfully.")
    conn.close()

if __name__ == '__main__':
    seed()
