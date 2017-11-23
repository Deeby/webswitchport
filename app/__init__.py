from flask import Flask
from flask_session import Session
from werkzeug.contrib.fixers import ProxyFix

# head -c 24 /dev/urandom > secret_key
# filename = 'secret_key'
# filename = os.path.join(app.instance_path.replace('instance', 'app'), filename)
# app.config['SECRET_KEY'] = open(filename, 'rb').read()
app = Flask(__name__)
# для gunicorn --bind 0.0.0.0:8000 --workers 3 run:app
app.wsgi_app = ProxyFix(app.wsgi_app)
app.config['SECRET_KEY'] = 'akshfklasdhfkasdf98asd7fasd'
app.config['SESSION_TYPE'] = 'filesystem'
sess = Session()
sess.init_app(app)

from app import views
