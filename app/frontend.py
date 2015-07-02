import os
from app.attachments import createAttachment, AttachmentTooLargeException, AttachmentNotSupportedException, TooManyAttachmentsException
from app import config, db
from flask import Blueprint, request, redirect, url_for, render_template, send_from_directory
from app.models import Board, Thread, Post, Attachment
from app.util import view, render_html
from app.forms import PostForm

frontend = Blueprint('frontend', __name__)

# TODO: Errors i18n
# TODO: Maybe handle TooManyAttachmentsException?
def createAttachmentsFromForm(form):
    result = []
    count = 0
    
    def createWithErrors(type, field):
        nonlocal count
        if not field.data: return
        count += 1
        if count > config['attachments']['max_files_per_post']: raise TooManyAttachmentsException('Too many files')
        try:
            result.append(createAttachment(type, field.data))
        except AttachmentTooLargeException as e:
            field.errors.append('Файл слишком большой')
            raise e
        except AttachmentNotSupportedException as e:
            field.errors.append('Неподдерживаемый формат приложения')
            raise e
        except AttachmentException as e:
            field.errors.append('Не удаётся загрузить файл')
            raise e

    for file_field in form.files:
        createWithErrors('file', file_field)

    for link_field in form.links:
        createWithErrors('link', link_field)
    
    return result

# TODO: Probably we need to commit attachments
def createPostFromForm(form, thread, is_op):
    # TODO: change to form validator or other clean way
    if is_op and form.text.data.strip() == '':
        raise Exception('OP post must contain text!')

    attachments = createAttachmentsFromForm(form)
    post = Post(
        is_op        = is_op,
        author_name  = form.author_name.data,
        author_email = form.author_email.data,
        topic        = form.topic.data,
        text         = form.text.data,
        thread       = thread
    )
    
    for attachment in attachments:
        post.attachments.append(attachment)
       
    return post
    

def createThreadFromForm(form, board):
    thread = Thread(
        board = board
    )
    db.session.add(thread)
    
    post = createPostFromForm(form, thread, True)
    db.session.add(post)
    
    return thread

# TODO: allow to set main page from admin panel
@frontend.route('/')
def index(board=None):
    return redirect(url_for('.board', board_tag='b'))

@frontend.route('/uploads/<path:filename>')
def serve_uploaded(filename):
    return send_from_directory(os.path.abspath(config['attachments']['base_dir']), filename)

# TODO: 404 if not found
# TODO: Either make it not view or make view work with it
# TODO: properly calculate threads per page (from cookies, from config, check <= maximum)
# TODO: properly calculate max_files_per_post
# TODO: properly calculate files_count
@frontend.route('/<board_tag>/', methods=['GET', 'POST'])
@frontend.route('/<board_tag>/<int:page>/', methods=['GET', 'POST'])
#@view(render_html('board.html'))
def board(board_tag='b', page=1):
    board = Board.query.filter_by(tag=board_tag).first()
    
    postForm = PostForm(1)
    if request.method == 'POST' and postForm.validate_on_submit():
        try:
            thread = createThreadFromForm(postForm, board)
        except Exception as e:
            print('!!!!!!!!!!!!!!!!!!!!!!')
            print('Exception: doing rollback (call from board)')
            print('!!!!!!!!!!!!!!!!!!!!!!')
            db.session.rollback()
            #raise e
        else:
            db.session.commit()
            if postForm.redirect_to.data == 'thread':
                return redirect(url_for('.thread', thread_id=thread.id, board_tag=board.tag))
            else:
                return redirect(url_for('.board', board_tag=board.tag))
    
    pagination = (Thread.query
        .filter_by(board=board)
        .order_by(
            Thread.is_pinned.desc(), 
            Thread.updated_at.desc()
        ).paginate(page, config['app']['default_threads_per_page'])
    )
    
    return render_template('board.html', **{
        'board': board,
        'threads': pagination.items,
        'pagination': pagination,
        'config': config,
        'files_count': 1,
        'postForm': postForm
    })

# TODO: 404 if not found
# TODO: Either make it not view or make view work with it
# TODO: allow to set main page from admin panel
# TODO: properly calculate threads per page (from cookies, from config, check <= maximum)
@frontend.route('/<board_tag>/thread/<thread_id>/', methods=['GET', 'POST'])
#@view(render_html('thread.html'))
def thread(board_tag, thread_id):
    thread = Thread.query.filter_by(id=thread_id).first()
    board = thread.board
    
    postForm = PostForm(1)
    if request.method == 'POST' and postForm.validate_on_submit():
        try:
            post = createPostFromForm(postForm, thread, False)
            db.session.add(post)
            
        except:
            print('!!!!!!!!!!!!!!!!!!!!!!')
            print('Exception: doing rollback (call from thread)')
            print('!!!!!!!!!!!!!!!!!!!!!!')
            db.session.rollback()
            #raise e
        else:
            db.session.commit()
            if postForm.redirect_to.data == 'thread':
                return redirect(url_for('.thread', thread_id=thread.id, board_tag=board.tag))
            else:
                return redirect(url_for('.board', board_id=board.id))
    
    posts = thread.posts

    return render_template('thread.html', **{
        'board': board,
        'thread': thread,
        'posts': posts,
        'config': config,
        'postForm': postForm,
        'files_count': 1
    })