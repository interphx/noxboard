from flask_wtf import Form
from wtforms import BooleanField, StringField, TextAreaField, RadioField, FileField, FieldList, validators
from . import config

text_validators = [validators.Length(max=15000, message="Text should be no more than 15000 characters long!")]
if not config['app']['allow_textless_posts']:
    text_validators.append(validators.InputRequired('Text should not be empty'))

# TODO: Show pinned option only for moderators
class PostForm(Form):
    author_name = StringField('Name', [validators.Length(max=64, message="Name should be no more than 64 characters long!")])
    author_email = StringField('Email')
    topic = StringField('Topic', [validators.Length(max=150, message="Topic should be no more than 150 characters long!")])
    text = TextAreaField('Text', text_validators)
    redirect_to = RadioField('Redirect to', choices=[('board', 'Board'), ('thread', 'Thread')], default="thread")
    files = FieldList(FileField('File'), max_entries=config['app']['max_files_per_post'])
    links = FieldList(StringField('Link'), [validators.URL(message='Invalid URL!')], max_entries=config['app']['max_files_per_post'])
    
    # TODO: just make files and links counts equal to request files count
    def __init__(self, attachments_count):
        super().__init__()

        for _ in range(max(0, attachments_count - len(self.files))):
            self.files.append_entry()

        for _ in range(max(0, attachments_count - len(self.links))):
            self.links.append_entry()