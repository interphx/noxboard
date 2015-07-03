import re
import requests
import mimetypes
import uuid
import hashlib
import io
import os
import re
import json
from urllib.parse import urlparse
from collections import namedtuple
from urllib.request import pathname2url
from werkzeug import secure_filename
from .util import download_file, getExt, isValidUrl, MemoryFile, join_path, download_bytes, FileSizeException, create_thumb, mime2ext, mime2thumb_ext
from .models import *
from . import config

HASHING_ALOGIRITHM = config['attachments']['hashing_algorithm']
THUMB_SIZE = tuple(config['attachments']['thumbnail_size'])
THUMB_PATTERN = '{name}_thumb.{ext}' # TODO
REMOTE_REQUEST_TIMEOUT = 6  # TODO
YOUTUBE_REGEX = re.compile(r'^(?:(?:https?\:)?\/\/)?(?:www\.)?(?:youtube(?:\-nocookie)?\.com|youtu\.be)\/\S+$')
YOUTUBE_VIDEO_ID_REGEX = re.compile(r'(?:(?:https?\:)?\/\/)?(?:www\.)?(?:youtube(?:-nocookie)?\.com\/(?:[^/]+\/.+\/|(?:v|e(?:mbed)?)\/|.*[?&]v=)|youtu\.be\/)([^"&?/ ]{11})')
PROSTOPLEER_REGEX = re.compile(r'^(?:(?:https?\:)?\/\/)?(?:www\.)?(?:pleer?\.com)\/tracks\/\S+$')
PROSTOPLEER_TRACK_ID_REGEX = re.compile(r'^(?:(?:https?\:)?\/\/)?(?:www\.)?(?:pleer?\.com)\/tracks\/(\S+)$')

AttachmentData = namedtuple('AttachmentData', ['resource', 'type', 'local', 'hash'])

class AttachmentException(Exception):
    pass

class AttachmentExistsException(AttachmentException):
    def __init__(self, duplicate_id):
        super().__init__('ATTACHMENT ALREADY EXISTS (YOU SHOULDNT SEE THIS EXCEPTION)')
        self.duplicate_id = duplicate_id

class AttachmentTooLargeException(AttachmentException):
    pass

class AttachmentNotSupportedException(AttachmentException):
    pass
    
class InvalidAttachmentException(AttachmentException):
    pass

class AttachmentsException(Exception):
    pass

class TooManyAttachmentsException(AttachmentsException):
    pass

def createAttachment(type, resource):
    fetcher = findMatchingFetcher(type, resource)
    if not fetcher:
        raise AttachmentNotSupportedException('Unsupported resource format')
    try:
        result = fetcher.fetch(resource)
    except AttachmentExistsException as e:
        return Attachment.query.get(e.duplicate_id)
    
    return Attachment(
        resource=result.resource,
        type=result.type,
        is_local=result.local,
        hash=result.hash
    )

class Fetcher:
    def __init__(self, name, directory=None):
        self.name = name
        if directory == None:
            directory = name
        self.directory = directory

    def getFullDirectory(self):
        return os.path.join(config['attachments']['base_dir'], self.directory)
    
    def isAllowed(self, resource):
        return False
    
    def __str__(self):
        return "<Fetcher %s>" % self.name
    
    def __repr__(self):
        return str(self)

class ImageUploadFetcher(Fetcher):
    def __init__(self, name, whitelist, directory=None):
        super().__init__(name, directory)
        self.whitelist = whitelist
        os.makedirs(self.getFullDirectory(), exist_ok=True) # TODO: Move to class DownloadingFileFetcher

    def isAllowed(self, resource):
        return getExt(resource.filename) in self.whitelist
    
    # TODO: chunked upload
    # TODO: check max file size
    def receive_upload(self, file):        
        blob = file.read()

        hash = hashlib.new(HASHING_ALOGIRITHM, blob).hexdigest()
        
        duplicate = Attachment.query.filter_by(hash=hash).first()
        if duplicate is not None:
            raise AttachmentExistsException(duplicate.id)
        
        try:
            thumb, mime = create_thumb(THUMB_SIZE, blob)
        except:
            raise InvalidAttachmentException('Invalid file')
        
        filename = secure_filename(str(uuid.uuid4()))
        
        full_filename = filename + '.' + mime2ext(mime)
        thumb_filename = THUMB_PATTERN.format(name=filename, ext=mime2thumb_ext(mime))

        dest = os.path.join(self.getFullDirectory(), full_filename)
        thumb_dest = os.path.join(self.getFullDirectory(), thumb_filename)
        
        location = join_path(self.getFullDirectory(), full_filename, separator='/')
        
        file.seek(0)
        file.save(dest)
        thumb.save(filename=thumb_dest)
        return location, hash, mime
    
    def fetch(self, task):
        [location, hash, type] = self.receive_upload(task)
        return AttachmentData(resource=pathname2url(location), type=type, local=True, hash=hash)

class RemoteImageFetcher(Fetcher):
    def __init__(self, name, whitelist, directory=None, max_file_size=config['attachments']['max_file_size']):
        super().__init__(name, directory)
        self.whitelist = whitelist
        self.max_file_size = max_file_size
        os.makedirs(self.getFullDirectory(), exist_ok=True) # TODO: Move to class DownloadingFileFetcher

    def isAllowed(self, resource):
        if not isValidUrl(resource): return False
        
        response = requests.head(resource)
        return (
            response.status_code == requests.codes.ok and 
            response.headers.get('content-type') in self.whitelist
        )
            

    def download(self, url):
        filename = secure_filename(str(uuid.uuid4()))
        
        response = requests.head(url)
        
        if int(response.headers.get('content-length') or 0) > self.max_file_size:
            raise AttachmentTooLargeException('File is too large!')
            
        # TODO: request headers just once
        content_type = response.headers.get('content-type')
        
        try:
            file = download_bytes(url, MemoryFile(), max_file_size=self.max_file_size)
        except FileSizeException:
            raise AttachmentTooLargeException('File is too large!')
        
        blob = file.getvalue()

        hash = hashlib.new(HASHING_ALOGIRITHM, file.getvalue()).hexdigest()
        
        duplicate = Attachment.query.filter_by(hash=hash).first()
        if duplicate is not None:
            raise AttachmentExistsException(duplicate.id)
        
        try:
            thumb, mime = create_thumb(THUMB_SIZE, blob)
        except:
            raise InvalidAttachmentException('Invalid file')
        
        filename = secure_filename(str(uuid.uuid4()))
        
        full_filename = filename + '.' + mime2ext(mime)
        thumb_filename = THUMB_PATTERN.format(name=filename, ext=mime2thumb_ext(mime))

        dest = os.path.join(self.getFullDirectory(), full_filename)
        thumb_dest = os.path.join(self.getFullDirectory(), thumb_filename)
        
        location = join_path(self.getFullDirectory(), full_filename, separator='/')
        
        file.seek(0)
        file.save(dest)
        thumb.save(filename=thumb_dest)
        
        return dest, hash, mime
    
    def fetch(self, task):
        [location, hash, type] = self.download(task)
        return AttachmentData(resource=pathname2url(location), type=type, local=True, hash=hash)
        
class YoutubeFetcher(Fetcher):
    def __init__(self, name):
        super().__init__(name)

    def isAllowed(self, resource):
        return re.match(YOUTUBE_REGEX, resource.strip())

    # Check if video exists by requesting header from Google
    def validateVideoId(self, video_id):
        # TODO: Probably request with v3 api call (requires Google project token)
        # Google changed the api and everything is broken now :c
        return True
        '''
        url = YOUTUBE_VALIDATION_URL % video_id
        try:
            status = requests.head(url, timeout=6).status_code
            return int(status) in [200, 404] # If validation page is not available, return true anyway
        except Exception as e:
            print(str(e))
            return True'''

    def getVideoId(self, raw_url):
        match = re.match(YOUTUBE_VIDEO_ID_REGEX, raw_url)
        if len(match.groups()) < 1:
            raise AttachmentException('Bad youtube video URL: %s' % raw_url)
            
        video_id = match.group(1)
        
        return video_id
            
    def fetch(self, task):
        video_id = self.getVideoId(task)
        if not self.validateVideoId(video_id):
            raise AttachmentException('Bad youtube video URL: %s; video id = %s' % (task, video_id))
        hash = hashlib.new(HASHING_ALOGIRITHM, video_id.encode('utf-8')).hexdigest()
        return AttachmentData(resource=video_id, type='youtube', local=False, hash=hash)

class ProstopleerFetcher(Fetcher):
    def __init__(self, name):
        super().__init__(name)

    def isAllowed(self, resource):
        return re.match(PROSTOPLEER_REGEX, resource.strip())

    def getTrackId(self, raw_url):
        match = re.match(PROSTOPLEER_TRACK_ID_REGEX, raw_url)
        if len(match.groups()) < 1:
            raise AttachmentException('Bad prostopleer track URL: %s' % raw_url)
            
        track_id = match.group(1)
        
        return track_id
    
    def getTrackEmbedId(self, track_id):
        response = requests.get('http://pleer.com/site_api/embed/track?id=%s' % track_id)
        return response.json()['embed_id']
            
    def fetch(self, task):
        track_id = self.getTrackId(task)
        embed_id = self.getTrackEmbedId(track_id)
        resource_string = track_id + ':' + embed_id
        hash = hashlib.new(HASHING_ALOGIRITHM, resource_string.encode('utf-8')).hexdigest()
        return AttachmentData(resource=resource_string, type='prostopleer', local=False, hash=hash)

class CoubFetcher(Fetcher):
    def __init__(self, name, whitelist=[r'(?:(?:https?\:)?\/\/)?(?:www\.)?coub\.com\/(?:view|embed)\/([^\?\&\#\"\\]+).*']):
        super().__init__(name, whitelist)
        # TODO
'''
    def isAllowed(self, resource):
        return any(re.match(expr, resource) for expr in self.whitelist)

    def getVideoIdAndValidate(self, raw_url):
        video_id_regex = r'(?:https?\:\/\/)?(?:www\.)?(?:youtube(?:-nocookie)?\.com\/(?:[^/]+\/.+\/|(?:v|e(?:mbed)?)\/|.*[?&]v=)|youtu\.be\/)([^"&?/ ]{11})'
        match = re.match(video_id_regex, raw_url)
        if len(match.groups()) < 1:
            raise AttachmentException('Bad youtube video URL!')
            
        video_id = match.group(1)
        
        if not self.validateVideoId(video_id):
            raise AttachmentException('Bad youtube video URL!')
        
        return video_id
            
    def fetch(self, task):
        video_id = self.getVideoIdAndValidate(task.resource)
        return AttachmentData(location=video_id, type='youtube', local=False)'''

fetchers = {
    'file': [],
    'link': []
}

def findMatchingFetcher(type, resource):
    if type not in fetchers:
        return None

    for fetcher in reversed(fetchers[type]):
        if fetcher.isAllowed(resource):
            return fetcher

    return None

def registerFetcher(type, fetcher):
    fetchers[type].append(fetcher)