from flask import Flask
from flask.ext.sqlalchemy import SQLAlchemy
from pralka_server.utils import RegexConverter

import os, sys
base = os.path.abspath(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))
sys.path.append(base)

app = Flask(__name__)

app.config.from_object('pralka_server.config')
app.url_map.converters['regex'] = RegexConverter

db = SQLAlchemy(app)

import pralka_server.views
#, models
