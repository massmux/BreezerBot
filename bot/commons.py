import configparser
import simplejson as json
import redis
import os
import threading
import bbot

settings = configparser.ConfigParser()
settings.read('settings.ini')

""" Bot initialization """
bot = bbot.BBot(settings['bot']['api_key'])
bot.about = "about"
bot.owner = "ownser"
bot.after_help = "help"

""" redis initialization """
from db import *

