<VirtualHost *:80>
    ServerName upload.neurovigil.com
    ServerAlias upload
    CustomLog /var/log/apache2/upload.neurovigil.com.access.log combined
    ErrorLog /var/log/apache2/upload.neurovigil.com.error.log
    RewriteEngine on
    #RewriteCond %{HTTP_HOST}  !^upload.neurovigil.com [NC]
    #RewriteCond %{HTTP_HOST}  !^$
    RewriteRule ^/(.*)    https://upload.neurovigil.com/$1 [L,R=301]

</VirtualHost>

<VirtualHost *:443>
    ServerName upload.neurovigil.com
    ServerAlias upload
    CustomLog /var/log/apache2/upload.neurovigil.com.access.log combined
    ErrorLog /var/log/apache2/upload.neurovigil.com.error.log
    Alias /static/admin /var/www/upload.neurovigil.com/portal/admin
    Alias /static/uploads /var/www/upload.neurovigil.com/portal/uploads

    SSLEngine on
    SSLCertificateFile /etc/ssl/certs/neurovigil.com.crt
    #SSLCertificateKeyFile /etc/ssl/private/upload.neurovigil.com.key
    SSLCertificateKeyFile /etc/ssl/private/neurovigil.key

    <Directory /var/www/upload.neurovigil.com/portal/uploads>
      Order deny,allow
      Allow from all
    </Directory>

    <LocationMatch .*>
	SSLRequireSSL
    </LocationMatch>


    WSGIScriptAlias / /var/www/upload.neurovigil.com/portal/project/wsgi.py
</VirtualHost>

