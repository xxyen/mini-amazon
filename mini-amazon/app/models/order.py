from flask import current_app as app
from datetime import datetime
class Order:
    def __init__(self, order_key, processingDate, uid, pid, category, product_name,number, amount,
                 img,description,status,address_x,address_y,packingDate=None,packedDate=None,loadingDate=None,
                 loadedDate=None,deliveringDate=None,deliveredDate=None,upsName=None,truckId=None,warehouseId=None):
        self.order_key = order_key 
        self.address_x = address_x
        self.address_y = address_y
        self.uid = uid
        self.pid = pid
        self.category = category
        self.product_name = product_name
        self.number = number
        self.amount = amount  ## total price
        self.img = img  ## product image
        self.description = description
        self.status = status
        self.processingDate = processingDate  ## processing date
        self.packingDate = packingDate
        self.packedDate = packedDate
        self.loadingDate = loadingDate
        self.loadedDate = loadedDate
        self.deliveringDate = deliveringDate
        self.deliveredDate = deliveredDate
        self.upsName = upsName
        self.truckId = truckId
        self.warehouseId = warehouseId
    

    @staticmethod
    def get_by_oid_uid(uid,oid):
        rows = app.db.execute('''
            SELECT o.o_orderKey, o.o_address_x, o.o_address_y, o.o_uid,
                              li.li_pid, p.p_category, p.p_productName, li.li_number, li.li_amount, p.p_image, p.p_description, o_fulfilment, 
                              o.o_processingDate, o.o_packingDate, o.o_packedDate, o.o_loadingDate, o.o_loadedDate, o.o_deliveringDate, o.o_deliveredDate,
                              o.ups_name,o.truck_id,o.warehouse_id
            FROM orders AS o
            JOIN lineItems AS li ON li.li_orderKey = o.o_orderKey
            JOIN products AS p ON p.p_pid = li.li_pid
            WHERE o.o_uid = :uid AND o.o_orderKey = :oid
            ORDER BY o.o_processingDate DESC
        ''', uid=uid,oid=oid)
        return [Order(*row) for row in rows] 
       
    @staticmethod
    def get_by_uid(uid):
        rows = app.db.execute('''
            SELECT o.o_orderKey, o.o_address_x, o.o_address_y, o.o_uid,
                              li.li_pid, p.p_category, p.p_productName, li.li_number, li.li_amount, p.p_image, p.p_description, o_fulfilment, 
                              o.o_processingDate, o.o_packingDate, o.o_packedDate, o.o_loadingDate, o.o_loadedDate, o.o_deliveringDate, o.o_deliveredDate,
                              o.ups_name,o.truck_id,o.warehouse_id
            FROM orders AS o
            JOIN lineItems AS li ON li.li_orderKey = o.o_orderKey
            JOIN products AS p ON p.p_pid = li.li_pid
            WHERE o.o_uid = :uid
            ORDER BY o.o_processingDate DESC
        ''', uid=uid)
       
        return [Order(*row) for row in rows] 

    
    @staticmethod
    def add_order(uid):
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        app.db.execute('''
            INSERT INTO orders(o_date,o_uid)
            VALUES (:current_time, :uid)
            ''', 
            current_time=current_time,
            uid=uid)
