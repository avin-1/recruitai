import sqlite3
conn = sqlite3.connect('backend/selected_candidates.db')
cursor = conn.cursor()

print('=== ALL SELECTED CANDIDATES ===')
cursor.execute('SELECT * FROM selected_candidates ORDER BY selection_date DESC')
rows = cursor.fetchall()
if rows:
    # Print header
    cursor.execute('PRAGMA table_info(selected_candidates)')
    columns = [column[1] for column in cursor.fetchall()]
    print(' | '.join(columns))
    print('-' * 80)
    
    # Print data
    for row in rows:
        print(' | '.join(str(item) for item in row))
else:
    print('No entries found in the database.')

conn.close()