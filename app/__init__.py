import yaml

from flask import Flask
from flask.ext.sqlalchemy import SQLAlchemy

DEFAULT_CONFIG_PATH = 'app/config/default.yml'
CONFIG_PATH = 'config.yml'

with open(DEFAULT_CONFIG_PATH, 'r') as f:
    config = yaml.load(f)
    print(config)

with open(CONFIG_PATH, 'r') as f:
    config.update(yaml.load(f))

application = Flask(__name__, template_folder='../' + config['app']['template_dir'], static_folder='../' + config['app']['static_dir'])

application.config['SQLALCHEMY_DATABASE_URI'] = config['app']['database_uri']
application.config['WTF_CSRF_ENABLED'] = True
application.config['SECRET_KEY'] = config['app']['csrf_secret_key']

application.config.update(config['flask'])

db = SQLAlchemy(application)

# MODELS
import app.models
######

# UPLOADS
import app.attachments
attachments.registerFetcher('file', attachments.ImageUploadFetcher(
    name = 'upload_images',
    whitelist = ['jpg', 'png', 'gif', 'tga', 'bmp'],
    directory = 'images'
))
attachments.registerFetcher('link', attachments.RemoteImageFetcher(
    name = 'remote_images',
    whitelist = ['image/jpeg', 'image/png', 'image/gif'],
    directory = 'images'
))
attachments.registerFetcher('link', attachments.YoutubeFetcher(
    name = 'youtube'
))
attachments.registerFetcher('link', attachments.ProstopleerFetcher(
    name = 'prostopleer'
))
######

# VIEWS
from app.frontend import frontend
from app.api import api
application.register_blueprint(frontend)
application.register_blueprint(api, url_prefix='/api')
######

db.create_all()

# DEBUG
if len(app.models.Board.query.all()) == 0:
    test = app.models.Board.create(
        tag = 'b',
        title = 'bread'    
    )
    db.session.add(test)
    db.session.commit()

######