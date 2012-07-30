import os

DB_CON = os.environ.get('DATABASE_URL')
LOG_LEVEL = os.environ.get('LOG_LEVEL', 'DEBUG')
DEV = not bool(DB_CON)

if DEV:
   DB_CON = 'postgresql://localhost/zephod'

