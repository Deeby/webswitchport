# WebSwitchPort

Веб-интерфейс для автоматизиации рутинных действий по поиску и переводу портов на устройствах cisco.

## Настройка и запуск

cisco.yaml - основной конфигурационный файл, с описанием устройств. Должен содержать информацию о ядре, обо всех коммутаторах агрегации и доступа - это необходимо для корректной работы утилиты поиска порта по мак-адресу.

Запуск приложения через gunicorn:

```
/home/user/venv/bin/gunicorn --bind 127.0.0.1:8000 --workers 3 run:app directory=/home/user/webswitchport
```
Где venv - виртуальное окружение с зависимостями. В качестве фронтэнда может быть использован, например, nginx в режиме прокси:

```
upstream server.ru {
    server 127.0.0.1:8000 fail_timeout=0;
}

server {
    listen 80;
    server_name server.ru;
    rewrite ^/(.*) https://server.ru/$1 permanent;
}

server {
    listen 443;
    client_max_body_size 4G;
    server_name server.ru;
    access_log  /home/user/webswitchport/myproject.access.log;
    keepalive_timeout 5;

    ssl on;
    ssl_certificate /etc/nginx/sites-available/webswitchport.crt;
    ssl_certificate_key /etc/nginx/sites-available/webswitchport.key;

    ssl_session_timeout 5m;

    ssl_protocols SSLv3 TLSv1;
    ssl_ciphers DHE-RSA-AES256-SHA:DHE-RSA-AES128-SHA:EDH-RSA-DES-CBC3-SHA:AES256-SHA:DES-CBC3-SHA:AES128-SHA:RC4-SHA:RC4-MD5;
    ssl_prefer_server_ciphers on;

    root /home/user/webswitchport/app/static;
    
    location / {
        proxy_pass http://server.ru;
    }

    location ~ ^/(static|media)/ {
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header Host $http_host;
        proxy_redirect off;
        if (!-f $request_filename) {
            proxy_pass http://server.ru;
            break;
        }
     }
}
```

## Поиск порта по mac-адресу

Поиск порта по маку выполняется через утилиту командной строки findport.py, которая может быть использована как самостоятельное приложение:

```
$ python findport.py
usage: findport.py [-h] [-r [ROOT]] -m [MAC] [-d [DOMAIN]] [-t] [-e]
```

## Особенности реализации

1. Авторизация производится путем попытки логина на случайно выбранное устройство - все устройства должны иметь идентичные настройки пользователей или использовать, например, tacacs.
2. Логин и пароль хранятся параметрах сессии на стороне сервера до ее завершения.
3. Любое действие выполняется сабмитом всей формы и требует перезагрузки страницы.
4. Порты trunk не показываются в списке портов, доступных для настройки. 
5. Учетная запись для перевода портов должна иметь следующие минимальные права доступа:

privilege configure level 5 interface
privilege interface level 5 switchport access vlan
privilege interface level 5 description
privilege exec level 5 write memory
privilege exec level 5 configure terminal
а также все соответствующие show привилегии.

6. Для поиска портов по mac адресу достаточно только show привилегий.
7. Поиск портов использует cdp и опирается на то, что на всех устройствах задано одинаковое доменное имя. При использовании findport.py его нужно явно указывать как аргумент.
