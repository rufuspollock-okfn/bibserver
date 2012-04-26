# install nginx and supervisor
apt-get install nginx supervisord


# create an nginx site config named e.g. bibsoup.net
# default location is /etc/nginx/sites-available
# then symlink from /etc/nginx/sites-enabled
upstream bibsoup_app_server {
	# server unix:/tmp/gunicorn.sock fail_timeout=0;
	# For a TCP configuration:
	server 127.0.0.1:5050 fail_timeout=0;
}

server {
	server_name  bibsoup.net;

	access_log  /var/log/nginx/bibsoup.net.access.log;

	server_name_in_redirect  off;

	client_max_body_size 20M;

	location / {
		## straight-forward proxy
		proxy_redirect off;
	  	proxy_connect_timeout 75s;
	  	proxy_read_timeout 180s;
		proxy_set_header Host $host;
		proxy_set_header X-Real-IP $remote_addr;
		proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;

		proxy_pass   http://bibsoup_app_server;
	}
}


# create a supervisord config named e.g. bibsoup.net.conf
# default location is /etc/supervisor/conf.d
[program:bibsoup.net]
command=/home/okfn/var/srvc/%(program_name)s/bin/gunicorn -w 4 -b 127.0.0.1:5050 bibserver.web:app
user=www-data
directory=/home/okfn/var/srvc/%(program_name)s/src/bibserver
stdout_logfile=/var/log/supervisor/%(program_name)s-access.log
stderr_logfile=/var/log/supervisor/%(program_name)s-error.log
autostart=true


# create a virtualenv and get the latest bibserver code installed
# bibserver requires python2.7+ so make sure that is available on your system 
virtualenv -p python2.7 bibsoup.net --no-site-packages
cd bibsoup.net
mkdir src
cd bin
source activate
cd ../src
git clone https://github.com/okfn/bibserver
cd bibserver
python setup.py install


# create a local_config.json with details as necessary
{
    "ELASTIC_SEARCH_HOST" : "elasticsearch.okserver.org:9200"
}


# in the case of OKF service deployment, make symbolic links from the supervisor 
# and nginx files which should be in the ~/etc folder into the /etc/nginx/sites-available
# and /etc/supervisor/conf.d folders, then make symbolic link from /etc/nginx/sites-available
# into /etc/nginx/sites-enabled


