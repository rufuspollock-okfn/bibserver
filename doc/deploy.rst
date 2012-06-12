.. _deploy:

==========
Deployment
==========

Pre-requisites
==============

This example is for installing bibserver to run bibsoup.net, but applies to 
other instances - just change relevant parts e.g. domain name and so on.

These instructions work on an ubuntu / debian machine, and explain how to get a
stable deployment using:

 * git (to get latest copy of code)
 * nginx (the web server that proxies to the web app)
 * python2.7+, pip, virtualenv (required to run the app)
 * gunicorn (runs the web app that receives the proxy from nginx)
 * supervisord (keeps everything up and running)


nginx config
============

Create an nginx site config named e.g. bibsoup.net
default location is /etc/nginx/sites-available
(for OKF machines should be in ~/etc/nginx/sites-available then symlinked)
then symlink from /etc/nginx/sites-enabled

    upstream bibsoup_app_server {
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


supervisord config
==================

Create a supervisord config named e.g. bibsoup.net.conf
- the default location for this is /etc/supervisor/conf.d
(for OKF machines, should be put in ~/etc/supervisor/conf.d then symlinked)

    [program:bibsoup.net]
    command=/home/okfn/var/srvc/%(program_name)s/bin/gunicorn -w 4 -b 127.0.0.1:5050 bibserver.web:app
    user=www-data
    directory=/home/okfn/var/srvc/%(program_name)s/src/bibserver
    stdout_logfile=/var/log/supervisor/%(program_name)s-access.log
    stderr_logfile=/var/log/supervisor/%(program_name)s-error.log
    autostart=true


Install bibserver
=================

Create a virtualenv and get the latest bibserver code installed.
Bibserver requires python2.7+ so make sure that is available on your system, 
then start a virtualenv to run it in

    virtualenv -p python2.7 bibsoup.net --no-site-packages
    cd bibsoup.net
    mkdir src
    cd bin
    source activate
    cd ../src
    git clone https://github.com/okfn/bibserver
    cd bibserver
    python setup.py install


Currently, setup.py install does not result in running system because 
config.json cannot be found. So, do dev install. This will be fixed asap

    pip install -e .


Then install gunicorn into the virtualenv

    pip install gunicorn


Now create a local_config.json with details as necessary
for example check the ES index you with to use for this instance (default is bibserver)

    {
        "debug": false,
        "port": 5050,
        "ELASTIC_SEARCH_DB" : "bibserver_something",
        "ELASTIC_SEARCH_HOST" : "localhost:9200"
    }


Now run bibserver directly to check it is working
- this requires elasticsearch to be up and running, as it attempts to create indices.

If it works, you should see confirmation of creation of the index and the mappings; 
if all good, kill it and move on. If not, debug the issues.

    python bibserver/web.py


If the above step failed to push the mappings, you can do so manually.
A command such as the following, augmented for your ES index URL and your index name,
should do the job for you (default mappings are in config.json)
(remember to do record and collection)

    curl -X PUT localhost:9200/bibserver/record/_mapping -d '{
        "record" : {
            "date_detection" : false,
            "dynamic_templates" : [
                {
                    "default" : {
                        "match" : "*",
                        "match_mapping_type": "string",
                        "mapping" : {
                            "type" : "multi_field",
                            "fields" : {
                                "{name}" : {"type" : "{dynamic_type}", "index" : "analyzed", "store" : "no"},
                                "exact" : {"type" : "{dynamic_type}", "index" : "not_analyzed", "store" : "yes"}
                            }
                        }
                    }
                }
            ]
        }
    }'


Enable everything
=================

In the case of OKF service deployment, make symbolic links from the supervisor 
and nginx files which should be in the ~/etc folder into the /etc/nginx/sites-available
and /etc/supervisor/conf.d folders, then make symbolic link from /etc/nginx/sites-available
into /etc/nginx/sites-enabled - if you do not use this pattern, just put the config 
directly in /etc/nginx/sites-available and symlink from there into sites-enabled

    cd /etc/nginx/sites-available
    ln -s ~/etc/nginx/sites-available/bibsoup.net .
    cd /etc/supervisor/conf.d
    ln -s ~/etc/supervisor/conf.d/bibsoup.net.conf .


Then enable the new nginx and supervisor settings

    cd /etc/nginx/sites-enabled
    ln -s ../sites-available/bibsoup.net .
    /etc/init.d/nginx reload
    supervisorctl reread
    supervisorctl update


Configure your domain name to point at your server, and it should work.


