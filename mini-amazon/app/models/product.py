from flask import current_app as app

class Product:    
    def __init__(self, pid, name, category, stock, price, description, image, avgReviewRating, totalSale):
        self.pid = pid
        self.name = name
        self.category = category
        self.stock = stock
        self.price = price
        self.description = description
        self.image = image
        self.avgReviewRating = avgReviewRating
        self.totalSale = totalSale

     
    @staticmethod
    def get_all():
        rows = app.db.execute('''
            SELECT p.p_pid, p.p_productname,p.p_category,p.p_stock, p.p_price, p.p_description, p.p_image, 
                               COALESCE(AVG(fp.fp_score),0) AS avgReviewRating, COUNT(fp.fp_pid) AS totalSale
            FROM products p
            JOIN feedbackProduct fp ON p.p_pid = fp.fp_pid
            GROUP BY p.p_pid 
            ORDER BY totalSale
            ''')
        return [Product(*row) for row in rows]


    @staticmethod
    def get(id):   
        rows = app.db.execute('''
            SELECT p.p_pid, p.p_productname,p.p_category,p.p_stock, p.p_price, p.p_description, p.p_image, 
                               COALESCE(AVG(fp.fp_score),0) AS avgReviewRating, COUNT(fp.fp_pid) AS totalSale
            FROM products p
            JOIN feedbackProduct fp ON p.p_pid = fp.fp_pid
            WHERE p.p_pid = :id
            GROUP BY p.p_pid 
            ORDER BY totalSale
            ''', id=id)
        return Product(*rows[0]) if rows else None

    
    @staticmethod
    def get_single_product(pid):
        rows = app.db.execute('''
            SELECT p.p_pid, p.p_productname,p.p_category,p.p_stock, p.p_price, p.p_description, p.p_image, 
                               COALESCE(AVG(fp.fp_score),0) AS avgReviewRating, COUNT(fp.fp_pid) AS totalSale
            FROM products p
            LEFT JOIN feedbackProduct fp ON p.p_pid = fp.fp_pid
            WHERE p.p_pid = :pid
            GROUP BY p.p_pid 
            ''', pid=pid)
        return Product(*rows[0]) if rows else None
    

    
    @staticmethod
    def get_products_by_sid(sid):
        rows = app.db.execute('''
            SELECT ps.ps_sid, ps.ps_pid, p.p_productName, p.p_category, ps.ps_stock, ps.ps_price, ps.ps_description, ps.ps_image, ps.ps_avgreviewrating, ps.ps_totalsale
            FROM Products AS p
            JOIN ProductSeller AS ps ON p.p_pid = ps.ps_pid
            WHERE ps.ps_sid = :sid
            ''', sid=sid)
        print(rows)
        return [Product(*row) for row in rows]

    @staticmethod
    def search_and_sort(k, s):
        query = '''
        SELECT p.p_pid, p.p_productname,p.p_category,p.p_stock, p.p_price, p.p_description, p.p_image, 
                               COALESCE(AVG(fp.fp_score),0) AS avgReviewRating, COUNT(fp.fp_pid) AS totalSale
        FROM products p
        LEFT JOIN  feedbackProduct fp ON p.p_pid = fp.fp_pid
        WHERE POSITION(LOWER(:k) in LOWER(p_productname)) > 0
        GROUP BY 
        p.p_pid, 
        p.p_productname,
        p.p_category,
        p.p_stock, 
        p.p_price, 
        p.p_description, 
        p.p_image
        '''
        
        if s == 'price-des-rank':
            query += ' ORDER BY p.p_price DESC'
        elif s == 'price-asc-rank':
            query += ' ORDER BY p.p_price ASC'
        elif s == 'review-rank':
            query += ' ORDER BY avgReviewRating DESC'
        elif s == 'exact-aware-popularity-rank':
            query += ' ORDER BY totalSale DESC'

        rows = app.db.execute(query, k=k)
        return [Product(*row) for row in rows]
        
    @staticmethod
    def get_product_by_sid_pid(pid):
        rows = app.db.execute('''
            SELECT p.p_pid, p.p_productname,p.p_category,p.p_stock, p.p_price, p.p_description, p.p_image, 
                    COALESCE(AVG(fp.fp_score),0) AS avgReviewRating, COUNT(fp.fp_pid) AS totalSale
            FROM products p
            LEFT JOIN feedbackProduct fp ON p.p_pid = fp.fp_pid
            WHERE p.p_pid = :pid
            GROUP BY p.p_pid 
            ''',pid=pid)
        return Product(*rows[0]) if rows else None
    
    # @staticmethod
    # def get_products_by_seller_id(id):
    #     rows = app.db.execute('''
    #         SELECT p.p_pid, p.p_category, p.p_productName,ps.ps_price
    #         FROM Products AS p
    #         JOIN ProductSeller AS ps ON p.p_pid = ps.ps_pid
    #         WHERE ps.ps_sid = :id
    #         ''', id=id)
    #     # print(rows)
    #     return [Product(*row) for row in rows]
    
    # @staticmethod
    # def get_products_by_id(id):
    #     rows = app.db.execute('''
    #         SELECT p.p_pid, p.p_category, p.p_productName,ps.ps_price
    #         FROM Products AS p
    #         JOIN ProductSeller AS ps ON p.p_pid = ps.ps_pid
    #         WHERE ps.ps_sid = :id
    #         ''', id=id)
    #     print(rows)
    #     return [Product(*row) for row in rows]
    
    @staticmethod
    def get_products_by_seller_id(seller_id):
        rows = app.db.execute('''
            SELECT  ps.ps_sid,p.p_pid, p.p_productname,p.p_category,  ps.ps_stock,ps.ps_price, ps.ps_description, ps.ps_image,  ps.ps_avgreviewrating, ps.ps_totalsale
            FROM Products AS p
            JOIN ProductSeller AS ps ON p.p_pid = ps.ps_pid
            WHERE ps.ps_sid = :id
            ''', id=seller_id)
        return [Product(*row) for row in rows]
    
    @staticmethod
    def update_stock(product_id, new_stock, seller_id):
        result = app.db.execute('''
            UPDATE ProductSeller
            SET ps_stock = :new_stock
            WHERE ps_pid = :product_id AND ps_sid = :seller_id
            ''', new_stock=new_stock,
                 product_id=product_id,
                 seller_id=seller_id)
        # app.db.commit()
        return result  
   
    @staticmethod
    def remove_product(product_id, seller_id):
        result = app.db.execute('''
            DELETE FROM ProductSeller
            WHERE ps_pid = :product_id AND ps_sid = :seller_id 
            ''', product_id=product_id,
                 seller_id=seller_id)
        print(result)
        return result
    
    @staticmethod
    def get_products_by_seller_id_not_in_sell(seller_id):
        rows = app.db.execute('''
            SELECT * FROM Products AS p
            WHERE p.p_pid NOT IN (SELECT p.p_pid
            FROM Products AS p
            JOIN ProductSeller AS ps ON p.p_pid = ps.ps_pid
            WHERE ps.ps_sid = :id) 
            ''', id=seller_id)
        return rows
    
    @staticmethod
    def insert_productseller_to_current_productseller(seller_id, product_id, price, stock):
        sql = """
        INSERT INTO ProductSeller
            (ps_sid, ps_pid, ps_price, ps_stock)
        values
            (:seller_id, :product_id, :price, :stock) """
        result = app.db.execute(sql, seller_id=seller_id, product_id=product_id, price=price, stock=stock)
        print(result)
        return result
    
    # @staticmethod
    # def update_avg_review_rating(pid):
    #     rows = app.db.execute('''
    #     SELECT AVG(fp_score)
    #     FROM FeedbackProduct
    #     WHERE fp_pid = :pid 
    #     ''', pid=pid)

    #     avgReviewRating = rows[0][0]
        
    #     print(avgReviewRating)
        
    #     app.db.execute('''
    #         UPDATE ProductSeller
    #         SET ps_avgReviewRating = :avgReviewRating
    #         WHERE ps_pid = :pid AND ps_sid = :sid
    #     ''', avgReviewRating=avgReviewRating, pid=pid, sid=sid)
