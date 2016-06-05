import sys
import os
import logging
import hmac
import urllib
import time

import simplejson as json

#import wsgiref.simple_server
#import wsgiref.handlers
import tornado.options
import tornado.ioloop
import tornado.web
import tornado.wsgi
import tornado.template
import tornado.httpclient as httpclient

from setting import settings
from setting import conn
from BeautifulSoup import BeautifulSoup

import main
import auth
import partners

application = tornado.web.Application([
    (r"/floating_zoo", main.FloatingZoneHandler),

    (r"/(\d+)", main.MainHandler),
    (r"/", main.MainHandler),
    (r"/tools", main.ToolsHandler),
    (r"/rabb8it", main.Rabb8itHandler),
    (r"/test", main.BaseHandler),

    (r"/auth/facebook", auth.FacebookGraphHandler),
    (r"/auth/google", auth.GoogleHandler),
    #(r"/auth/twitter", TwitterHandler),
    (r"/auth/logout", auth.LogoutHandler),

    (r"/api/wall", main.WallAPIHandler),
    (r"/api/get", main.GetAPIHandler),
    (r"/api/collection", main.CollectionAPIHandler),
    (r"/api/like", main.LikeAPIHandler),
    (r"/api/comments", main.CommentsAPIHandler),
    (r"/api/boards", main.BoardsAPIHandler),
    (r"/api/city", main.CityAPIHandler),
    (r"/api/country", main.CountryAPIHandler),

    (r"/partners", partners.PartnersDashboardHandler),
    (r"/partners/login", partners.PartnersLoginHandler),

    (r"/widget/(.*)", partners.WidgetHandler),

    #(r"/(.*)", main.MainHandler),

    #(r"/()", tornado.web.StaticFileHandler, dict(path=settings['static_path']+'/index.html')),
    (r"/(.*)", tornado.web.StaticFileHandler, dict(path=settings['static_path'], default_filename='index.html')),
], **settings)

if __name__ == "__main__":
    tornado.options.parse_command_line()
    application.listen(int(sys.argv[1]))
    tornado.ioloop.IOLoop.instance().start()
