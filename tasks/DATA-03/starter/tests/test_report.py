import sqlite3,unittest
from pathlib import Path
SQL=Path('report.sql').read_text()
class T(unittest.TestCase):
 def test_report(self):
  c=sqlite3.connect(':memory:');c.executescript('CREATE TABLE orders(id,customer_id,created_at,status);CREATE TABLE order_items(id,order_id,quantity,unit_price_cents);CREATE TABLE refunds(id,order_id,amount_cents,status);INSERT INTO orders VALUES(1,"c1","2026-01-02T00:00:00Z","paid"),(2,"c1","2026-01-03T00:00:00Z","cancelled");INSERT INTO order_items VALUES(1,1,2,500),(2,2,1,999);INSERT INTO refunds VALUES(1,1,200,"successful");');self.assertEqual(c.execute(SQL).fetchall(),[('2026-01','c1',1000,200,800,1)])
