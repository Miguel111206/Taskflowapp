import pymysql

conn = pymysql.connect(host='localhost', port=3306, user='root', password='123456789', database='taskflow')
cursor = conn.cursor()

# Check and add priority column
cursor.execute('SHOW COLUMNS FROM task LIKE "priority"')
if not cursor.fetchone():
    cursor.execute('ALTER TABLE task ADD COLUMN priority VARCHAR(50) DEFAULT "media"')
    print('Added priority column')
else:
    print('priority column already exists')

# Check and add created_at column
cursor.execute('SHOW COLUMNS FROM task LIKE "created_at"')
if not cursor.fetchone():
    cursor.execute('ALTER TABLE task ADD COLUMN created_at DATETIME DEFAULT CURRENT_TIMESTAMP')
    print('Added created_at column')
else:
    print('created_at column already exists')

conn.commit()
conn.close()
print('Done!')
