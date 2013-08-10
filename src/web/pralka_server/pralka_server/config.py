import os
basedir = os.path.abspath(os.path.dirname(__file__))

SQLALCHEMY_DATABASE_URI = os.environ['PRALKA_SQLALCHEMY_DATABASE_URI']
TWITTER_CONSUMER_KEY = os.environ['PRALKA_TWITTER_CONSUMER_KEY']
TWITTER_CONSUMER_SECRET = os.environ['PRALKA_TWITTER_CONSUMER_SECRET']
SECRET = os.environ['PRALKA_SECRET']
DOMAIN_NAME = '127.0.0.1:5000'
#SQLALCHEMY_MIGRATE_REPO = os.path.join(basedir, 'db_repository')