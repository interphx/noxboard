# Noxboard

A modern forum/imageboard engine prototype built with Flask framework. Usable, but work in progress.

### Installation
1. Install the [dependencies](#dependencies)
2. Clone this repository
3. Open config and set ```flask.HOST``` to 127.0.0.1  to run locally or 0.0.0.0 to run as public server. Also set ```flask.PORT``` at your convenience.
4. Set ```app.csrf_secret_key``` to long random string
5. Execute run.py

It is highly recommended to use separate web server (ngnix or Apache) to serve static files (by default they are located in /static and /uploads directories under the project root). 

Built-in Flask server is for debugging purposes. It is therefore advised to wait until this engine gets WSGI support and then use it as regular WSGI application through separate web server. Some settings, such as maximum upload file size or maximum requests per second, should also be set in your web server.

### Features
##### Already implemented
- Standard anonymous imageboard functionality
- Attachments support via files uploading and links
- Attach YouTube videos
- Attach Prostopleer tracks
- Multiple attachments per post
- Automatic threads updating with AJAX
- Bold, italic, quotes and other formatting features
- Support for multiple boards
- Rendering with Jinja2
- Almost awesome front-end
- Russian frontend (smells like vodka!)

##### To be added
- Posting with AJAX
- Client user settings
- Admin panel
- Captcha support
- REST API
- Even more awesome front-end
- Caching
- Virtualenv support
- Run as WSGI application
- i18n (particularly English language support)

### Dependencies
Everything is easily installable with pip:
```
pip install flask flask-sqlalchemy flask-wtf requests pyparsing bleach pyyaml wand
```
- Python 3.4 or newer
- [Flask](http://github.com/mitsuhiko/flask)
- [Flask-SQLAlchemy](http://github.com/mitsuhiko/flask-sqlalchemy)
- [Flask-WTF](http://github.com/lepture/flask-wtf)
- [requests](https://github.com/kennethreitz/requests)
- [pyparsing](http://pyparsing.wikispaces.com/)
- [bleach](https://github.com/jsocol/bleach)
- [pyyaml](http://pyyaml.org/)
- [Wand](https://github.com/dahlia/wand/) with [ImageMagick](http://www.imagemagick.org/) (in nearest future [Pillow](https://python-pillow.github.io/) will also be supported)
