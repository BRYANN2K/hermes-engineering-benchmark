import sqlite3,unittest
from migration import migrate
def db():
 c=sqlite3.connect(':memory:');c.executescript('PRAGMA user_version=1;CREATE TABLE customers(id INTEGER PRIMARY KEY,email TEXT NOT NULL);CREATE TABLE invoices(id INTEGER PRIMARY KEY,customer_id INTEGER,total_dollars TEXT,paid INTEGER);INSERT INTO customers VALUES(1,"a@b");INSERT INTO invoices VALUES(7,1,"12.34",NULL);');return c
class T(unittest.TestCase):
 def test_migrates(self):
  c=db();migrate(c);self.assertEqual(c.execute('pragma user_version').fetchone()[0],2);self.assertEqual(c.execute('select id,customer_id,total_cents,paid from invoices').fetchall(),[(7,1,1234,0)]);migrate(c);self.assertEqual(c.execute('select count(*) from invoices').fetchone()[0],1)
