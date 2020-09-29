import os
import unittest

from src.masoniteorm.models import Model
from src.masoniteorm.relationships import belongs_to, has_many


class Profile(Model):
    __table__ = "profiles"
    __connection__ = "sqlite"


class Articles(Model):
    __table__ = "articles"
    __connection__ = "sqlite"

    @belongs_to("id", "article_id")
    def logo(self):
        return Logo


class Logo(Model):
    __table__ = "logos"
    __connection__ = "sqlite"


class User(Model):

    __connection__ = "sqlite"

    _eager_loads = ()

    __casts__ = {"is_admin": "bool"}

    @belongs_to("id", "user_id")
    def profile(self):
        return Profile

    @has_many("id", "user_id")
    def articles(self):
        return Articles

    def get_is_admin(self):
        return "You are an admin"


class TestRelationships(unittest.TestCase):
    maxDiff = None

    def test_relationship_can_be_callable(self):
        self.assertEqual(
            User.profile().where("name", "Joe").to_sql(),
            """SELECT * FROM "profiles" WHERE "profiles"."name" = 'Joe'""",
        )

    def test_can_access_relationship(self):
        for user in User.where("id", 1).get():
            self.assertIsInstance(user.profile, Profile)

    def test_can_access_has_many_relationship(self):
        user = User.hydrate(User.where("id", 1).first())
        self.assertEqual(len(user.articles), 4)

    def test_can_access_relationship_multiple_times(self):
        user = User.hydrate(User.where("id", 1).first())
        self.assertEqual(len(user.articles), 4)
        self.assertEqual(len(user.articles), 4)

    def test_loading(self):
        users = User.with_("articles").get()
        for user in users:
            user

    def test_casting(self):
        users = User.with_("articles").where("is_admin", True).get()
        for user in users:
            user

    def test_setting(self):
        users = User.with_("articles").where("is_admin", True).get()
        for user in users:
            user.name = "Joe"
            user.is_admin = 1
            user.save()