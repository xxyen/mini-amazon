from flask_login import UserMixin
from flask import current_app as app
from werkzeug.security import generate_password_hash, check_password_hash

from .. import login


class User(UserMixin):
    def __init__(self, id, email, firstname,lastname, address, balance, image, isSeller,address_x,address_y):
        self.id = id
        self.email = email
        self.firstname = firstname
        self.lastname = lastname
        self.address = address
        self.balance = balance
        self.image = image
        self.isSeller = isSeller
        self.address_x = address_x
        self.address_y = address_y

# retrieve user information from a database based on a specific user ID (uid).
    @staticmethod
    def get_by_uid(id):
        rows = app.db.execute('''
            SELECT u_uid, u_email, u_firstname, u_lastname, u_address, u_balance, u_image, u_isSeller, u_address_x,u_address_y
            FROM Users
            WHERE u_uid = :id
            ''', id=id)
        return User(*rows[0]) if rows else None


    @staticmethod
    def get_by_auth(email, password):
        rows = app.db.execute("""
SELECT u_password,u_uid, u_email, u_firstname, u_lastname,u_address,u_balance,u_image, u_isSeller, u_address_x, u_address_y
FROM Users
WHERE u_email = :email
""",
                              email=email)
        if not rows:  # email not found
            return None
        elif not check_password_hash(rows[0][0], password):
            # incorrect password
            return None
        else:
            return User(*(rows[0][1:]))

    @staticmethod
    def email_exists(email):
        rows = app.db.execute("""
SELECT u_email
FROM Users
WHERE u_email = :email
""",
                              email=email)
        return len(rows) > 0

    @staticmethod
    def register(email, password, firstname, lastname, address, address_x,address_y):
        try:
            rows = app.db.execute("""
INSERT INTO Users(u_email, u_password, u_firstname, u_lastname, u_address, u_address_x,u_address_y)
VALUES(:email, :password, :firstname, :lastname, :address, :address_x,:address_y)
RETURNING u_uid
""",
                                  email=email,
                                  password=generate_password_hash(password),
                                  firstname=firstname, lastname=lastname,address=address, address_x=address_x,address_y=address_y)
            id = rows[0][0]
            print("inserting success!")
            return User.get(id)
        except Exception as e:
            # likely email already in use; better error checking and reporting needed;
            # the following simply prints the error to the console:
            print(str(e))
            return None

    @staticmethod
    @login.user_loader
    def get(id):
        
        rows = app.db.execute("""
SELECT u_uid, u_email, u_firstname, u_lastname,u_address,u_balance,u_image, u_isSeller,u_address_x,u_address_y
FROM Users
WHERE u_uid = :id
""",
                            id=id)
        return User(*(rows[0])) if rows else None


    # def is_user_seller(given_uid):
    #     result = app.db.execute("SELECT u_isSeller FROM Users WHERE u_uid = :given_uid", {"given_uid": given_uid})
    #     row = result.fetchone()
    #     return row[0] if row else False
