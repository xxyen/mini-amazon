from flask import current_app as app
from datetime import datetime

class Cart:
    def __init__(self, id, pid,price,quantity,s_firstname,s_lastname,status,productName,productDescription,image):
        self.c_uid = id
        self.c_pid = pid
        # self.c_sid = sid
        self.c_price = price
        self.c_quantity = quantity
        self.s_firstname=s_firstname
        self.s_lastname=s_lastname
        self.c_status=status
        self.productName = productName
        self.productDescription = productDescription
        self.image=image
        self.total_price = price*quantity
        
    
    @staticmethod
    def get(uid):
        rows = app.db.execute('''
            SELECT c_uid, c_pid, products.p_price, c_quantity,
                              users.u_firstname,users.u_lastname, c_status,products.p_productname,products.p_description,products.p_image
            FROM carts 
            JOIN users on carts.c_uid=users.u_uid
            JOIN products ON carts.c_pid = products.p_pid
            WHERE carts.c_uid = :uid
            ''', uid=uid)
        return [Cart(*row) for row in rows]

    @staticmethod
    def delete_item(uid, pid):
        app.db.execute('''
            DELETE FROM carts
            WHERE c_uid=:uid 
            AND c_pid=:pid 
            AND c_status=false
            ''', 
            uid = uid,
            pid = pid
            )
    
    @staticmethod
    def save_for_later(uid, pid):
        app.db.execute('''
            UPDATE carts
            SET c_status=true
            WHERE c_uid=:uid 
            AND c_pid=:pid 
            ''', 
            uid = uid,
            pid = pid)
    
    @staticmethod
    def move_to_cart(uid, pid):
        app.db.execute('''
            UPDATE carts
            SET c_status=false
            WHERE c_uid=:uid 
            AND c_pid=:pid 
            ''', 
            uid = uid,
            pid = pid)
    
    @staticmethod
    def change_quantity(uid, pid, quantity):
        app.db.execute('''
            UPDATE carts
            SET c_quantity = :quantity
            WHERE c_uid = :uid
            AND c_pid = :pid
            ''', 
            uid = uid,
            pid = pid,
            quantity = quantity)
    
    @staticmethod
    def checkout(uid):
        app.db.execute('''
            DELETE FROM carts
            WHERE c_uid=:uid 
            AND c_status=false 
            ''', 
            uid = uid)
    
    @staticmethod
    def add_to_cart(uid, pid, quantity):
        print(quantity)
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(current_time)
        print("--------------result-----------------------")
        print(uid)
        result = app.db.execute(
            '''
            UPDATE carts
            SET c_quantity = c_quantity + :quantity, c_date = :current_time, c_status = :c_status
            WHERE c_uid = :uid AND c_pid = :pid
            ''',
            uid=uid,
            pid=pid,
            current_time=current_time,
            c_status=False,
            quantity=quantity) 
        if not result:
            print(111111111111111111111111111111111111111)
            app.db.execute('''
                INSERT INTO carts (c_uid, c_pid, c_date, c_status, c_quantity)
                VALUES (:uid, :pid, :current_time, :c_status, :quantity)
                ''', 
                uid=uid,
                pid=pid,
                current_time=current_time,
                c_status=False,
                quantity=quantity)