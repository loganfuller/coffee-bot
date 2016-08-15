import os
import sqlite3


class DB(object):
    def __init__(self,
                 db_file_path=os.path.join(
                     os.path.dirname(__file__), "../brain.db")):
        self._conn = sqlite3.connect(db_file_path)
        self._cur = self._conn.cursor()

        try:
            with self._conn:
                self._cur.execute(
                    "CREATE TABLE users (id TEXT PRIMARY KEY, username TEXT "
                    "UNIQUE, first_name TEXT, last_name TEXT)"
                )
        except sqlite3.OperationalError:
            pass

    def update_users_table(self, users):
        """Insert new users into users table if they don't already exist.
        Expects a list."""
        with self._conn:
            self._cur.executemany(
                "INSERT OR IGNORE INTO users(id, username, first_name, "
                "last_name) VALUES (:id, :username, :first_name, :last_name)",
                users
            )
