from flask import Flask
import os

app = Flask(__name__)
#  flask WTF использует встроенную защиту от CSRF атак, генерится ключ так:
#  head -c 24 /dev/urandom > secret_key
filename = 'secret_key'
#  заменяем инстанс на имя нашей папки с приложением (временный хак)
filename = os.path.join(app.instance_path.replace('instance', 'app'), filename)
app.config['SECRET_KEY'] = open(filename, 'rb').read()
from app import views
