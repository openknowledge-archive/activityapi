import os

DEBUG = True
PROD = False
TESTING = True
DB_CON = os.environ.get('DATABASE_URL')
LOG_LEVEL = os.environ.get('LOG_LEVEL', 'DEBUG')

if not PROD:
   DB_CON = 'postgresql://localhost/zephod'


SECRET_KEY = 'aTi1LqrwnK01XnRlVMh4HVYZ'
CSRF_SESSION_KEY = 'uaextvIbdtdLlxaBhNIRdt1a'
CSRF_ENABLED = False
