import app.api
from app.util import request_wants_json

from flask import jsonify, render_template, Blueprint

frontend = Blueprint('frontend', __name__)

@frontend.route('/hello/')
@frontend.route('/hello/<name>')
def hello(name='World'):
    if request_wants_json():
        return jsonify(api.hello(name))
    return name