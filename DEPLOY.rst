# this example is for installing bibserver to run bibsoup.net, but applies to 
# other instances - just change relevant parts e.g. domain name and so on
# these instructions work on an ubuntu / debian machine, and has some pre-requisites
# nginx, supervisord, git, python2.7+, virtualenv, pip


# create an nginx site config named e.g. bibsoup.net
# default location is /etc/nginx/sites-available
# for OKF machines should be in ~/etc/nginx/sites-available then symlinked (see below)
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
# for OKF machines, should be put in ~/etc/supervisor/conf.d then symlinked (see below)
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


# currently, setup.py install does not result in running system because 
# config.json cannot be found. So, do dev install. This will be fixed on 
# move to Flask config method
pip install -e .


# and install gunicorn into the virtualenv
pip install gunicorn


# create a local_config.json with details as necessary
# for example check the ES index you with to use for this instance (default is bibserver)
{
    "debug": false,
    "ELASTIC_SEARCH_HOST" : "elasticsearch.okserver.org:9200"
}


# run bibserver directly to check it is working
# requires elasticsearch to be up and running, as will attempt to create indices
# if it works, kill it and move on. If not, debug the issues
python bibserver/web.py


# in the case of OKF service deployment, make symbolic links from the supervisor 
# and nginx files which should be in the ~/etc folder into the /etc/nginx/sites-available
# and /etc/supervisor/conf.d folders, then make symbolic link from /etc/nginx/sites-available
# into /etc/nginx/sites-enabled
cd /etc/nginx/sites-available
ln -s ~/etc/nginx/sites-available/bibsoup.net .
cd /etc/supervisor/conf.d
ln -s ~/etc/supervisor/conf.d/bibsoup.net.conf .


# to enable the new settings
cd /etc/nginx/sites-enabled
ln -s ../sites-available/bibsoup.net .
/etc/init.d/nginx reload
supervisorctl reread
supervisorctl update


# point your domain name at the server, and it should work
