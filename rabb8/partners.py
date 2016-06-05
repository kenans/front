import sys
import os
import logging
import hmac
import urllib
import time
import random

import simplejson as json

import tornado.options
import tornado.ioloop
import tornado.web
import tornado.wsgi
import tornado.template
import tornado.httpclient as httpclient

import setting
from setting import settings
from setting import conn
#from BeautifulSoup import BeautifulSoup

import jsmin

import main


class PartnersLoginHandler(main.BaseHandler):
    def get(self):
        next = self.get_argument("next", "")
        if next:
            next = "?next="+next
        self.render("./template/partners/login.html", user=self.current_user, next=next, version=setting.VERSION)

    def post(self):
        if self.get_argument("password") != '1234':
            self.redirect("/partners/login")
        else:
            self.write("hello")


class PartnersDashboardHandler(main.BaseHandler):
    def get(self):
        next = self.get_argument("next", "")
        if next:
            next = "?next="+next

        collection = conn.query("SELECT * FROM collection WHERE user_id = %s", self.current_user['id'])
        self.render("./template/partners/dashboard.html", user=self.current_user, collection=collection, next=next, version=setting.VERSION)


class WidgetHandler(main.BaseHandler):
    def get(self, type):
        print self.request.query == ""

        types = {'1x4.js':4, '2x2.js':4, '4x1.js':4, '2x2s.js':4, '6x1s.js':6, 'test.js':6}
        if type in types: #404
            ret = types[type]
        else:
            self.finish()
            return

        #memcache for every table update
        links = [(i["weight"], i["collection_id"]) for i in conn.query("SELECT collection_id, weight FROM widget_links WHERE weight > 0")]
        collection_ids = WidgetHandler.weighted_shuffle(links, ret)
        collection_ids.sort()
        #print collection_ids

        #cache by collection_ids hash
        collection = conn.query("SELECT * FROM collection WHERE id in %s ORDER BY id DESC", collection_ids)
        #random.shuffle(collection)

        #jsmin.jsmin doesnt work here
        self.write(self.render_string("./template/widget/%s" % type, images=collection))

    @classmethod
    def weighted_shuffle(cls, choices, ret):
        new_choices = []
        for i in range(ret):
            total = sum(w for w,c in choices)
            r = random.uniform(0, total)
            upto = 0
            for w, c in choices:
                if upto+w > r:
                    choices.remove((w, c))
                    new_choices.append(c)
                    break
                upto += w
        #new_choices.append(choices[0][0])
        return new_choices
