import sys
import os
import logging
import hmac
import urllib
import time
import urlparse

import simplejson as json

import tornado.options
import tornado.ioloop
import tornado.web
import tornado.wsgi
import tornado.template
import tornado.httpclient as httpclient

from setting import CATEGORIES
from setting import CITIES
from setting import VERSION

from setting import settings
from setting import conn
from BeautifulSoup import BeautifulSoup


class BaseHandler(tornado.web.RequestHandler):
    def get_current_user(self):
        user_json = self.get_secure_cookie("user")
        if not user_json: return None
        return tornado.escape.json_decode(user_json)


class MainHandler(BaseHandler):
    def get(self, city="Singapore"):
        next = self.get_argument("next", "")
        if next:
            next = "?next="+next
        global CATEGORIES
        global CITIES

        if not self.current_user:
            self.collection = conn.query("SELECT * FROM collection ORDER BY id DESC LIMIT 0, 20")

        self.render("./template/index.html", user=self.current_user, categories=CATEGORIES, cities=CITIES, next=next, version=VERSION)


class ToolsHandler(BaseHandler):
    def get(self):
        next = self.get_argument("next", "")
        if next:
            next = "?next="+next
        self.render("./template/tools.html", user=self.current_user, categories=CATEGORIES, next=next, version=VERSION)


class Rabb8itHandler(BaseHandler):
    def get(self):
        url = self.get_argument("url", "")
        next = "?next=/rabb8it?url=%s"%url
        self.render("./template/rabb8it.html", user=self.current_user, categories=CATEGORIES, next=next, url=url, version=VERSION)


class WallAPIHandler(BaseHandler):
    def get(self):
        page = self.get_argument("page", "0")
        if not page.isdigit():
            return
        page = int(page)

        board_id = self.get_argument("board_id", "0")
        if not board_id.isdigit():
            return
        board_id = int(board_id)
        if board_id == 0:
            collection = conn.query("SELECT * FROM collection ORDER BY id DESC LIMIT %s, 20", page*20)
        else:
            collection = conn.query("SELECT * FROM collection WHERE board_id = %s ORDER BY id DESC LIMIT %s, 20", board_id, page*20)

        if self.current_user:
            ids = tuple([i["id"] for i in collection])
            if len(ids) > 1:
                likes = conn.query("SELECT * FROM likes WHERE user_id=%s AND collection_id IN %s", self.current_user["id"], ids)
            elif len(ids) == 1:
                likes = conn.query("SELECT * FROM likes WHERE user_id=%s AND collection_id = %s", self.current_user["id"], ids[0])
            else:
                self.write({"collection":[]})
                return

            liked = set([i["collection_id"] for i in likes])
            for i in collection:
                i["liked"] = i["id"] in liked

        self.write({"collection":collection})


class GetAPIHandler(BaseHandler):
    def parse_src(self, src):
        if src.startswith("http://") or src.startswith("https://") :
            return src
        elif src.startswith("/"):
            o = urlparse.urlparse(self.url)
            host = o.scheme + "://" + o.netloc
            return host + src
        else:
            return self.url + src

    def handle_request(self, response):
        if response.code == 200:
            soup = BeautifulSoup(response.body)
            images = [{"src" : self.parse_src(i.get("src", ""))} for i in soup.findAll("img") if i.get("src")]
            self.finish({"images": images, "url": self.url, "error":None})

        #self.finish({"status": response.code, "url": response.request.url})

    @tornado.web.asynchronous
    def get(self):
        self.url = self.get_argument("url")
        http_client = httpclient.AsyncHTTPClient()
        http_client.fetch(self.url, self.handle_request)

class CollectionAPIHandler(BaseHandler):
    #@tornado.web.authenticated
    def post(self):
        if self.current_user:
            title = self.get_argument("title","")
            body = self.get_argument("body","")
            width = self.get_argument("width")
            height = self.get_argument("height")
            image_url = self.get_argument("image_url")
            source_url = self.get_argument("source_url")

            board_id = self.get_argument("board_id")
            user_id = self.current_user["id"]
            likes = 0

            conn.execute("INSERT INTO collection (title, body, width, height, likes, image_url, source_url, user_id, board_id)\
                          VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)",\
                          title, body, width, height, likes, image_url, source_url, user_id, board_id)
            self.finish({"error":None})

    def delete(self):
        collection_id = self.get_argument("id")
        if self.current_user:
            rows = conn.execute_rowcount("DELETE FROM collection WHERE id = %s and user_id = %s", collection_id, self.current_user["id"])
            print rows
            #need to delete all likes
            if rows == 1:
                conn.execute("DELETE FROM likes WHERE collection_id = %s", collection_id)

            self.finish({"error":None})

    def get(self):
        collection_id = self.get_argument("id")
        collection = conn.get("SELECT * FROM collection WHERE id=%s", collection_id)
        if not collection:
            self.finish('')
            return

        liked = conn.get("SELECT * FROM likes WHERE collection_id = %s", collection_id)
        collection["liked"] = liked is not None

        self.finish(collection)

class LikeAPIHandler(BaseHandler):
    def post(self):
        if self.current_user:
            collection_id = self.get_argument("id")
            user_id = self.current_user["id"]

            conn.execute("UPDATE collection SET likes = likes + 1 \
                          WHERE id = %s",\
                          collection_id)

            conn.execute("INSERT INTO likes (user_id, collection_id)\
                          VALUES (%s, %s)",\
                          user_id, collection_id)

class BoardsAPIHandler(BaseHandler):
    #@tornado.web.authenticated
    def get(self):
        if self.current_user:
            board_id = self.get_argument("id", None)
            if board_id:
                board = conn.get("SELECT * FROM boards WHERE user_id = %s and id = %s", self.current_user["id"], board_id)
                self.finish({"board": board,"error":None})
                return
            boards = conn.query("SELECT * FROM boards WHERE user_id = %s", self.current_user["id"])
            self.finish({"boards":boards, "error":None})
        else:
            self.finish({"error":"login required"})

    def post(self):
        if self.current_user:
            board_id = self.get_argument("board_id")
            name = self.get_argument("name")
            category_id = self.get_argument("category_id")

            conn.execute("UPDATE boards SET name = %s, category_id = %s WHERE id = %s and user_id = %s", name, category_id, board_id, self.current_user["id"])
            self.finish({"error":None})

    def put(self):
        if self.current_user:
            name = self.get_argument("name")
            category_id = self.get_argument("category_id")

            board = conn.get("SELECT * FROM boards WHERE user_id = %s and name = %s", self.current_user["id"], name)

            if board:
                self.finish({"error":"duplicated name"})
            else:
                conn.execute("INSERT INTO boards (user_id, name) VALUES (%s,%s)", self.current_user["id"], name)
                self.finish({"error":None})

    def delete(self):
        if self.current_user:
            board_id = self.get_argument("board_id")
            name = self.get_argument("name")
            category_id = self.get_argument("category_id")

            board = conn.get("SELECT * FROM boards WHERE user_id = %s and name = %s and id= %s and category_id = %s", self.current_user["id"], name, board_id, category_id)

            if board:
                conn.execute("DELETE FROM boards WHERE id = %s and user_id = %s", board_id, self.current_user["id"])
                self.finish({"error":None})
            else:
                self.finish({"error":"something else changed"})

class CommentsAPIHandler(BaseHandler):
    def get(self):
        collection_id = self.get_argument("id")
        comments = conn.query("SELECT * FROM comments WHERE collection_id = %s", collection_id)
        self.finish({"comments":comments, "collection_id":collection_id, "error":None})


    def post(self):
        #post comment
        if self.current_user:
            collection_id = self.get_argument("id")
            comment = self.get_argument("comment")
            conn.execute("INSERT INTO comments (collection_id, comment, user_id, create_time) VALUES (%s,%s,%s,%s)", collection_id, comment,self.current_user["id"], int(time.time()))
            self.finish({"error":None})


class CityAPIHandler(BaseHandler):
    def handle_request(self, response):
        if response.code == 200:
            lines = response.body.split("\n")
            if len(lines) >= 3 and self.current_user:
                city = lines[1][6:]
                if city == "(Private Address)":
                    city = "Singapore"
                #current_user = conn.get("SELECT * FROM users WHERE id = %s",\
                #                         self.current_user["id"])
                self.finish({"city": self.current_user.get("city",""), "guess_city": city, "error":None})
                return

        self.finish({"error": "query failed"})

    @tornado.web.asynchronous
    def get(self):
        ip = self.request.headers.get("X-Forwarded-For", None) or self.request.remote_ip
        url = "http://api.hostip.info/get_html.php?ip=%s" % ip
        http_client = httpclient.AsyncHTTPClient()
        http_client.fetch(url, self.handle_request)

    @tornado.web.authenticated
    def post(self):
        city = self.get_argument("city")
        conn.execute("UPDATE users SET city = %s WHERE id = %s",\
                        city, self.current_user["id"])

        self.current_user["city"] = city
        self.set_secure_cookie("user", tornado.escape.json_encode(self.current_user))


class CountryAPIHandler(BaseHandler):
    def handle_request(self, response):
        if response.code == 200:
            lines = response.body.split("\n")
            if len(lines) >= 3 and self.current_user:
                country = lines[0][9:]
                if country == "(Private Address) (XX)":
                    country = "SINGAPORE"
                self.finish({"country": self.current_user.get("country",""), "guess_country": country, "error":None})
                return

        self.finish({"error": "query failed"})

    @tornado.web.asynchronous
    def get(self):
        ip = self.request.headers.get("X-Forwarded-For", None) or self.request.remote_ip
        url = "http://api.hostip.info/get_html.php?ip=%s" % ip
        http_client = httpclient.AsyncHTTPClient()
        http_client.fetch(url, self.handle_request)

    @tornado.web.authenticated
    def post(self):
        country = self.get_argument("country")
        conn.execute("UPDATE users SET country = %s WHERE id = %s",\
                        country, self.current_user["id"])

        self.current_user["country"] = country
        self.set_secure_cookie("user", tornado.escape.json_encode(self.current_user))


class FloatingZoneHandler(BaseHandler):
    def get(self):
        global CATEGORIES
        self.render("./template/floating_zoo.html", user=self.current_user, categories=CATEGORIES, next="/floating_zoo", version=VERSION)


