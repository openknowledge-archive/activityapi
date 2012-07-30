import os

DB_CON = os.environ.get('DATABASE_URL')
LOG_LEVEL = os.environ.get('LOG_LEVEL', 'DEBUG')
DEV = not bool(DB_CON)

if not DB_CON:
    raise ValueError('No DATABASE_URL defined in the environment. Try running:\n          $ export DATABASE_URL=postgresql://user:pass@localhost/mydatabase')

