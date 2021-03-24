import os

basedir = os.path.abspath(os.path.dirname(__file__))

class Config(object):
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'asdf'
    DATA_DIR = os.path.join(basedir, 'data')
    FILTER_DIR = os.path.join(basedir, 'filter')