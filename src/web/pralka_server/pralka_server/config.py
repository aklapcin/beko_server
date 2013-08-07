import os
basedir = os.path.abspath(os.path.dirname(__file__))

SQLALCHEMY_DATABASE_URI = 'postgresql://pralka:washingMachine@localhost/pralka'
SQLALCHEMY_MIGRATE_REPO = os.path.join(basedir, 'db_repository')