import unittest

from config.database import DATABASES
from src.masoniteorm.connections import SQLiteConnection
from src.masoniteorm.schema import Schema
from src.masoniteorm.schema.platforms import SQLitePlatform
from src.masoniteorm.schema.Table import Table


class TestSQLiteSchemaBuilderAlter(unittest.TestCase):
    def setUp(self):
        self.schema = Schema(
            connection=SQLiteConnection,
            connection_details=DATABASES,
            platform=SQLitePlatform,
            dry=True,
        ).on("sqlite")

    def test_can_add_columns(self):
        with self.schema.table("users") as blueprint:
            blueprint.string("name")
            blueprint.integer("age")

        self.assertEqual(len(blueprint.table.added_columns), 2)

        sql = [
            "ALTER TABLE users ADD COLUMN name VARCHAR",
            "ALTER TABLE users ADD COLUMN age INTEGER",
        ]

        self.assertEqual(blueprint.to_sql(), sql)

    def test_alter_rename(self):
        with self.schema.table("users") as blueprint:
            blueprint.rename("post", "comment", "integer")

        table = Table("users")
        table.add_column("post", "integer")
        blueprint.table.from_table = table

        sql = [
            "CREATE TEMPORARY TABLE __temp__users AS SELECT post FROM users",
            "DROP TABLE users",
            'CREATE TABLE "users" (comment INTEGER)',
            'INSERT INTO "users" (comment) SELECT post FROM __temp__users',
            "DROP TABLE __temp__users",
        ]

        self.assertEqual(blueprint.to_sql(), sql)

    def test_alter_drop(self):
        with self.schema.table("users") as blueprint:
            blueprint.drop_column("post")

        table = Table("users")
        table.add_column("post", "string")
        table.add_column("name", "string")
        table.add_column("email", "string")
        blueprint.table.from_table = table

        sql = [
            "CREATE TEMPORARY TABLE __temp__users AS SELECT name, email FROM users",
            "DROP TABLE users",
            'CREATE TABLE "users" (name VARCHAR, email VARCHAR)',
            'INSERT INTO "users" (name, email) SELECT name, email FROM __temp__users',
            "DROP TABLE __temp__users",
        ]

        self.assertEqual(blueprint.to_sql(), sql)

    def test_change(self):
        with self.schema.table("users") as blueprint:
            blueprint.integer("age").change()
            blueprint.string("name")

        self.assertEqual(len(blueprint.table.added_columns), 1)
        self.assertEqual(len(blueprint.table.changed_columns), 1)
        table = Table("users")
        table.add_column("age", "string")

        blueprint.table.from_table = table

        sql = [
            "ALTER TABLE users ADD COLUMN name VARCHAR",
            "CREATE TEMPORARY TABLE __temp__users AS SELECT age FROM users",
            "DROP TABLE users",
            'CREATE TABLE "users" (age INTEGER, name VARCHAR(255))',
            'INSERT INTO "users" (age) SELECT age FROM __temp__users',
            "DROP TABLE __temp__users",
        ]

        self.assertEqual(blueprint.to_sql(), sql)

    def test_drop_add_and_change(self):
        with self.schema.table("users") as blueprint:
            blueprint.integer("age").change()
            blueprint.string("name")
            blueprint.drop_column("email")

        self.assertEqual(len(blueprint.table.added_columns), 1)
        self.assertEqual(len(blueprint.table.changed_columns), 1)
        table = Table("users")
        table.add_column("age", "string")
        table.add_column("email", "string")

        blueprint.table.from_table = table

        sql = [
            "ALTER TABLE users ADD COLUMN name VARCHAR",
            "CREATE TEMPORARY TABLE __temp__users AS SELECT age FROM users",
            "DROP TABLE users",
            'CREATE TABLE "users" (age INTEGER, name VARCHAR(255))',
            'INSERT INTO "users" (age) SELECT age FROM __temp__users',
            "DROP TABLE __temp__users",
        ]

        self.assertEqual(blueprint.to_sql(), sql)

    def test_alter_drop_on_table_schema_table(self):
        schema = Schema(
            connection=SQLiteConnection,
            connection_details=DATABASES,
            # platform=SQLitePlatform,
        ).on("sqlite")

        with schema.table("table_schema") as blueprint:
            blueprint.drop_column("name")

        with schema.table("table_schema") as blueprint:
            blueprint.string("name")
