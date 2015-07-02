import datetime
from app.database import Column, Model, relationship, db
from app import config

attachment_to_post = db.Table('attachment_to_post',
    Column('attachment_id', db.Integer, db.ForeignKey('attachment.id')),
    Column('post_id', db.Integer, db.ForeignKey('post.id'))
)

class Post(Model):
    id = Column(db.Integer, primary_key=True)
    is_op = Column(db.Boolean, default=False)
    author_email = Column(db.String(255), default=None)
    author_name = Column(db.String(255), default=None)
    topic = Column(db.String(255), default=None)
    text = Column(db.Text, nullable=False)
    created_at = Column(db.DateTime, default=datetime.datetime.utcnow)
    thread_id = Column(db.Integer, db.ForeignKey('thread.id'), nullable=False)
    thread = relationship('Thread', backref=db.backref('posts', lazy='dynamic'), uselist=False)
    attachments = relationship('Attachment', secondary=attachment_to_post,
        backref=db.backref('posts', lazy='dynamic')
    )
    
    def __repr__(self):
        return '<Thread %d>' % self.id

    def serialize(self):
        return ({
            'id': self.id,
            'is_op': self.is_op,
            'author_email': self.author_email,
            'author_name': self.author_name,
            'topic': self.topic,
            'text': self.text,
            'created_at': str(self.created_at), # TODO?
            'thread_id': self.thread_id 
        })

class Thread(Model):
    id = Column(db.Integer, primary_key=True)
    is_pinned = Column(db.Boolean, default=False)
    is_open = Column(db.Boolean, default=True)
    created_at = Column(db.DateTime, default=datetime.datetime.utcnow, nullable=False)
    updated_at = Column(db.DateTime, default=datetime.datetime.utcnow, nullable=False)
    board_id = Column(db.Integer, db.ForeignKey('board.id'), nullable=False)
    board = relationship('Board', backref=db.backref('threads', lazy='dynamic'), uselist=False)

    def __repr__(self):
        return '<Thread %d>' % self.id

class Board(Model):
    id = Column(db.Integer, primary_key=True)
    tag = Column(db.String(16), unique=True, nullable=False)
    title = Column(db.String(150), nullable=False)
    new_thread_requires_file = Column(db.Boolean, default=True)
    max_file_size = Column(db.Integer, default=config['attachments']['max_file_size'])
    max_files_per_post = Column(db.Integer, default=config['attachments']['max_files_per_post'])
    allow_textless_posts = Column(db.Boolean, default=config['app']['allow_textless_posts'])

    def __repr__(self):
        return '<Board %r>' % self.tag

class Attachment(Model):
    id = Column(db.Integer, primary_key=True)
    resource = Column(db.String(512), nullable=False)
    type = Column(db.String(64), nullable=False)
    is_local = Column(db.Boolean, nullable=False)
    hash = Column(db.String(64), nullable=False)
    #post_id = Column(db.Integer, db.ForeignKey('post.id'), nullable=False)
    #post = relationship('Post', backref=db.backref('attachments', lazy='dynamic'), uselist=False)

    def __repr__(self):
        return '<Attachment %r>' % self.id
    
    # TODO
    @staticmethod
    def fromFile(file):
        pass
    
    # TODO
    @staticmethod
    def fromLink(link):
        pass