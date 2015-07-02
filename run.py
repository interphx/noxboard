#! python3.4
import sys
from app import application, config

if __name__ == '__main__':
    application.run(debug=config['app']['debug'], host=config['flask']['HOST'], port=config['flask']['PORT'])