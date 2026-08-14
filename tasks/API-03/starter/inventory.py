import sqlite3
class ReservationConflict(Exception):pass
class InsufficientStock(Exception):pass
class InventoryStore:
    def __init__(self,path,clock):
        self.conn=sqlite3.connect(path);self.clock=clock
        self.conn.execute('CREATE TABLE IF NOT EXISTS stock(sku TEXT PRIMARY KEY, quantity INTEGER NOT NULL)')
        self.conn.execute('CREATE TABLE IF NOT EXISTS reservations(key TEXT PRIMARY KEY, sku TEXT, quantity INTEGER, created_at REAL)');self.conn.commit()
    def add_stock(self,sku,quantity):
        self.conn.execute('INSERT INTO stock VALUES(?,?) ON CONFLICT(sku) DO UPDATE SET quantity=quantity+excluded.quantity',(sku,quantity));self.conn.commit();return self.stock(sku)
    def reserve(self,sku,quantity,key):raise NotImplementedError
    def stock(self,sku):
        row=self.conn.execute('SELECT quantity FROM stock WHERE sku=?',(sku,)).fetchone();return row[0] if row else 0
    def reservations(self):return []
    def close(self):self.conn.close()
