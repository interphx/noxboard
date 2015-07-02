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
        return jsonify(**{'success': False, 'errors': ['No thread with id %s' % thread_id]}), 404
    
    post = Post.query.get(last_id)
    if not post:
        return jsonify(**{'success': False, 'errors': ['No post with id %s' % last_id]}), 404
    

    posts = Post.query.filter_by(thread=thread).filter(Post.created_at >= post.created_at).filter(Post.id > last_id).all()
    posts = [post.serialize() for post in posts]

    return jsonify(**{'success': True, 'posts': posts})

# TODO: RESTful API with search
# TODO: nice generic validation for evrything (LIVR?)
@api.route('/threads/<int:thread_id>/posts/create/', methods=['POST'])
def create_post(thread_id):
    data = request.get_json(force=True)
    
    author_email = data.get('author_email', '')
    author_name = data.get('author_name', '')
    topic = data.get('topic', '')
    
    text = data.get('text')
    if text is None:
        return jsonify(**{'success': False, 'errors': ['Text must not be empty']}), 400
    
    thread = Thread.query.get(thread_id)
    
    attachment_ids = data.get('attachments', [])
    
    # TODO: return proper errors
    try:
        attachments = [Attachment.query.get(id) for id in attachment_ids]
        if None in attachments:
            raise Exception('Wrong attachment id was supplied')
    except:
        return jsonify(**{'success': False, 'errors': ['Something is wrong with your attachments']}), 400
    
    post = Post(
        is_op        = false,
        author_name  = author_name,
        author_email = author_email,
        topic        = topic,
        text         = text,
        thread       = thread,
        attachments  = attachments
    )
    db.session.add(post)
    db.session.commit()

    return jsonify(**{'success': True})
'''
# TODO: RESTful API with search
# TODO: nice generic validation for evrything (LIVR?)
@api.route('/attachments/create/', method=['POST'])
def create_attachment(thread_id):
    # TODO'''