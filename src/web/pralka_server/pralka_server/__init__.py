from flask import Flask
from flask.ext.sqlalchemy import SQLAlchemy
from pralka_server.utils import RegexConverter, ItsdangerousSessionInterface
from pralka_server import config
# Tiny little path magic
import os, sys
libs = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), "lib")
sys.path.append(libs)

app = Flask(__name__)

app.config.from_object('pralka_server.config')

app.url_map.converters['regex'] = RegexConverter
app.session_interface = ItsdangerousSessionInterface()
app.secret_key = config.SECRET
db = SQLAlchemy(app)

import pralka_server.views
#, models
