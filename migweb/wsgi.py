"""
WSGI config for migweb project.

This module contains the WSGI application used by Django's development server
and any production WSGI deployments. It should expose a module-level variable
named ``application``. Django's ``runserver`` and ``runfcgi`` commands discover
this application via the ``WSGI_APPLICATION`` setting.

Usually you will have the standard Django WSGI application here, but it also
might make sense to replace the whole Django WSGI application with a custom one
that later delegates to the Django one. For example, you could introduce WSGI
middleware here, or combine a Django application with an application of another
framework.

"""

from __future__ import absolute_import

# virtualenv magic #yolo
activate_env = '/home/webdev/.virtualenvs/migweb/bin/activate_this.py'
# execfile(activate_env, dict(__file__=activate_env))

import os

import sys
path = '/srv/www'
if path not in sys.path:
    sys.path.append(path)

# We defer to a DJANGO_SETTINGS_MODULE already in the environment. This breaks
# if running multiple sites in the same mod_wsgi process. To fix this, use
# mod_wsgi daemon mode with each site in its own daemon process, or use
# os.environ["DJANGO_SETTINGS_MODULE"] = "migweb.settings"
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "migweb.settings")


# This application object is used by any WSGI server configured to use this
# file. This includes Django's development server, if the WSGI_APPLICATION
# setting points here.
from django.core.wsgi import get_wsgi_application
from apig_wsgi import make_lambda_handler
application = get_wsgi_application()
lambda_handler = make_lambda_handler(application)

# Apply WSGI middleware here.
# from helloworld.wsgi import HelloWorldApplication
# application = HelloWorldApplication(application)

# From https://devcenter.heroku.com/articles/django-memcache
# Fix django closing connection to MemCachier after every request (#11331)
from django.core.cache.backends.memcached import BaseMemcachedCache
BaseMemcachedCache.close = lambda self, **kwargs: None
