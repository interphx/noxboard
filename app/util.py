import flask
import requests
import io
import re
import os
from app import config
from functools import wraps
from flask import render_template, jsonify

FILE_DOWNLOAD_TIMEOUT = 12
FILE_DOWNLOAD_CHUNK_SIZE = 1024
FILE_DOWNLOAD_MAX_SIZE = config['app']['max_file_size']

VALID_URL_REGEX = re.compile(
    r'^(?:http|ftp)s?://' # http:// or https://
    r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|' #domain...
    r'localhost|' #localhost...
    r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})' # ...or ip
    r'(?::\d+)?' # optional port
    r'(?:/?|[/?]\S+)$', re.IGNORECASE
)

def join_path(*args, separator=os.path.sep, trailing=False):
    result = ''
    for i, arg in enumerate(args):
        if arg[-len(separator):] != separator and (i != len(args) or trailing):
            result += arg + separator
        else:
            result += arg
    if not trailing and result[-len(separator):] == separator:
        return result[:-len(separator)]
    return result

class MemoryFile(io.BytesIO):

    def save(self, filename):
        with open(filename, 'wb') as f:
            f.write(self.getvalue())

# TODO: Rename to reflect the fact that it does not always return extension from file name
# TODO: Probably use mimetypes?
def getExt(filename):
    result = os.path.splitext(filename)[1][1:]
    if result in ['jpeg', 'jpe', 'jfif']: result = 'jpg'
    return result

def isValidUrl(url):
    return url is not None and VALID_URL_REGEX.search(url)

class FileSizeException(Exception):
    pass

def download_bytes(url, destination=None, max_file_size=FILE_DOWNLOAD_MAX_SIZE, timeout=FILE_DOWNLOAD_TIMEOUT):
    response = requests.get(url, timeout=timeout, stream=True)
    response.raise_for_status()
    
    if destination is None:
        destination = MemoryFile()
    
    if int(response.headers.get('content-length') or 0) > max_file_size:
        raise FileSizeException('File is too large!')
    
    size = 0
    
    for chunk in response.iter_content(chunk_size=FILE_DOWNLOAD_CHUNK_SIZE):
        if chunk:
            size += len(chunk)
            if size > max_file_size:
                raise FileSizeException('File is too large!')
            destination.write(chunk)
            destination.flush()
    
    return destination

def download_file(url, destination, max_file_size=FILE_DOWNLOAD_MAX_SIZE, timeout=FILE_DOWNLOAD_TIMEOUT):
    response = requests.get(url, timeout=timeout, stream=True)
    response.raise_for_status()
    
    if int(response.headers.get('content-length') or 0) > max_file_size:
        raise FileSizeException('File is too large!')
    
    size = 0
    
    with open(destination, 'wb') as f:
        for chunk in response.iter_content(chunk_size=FILE_DOWNLOAD_CHUNK_SIZE):
            if chunk:
                size += len(chunk)
                if size > max_file_size:
                    raise FileSizeException('File is too large!')
                f.write(chunk)
                f.flush()
    
    return destination
    

def request_wants_json(request):
    best = request.accept_mimetypes.best_match(['application/json', 'text/html'])
    return (best == 'application/json' and 
        request.accept_mimetypes[best] > request.accept_mimetypes['text/html'])

class html_or_json(object):
    def __init__(self, html_template_name, json_serializer=flask.jsonify):
        self.html_template_name = html_template_name
        self.json_serializer = json_serializer
    
    def __call__(self, f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            result = f(*args, **kwargs)
            if request_wants_json(flask.request):
                return self.json_serializer(result)
            return flask.render_template(self.html_template_name, **result)
        return wrapper

def render_html(template_name):
    return lambda data: render_template(template_name, **data)

def render_json(data):
    return jsonify(data)
        
def view(render_function):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            return render_function(f(*args, **kwargs))
        return wrapper
    return decorator
    