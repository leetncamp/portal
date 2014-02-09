<VirtualHost *:80>
    ServerName upload.neurovigil.com
    ServerAlias upload
    CustomLog /var/log/apache2/upload.neurovigil.com.access.log combined
    ErrorLog /var/log/apache2/upload.neurovigil.com.error.log
    RedirectPermanent / https://upload.neurovigil.com/
</VirtualHost>

<VirtualHost *:443>
    ServerName upload.neurovigil.com
    ServerAlias upload
    CustomLog /var/log/apache2/upload.neurovigil.com.access.log combined
    ErrorLog /var/log/apache2/upload.neurovigil.com.error.log
    SSLEngine on
    SSLCertificateFile /etc/ssl/certs/neurovigil.com.crt
    SSLCertificateKeyFile /etc/ssl/private/neurovigil.key


    Alias /static/admin /www/upload.neurovigil.com/admin
    Alias /static/media /www/upload.neurovigil.com/media
    <Directory /www/djnipscc/media>
      Order deny,allow
      Allow from all
    </Directory>
    <Directory /www/djnipscc/admin>
      Order deny,allow
      Allow from all
    </Directory>


    WSGIScriptAlias / /www/upload.neurovigil.com/project/wsgi.py


</VirtualHost>
