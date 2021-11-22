import os
basedir = os.path.abspath(os.path.dirname(__file__))


class Config(object):
    SECRET_KEY = os.environ.get('SECRET_KEY') or '**************'
    MYSQL_USER = os.environ.get('MYSQL_DATABASE_USER') or 'root'
    MYSQL_PASSWORD = os.environ.get('MYSQL_DATABASE_PASSWORD') or ''
    MYSQL_DB = os.environ.get('MYSQL_DATABASE_DB') or 'metro-hacks'
    MYSQL_HOST = os.environ.get('MYSQL_DATABASE_HOST') or 'localhost'
    SESSION_PERMANENT = False
    SESSION_COOKIE_SAMESITE=None
    SESSION_COOKIE_SECURE=True
