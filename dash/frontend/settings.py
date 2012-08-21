import os

LOG_LEVEL = os.environ.get('LOG_LEVEL', 'DEBUG')
# TODO nobody will ever know what the difference between these is...
DEBUG = True
TESTING = True

# TODO remove these. Legacy. (I'm pretty certain...)
SECRET_KEY = 'aTi1LqrwnK01XnRlVMh4HVYZ'
CSRF_SESSION_KEY = 'uaextvIbdtdLlxaBhNIRdt1a'
CSRF_ENABLED = False

