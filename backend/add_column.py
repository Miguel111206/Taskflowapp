from app.db import engine
from sqlmodel import text

with engine.connect() as conn:
    try:
        conn.execute(text('ALTER TABLE task ADD COLUMN image TEXT NULL'))
        conn.commit()
        print('Column image added')
    except Exception as e:
        print(f'Error: {e}')