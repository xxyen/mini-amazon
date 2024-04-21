from flask import current_app as app

class FeedbackToProduct:    
    def __init__(self, pid, uid, date, content, score, image, firstname=None, lastname=None, user_image=None, productName=None):
        self.pid = pid
        self.uid = uid
        self.date = date
        self.content = content
        self.score = score
        self.image = image
        
        self.firstname = firstname
        self.lastname = lastname
        self.user_image = user_image
        self.productName = productName

    @staticmethod
    def get_by_user(uid, limit=6):
        # names represent the sellers
        query = '''
            SELECT fp_pid,  fp_uid, fp_date, fp_content, fp_score, fp_image, u_firstname, u_lastname, u_image, p_productName
            FROM feedbackProduct, Products, Users
            WHERE fp_uid = :uid AND fp_pid = p_pid 
            ORDER BY fp_date DESC
        '''
        if limit > 0:
            query += ' LIMIT :limit'
            rows = app.db.execute(query, uid=uid, limit=limit)
        else:
            rows = app.db.execute(query, uid=uid)
    
        return [FeedbackToProduct(*row) for row in rows]

    @staticmethod
    def get_by_product(pid):
        # names represent the users
        rows = app.db.execute('''
            SELECT fp_pid,  fp_uid, fp_date, fp_content, fp_score, fp_image, u_firstname, u_lastname, u_image
            FROM feedbackProduct, Users
            WHERE fp_pid = :pid AND fp_uid = u_uid
            ORDER BY fp_date DESC;
            ''', pid=pid)
        return [FeedbackToProduct(*row) for row in rows]
    
    @staticmethod
    def get_specific(pid,uid):
        rows = app.db.execute('''
            SELECT fp_pid, fp_uid, fp_date, fp_content, fp_score, fp_image
            FROM feedbackProduct
            WHERE fp_pid = :pid  AND fp_uid = :uid
            ORDER BY fp_date DESC;
            ''', pid=pid, uid=uid)
        return FeedbackToProduct(*rows[0]) if rows else None

    @staticmethod
    def insert_or_update(pid, uid, content, score, image):
        try:
            existing_feedback = FeedbackToProduct.get_specific(pid, uid)
            if existing_feedback:
                # if the record exists, then update it
                app.db.execute('''
                    UPDATE feedbackProduct
                    SET fp_content = :content, fp_score = :score, fp_image = :image, fp_date = CURRENT_TIMESTAMP
                    WHERE fp_pid = :pid  AND fp_uid = :uid
                ''', pid=pid, uid=uid, content=content, score=score, image=image)
            else:
                # if the record does not exist, then insert it
                app.db.execute('''
                    INSERT INTO feedbackProduct (fp_pid, fp_uid, fp_content, fp_score, fp_image, fp_date)
                    VALUES (:pid,:uid, :content, :score, :image, CURRENT_TIMESTAMP)
                ''', pid=pid,uid=uid, content=content, score=score, image=image)
            return True
        except Exception as e:
            print(f"Error: {str(e)}")
            return False

    @staticmethod
    def delete(pid, uid):
        try:
            print("delete", pid, uid)
            app.db.execute('''
                DELETE FROM feedbackProduct
                WHERE fp_pid = :pid AND fp_uid = :uid
            ''', pid=pid, uid=uid)
            return True
        except Exception as e:
            print(f"Error: {str(e)}")
            return False
    
    
    
# class FeedbackToSeller:    
#     def __init__(self, sid, uid, date, content, score, image):
#         self.sid = sid
#         self.uid = uid
#         self.date = date
#         self.content = content
#         self.score = score
#         self.image = image
        
