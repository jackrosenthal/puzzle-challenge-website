# This file could be used to deploy the site in production
#
# Set the PASTE_CONFIG environment variable in your web server
# to the path of your config INI

import os
PASTE_CONFIG = os.getenv('PASTE_CONFIG')

import logging.config
logging.config.fileConfig(PASTE_CONFIG)

from paste.deploy import loadapp
application = loadapp('config:{}'.format(PASTE_CONFIG))