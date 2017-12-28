from flask import Flask
from flask_session import Session
from werkzeug.contrib.fixers import ProxyFix
import os

app = Flask(__name__)

# head -c 24 /dev/urandom > secret_key
filename = 'secret_key'
filename = os.path.join(app.instance_path.replace('instance', 'app'), filename)
app.wsgi_app = ProxyFix(app.wsgi_app)
app.config['SECRET_KEY'] = open(filename, 'rb').read()
# app.config['SECRET_KEY'] = ''.join(random.SystemRandom().choice(string.digits + string.ascii_letters) for _ in range(30))
app.config['SESSION_TYPE'] = 'filesystem'
app.config['PERMANENT_SESSION_LIFETIME'] = 1800
sess = Session()
sess.init_app(app)


@app.before_request
def make_session_permanent():
    sess.permanent = True


from app import views
