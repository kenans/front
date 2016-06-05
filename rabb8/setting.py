import sys
import os
import logging
import uuid

import tornado.database

"""
settings = {
    #"xsrf_cookies": True,
    "twitter_consumer_key": "jKJQsSuIiKM0D6iILmxC5A",
    "twitter_consumer_secret": "tMtVVJTMjDiPVSsuHhbA4Qb58ATFewAwuir3ORz92E",
    "AmazonAccessKeyID": "AKIAJC6EF76YUIBCYWRQ",
    "AmazonSecretAccessKey": "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",
    "static_path": os.path.join(os.path.dirname(__file__), "static/"),
    "cookie_secret": "61oETzKXQAcaYdk85gE4GeJJF2d17EQnp2zczP1o/zZ=",
    "login_url": "/",
    "debug": True,
}
"""

settings = {
    "facebook_api_key": "327816263932087",
    "facebook_secret": "df23d3cccb1afe67fda6b90da99c2a4f",
    "static_path": os.path.join(os.path.dirname(__file__), "./static/"),
    "cookie_secret": "61oETzKXQAGaYdkL5gE4GeKKF2d17EQnp2zczP1o/zZ=",
    "debug": True,
}

if settings["debug"]:
    #conn = tornado.database.Connection("/Applications/XAMPP/xamppfiles/var/mysql/mysql.sock", "rabb8", "root", "root")
    conn = tornado.database.Connection("127.0.0.1", "rabb8", "root", "root")
else:
    conn = tornado.database.Connection("/var/run/mysqld/mysqld.sock", "rabb8", "root", "root")

CATEGORIES = conn.query("SELECT * FROM categories")
CITIES = conn.query("SELECT * FROM cities")
VERSION = open('version').readline().strip()
if settings["debug"]: VERSION = ""
