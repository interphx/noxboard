import re
from flask import Blueprint, request, jsonify
from . import config, db
from .util import view
from .attachments import createAttachment
from .models import *


api = Blueprint('api', __name__)

# TODO: RESTful API with search
@api.route('/threads/<int:thread_id>/posts/after/<int:last_id>/')
def posts(thread_id, last_id):
    thread = Thread.query.get(thread_id)
    
    if not thread:
        return jsonify(**{'errors': ['No thread with id %s' % thread_id]}), 404
    
    posts = Post.query.filter_by(thread=thread).filter(Post.id > last_id).all()
    posts = [post.serialize() for post in posts]

    return jsonify(**{'posts': posts})