import tornado.web
import tornado.template
import tornado.database
import tornado.auth
import tornado.escape

from setting import settings
from setting import conn


class TwitterHandler(tornado.web.RequestHandler,
                     tornado.auth.TwitterMixin):
    @tornado.web.asynchronous
    def get(self):
        if self.get_argument("oauth_token", None):
            self.get_authenticated_user(self.async_callback(self._on_auth))
            return
        self.authorize_redirect()

    def _on_auth(self, user):
        print type(user)
        print user
        if not user:
            raise tornado.web.HTTPError(500, "Twitter auth failed")
        self.redirect("/")

        '''
        current_user = conn.get("SELECT * FROM users WHERE email = %s and type = 't'",\
                                 user["email"])

        if current_user is None:
            self.user["id"] = conn.execute("INSERT INTO users (type, email, name) VALUES ('g', %s, %s)",\
                                       user["email"], user["name"])
            self.user["pingball"] = 0
        else:
            self.user["id"] = current_user["id"]
            self.user["pingball"] = current_user["pingball"]

        #print self.user
        self.set_secure_cookie("user", tornado.escape.json_encode(self.user))

        self.redirect(self.redirect_url)
        '''

        # Save the user using, e.g., set_secure_cookie()

class GoogleHandler(tornado.web.RequestHandler,
                    tornado.auth.GoogleMixin):
    @tornado.web.asynchronous
    def get(self):
        if self.get_argument("openid.mode", None):
            self.redirect_url = self.get_argument("next", "/")
            self.get_authenticated_user(self.async_callback(self._on_auth))
            return
        self.authenticate_redirect()
        #self.finish()

    def _on_auth(self, user):
        if not user:
            raise tornado.web.HTTPError(500, "Google auth failed")
        self.user = user

        current_user = conn.get("SELECT * FROM users WHERE email = %s and type = 'g'",\
                                 user["email"])

        if current_user is None:
            self.user["id"] = conn.execute("INSERT INTO users (type, email, name) VALUES ('g', %s, %s)",\
                                       user["email"], user["name"])
            self.user["city"] = ""
        else:
            self.user["id"] = current_user["id"]
            self.user["city"] = current_user["city"]

        ip = self.request.headers.get("X-Forwarded-For", None) or self.request.remote_ip
        conn.execute("UPDATE users SET last_login_ip = %s WHERE id = %s",\
                      ip, self.user["id"])

        self.set_secure_cookie("user", tornado.escape.json_encode(self.user))

        if self.redirect_url == "/":
            self.redirect_url == "/"+self.user["city"]
        self.redirect(self.redirect_url)


class FacebookGraphHandler(tornado.web.RequestHandler,
                           tornado.auth.FacebookGraphMixin):
    @tornado.web.asynchronous
    def get(self):
        if self.get_argument("code", False):
            self.redirect_url = self.get_argument("next", "/")
            self.get_authenticated_user(
                redirect_uri='http://'+self.request.host+'/auth/facebook',
                client_id=self.settings["facebook_api_key"],
                client_secret=self.settings["facebook_secret"],
                code=self.get_argument("code"),
                callback=self._on_auth)
            return

        self.authorize_redirect(redirect_uri='http://'+self.request.host+'/auth/facebook',
                                client_id=self.settings["facebook_api_key"],
                                extra_params={}) #"scope": "email"

    @tornado.web.asynchronous
    def _on_auth(self, user):
        if not user:
            raise tornado.web.HTTPError(500, "Facebook auth failed")
        self.user = user
        #print user

        #login or create account with fb
        current_user = conn.get("SELECT * FROM users WHERE facebook_id = %s and type = 'f'",\
                                 user["id"])

        if current_user is None:
            self.user["id"] = conn.execute("INSERT INTO users (type, facebook_id, name) VALUES ('f', %s, %s)",\
                                       user["id"], user["name"])
            self.user["city"] = ""
        else:
            self.user["id"] = current_user["id"]
            self.user["city"] = current_user["city"]

        #get fb email
        self.facebook_request(
            path="/me",
            callback=self._on_userinfo,
            access_token=user["access_token"])

    def _on_userinfo(self, user):
        #print user
        self.user["email"] = user["email"] if "email" in user else ""

        ip = self.request.headers.get("X-Forwarded-For", None) or self.request.remote_ip
        conn.execute("UPDATE users SET email = %s, last_login_ip = %s WHERE id = %s",\
                      self.user["email"], ip, self.user["id"])

        self.set_secure_cookie("user", tornado.escape.json_encode(self.user))

        if self.redirect_url == "/":
            self.redirect_url == "/"+self.user["city"]
        self.redirect(self.redirect_url)


class LogoutHandler(tornado.web.RequestHandler):
    def get(self):
        self.clear_cookie("user")
        self.redirect("/")
        #self.redirect("https://accounts.google.com/Logout")

