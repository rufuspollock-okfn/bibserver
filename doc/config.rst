=============
Configuration
=============

Configuration is managed via some key files. To make changes, just use 
local_config.json.


config.json
===========

The main default config - does not need to be altered. Instead, it is updated 
by local_config.json


local_config.json
=================

This is where configurations should be set for you particular instances. These 
are the various values you can set:


config.py
=========

This is the config class - it loads config in from config.json, then overrides 
with updates from local_config.json. The config object is then made available 
and can be imported elsewhere in the app. Changes to config need only happen 
in local_config.json.


core.py
=======

This is where configure_app and create_app are definedm which prepare the flask 
settings for the app to run. This is imported by web.py when the app is created.
Settings are read from config.


default_settings.py
===================

Contains a "secure-key" setting for flask config
