from flask import Flask
from config import Config


app = Flask(__name__)
app.config.from_object(Config)

from poem import db

app.app_context().push()
db.init_app(app)
db.drop_all()
db.create_all()

from app import routes
