from flask import render_template, redirect, url_for, flash, request
from werkzeug.urls import url_parse
from flask_login import login_user, logout_user, current_user
from flask_wtf import FlaskForm
from wtforms import IntegerField, StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import ValidationError, DataRequired, Email, EqualTo,NumberRange

from .models.user import User
from .models.product import Product
from .models.feedback import FeedbackToProduct
from .models.order import Order
from .models.cart import Cart

from flask import Blueprint
bp = Blueprint('users', __name__)


class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')

@bp.route('/user/<int:user_id>')
def user_detail(user_id): 
    print("---------user_detail------------------")
    user = User.get_by_uid(user_id)
    if current_user.is_authenticated and current_user.id == user_id:
        recent_feedbacks = FeedbackToProduct.get_by_user(user_id)
        user_orders = Order.get_by_uid(user_id)
    else:
        recent_feedbacks = FeedbackToProduct.get_by_user(user_id)
        user_orders = None
    ## get order details for a specific user.
        
    return render_template('user_detail.html', user=user, feedbacks=recent_feedbacks,orders=user_orders)


@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        if current_user.isSeller:
            return redirect(url_for('users.seller_page', id=current_user.id))
        else:
            return redirect(url_for('index.index'))

    form = LoginForm()

    if form.validate_on_submit():
        user = User.get_by_auth(form.email.data, form.password.data)
        # print(user)
        if user is None:
            flash('Invalid email or password')
            return redirect(url_for('users.login'))
        login_user(user)
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':  
            if not user.isSeller:
                next_page = url_for('index.index')  
            else:
                next_page = url_for('users.seller_page', id=current_user.id) 

        return redirect(next_page)
    return render_template('login.html', title='Sign In', form=form)


class RegistrationForm(FlaskForm):
    firstname = StringField('First Name', validators=[DataRequired()])
    lastname = StringField('Last Name', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    password2 = PasswordField(
        'Repeat Password', validators=[DataRequired(), EqualTo('password')])
    address = StringField('Address', validators=[DataRequired()])  
    address_x = IntegerField('Address X', validators=[DataRequired(), NumberRange(min=-10000, max=10000)], default=0)
    address_y = IntegerField('Address Y', validators=[DataRequired(), NumberRange(min=-10000, max=10000)], default=0)
    submit = SubmitField('Register')
    

    def validate_email(self, email):
        if User.email_exists(email.data):
            raise ValidationError('Already a user with this email.')


@bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index.index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        if User.register(form.email.data,
                         form.password.data,
                         form.firstname.data,
                         form.lastname.data,
                         form.address.data,
                         form.address_x.data,
                         form.address_y.data):
            flash('Congratulations, you are now a registered user!')
            return redirect(url_for('users.login'))
    return render_template('register.html', title='Register', form=form)


@bp.route('/logout')
def logout():
    print("-------------logout----------------")
    logout_user()
    return redirect(url_for('index.index'))

@bp.route('/seller_page/<int:id>')
def seller_page(id):
    # brought_products = 0
    print("-------------seller_page----------------")
    avail_products = Product.get_products_by_sid(id)
    return render_template('index.html', avail_products=avail_products)

        
@bp.route('/cart/<int:user_id>')
def user_cart(user_id): 
    user = User.get_by_uid(user_id)
    if current_user.is_authenticated and current_user.id == user_id:
        cart_items = Cart.get(current_user.id)
    else:
        # Handle unauthenticated users
        cart_items = []
    cart_found  = any(not cart.c_status for cart in cart_items)
    saved_found = any( cart.c_status for cart in cart_items)
    cart_total_price=0
    for cart in cart_items:
        if cart.c_status==False:
            cart_total_price += cart.total_price
    return render_template('carts.html', user=user,cart_items=cart_items,cart_found=cart_found,saved_found=saved_found,cart_total_price=cart_total_price)

@bp.route('/cart/delete/<int:user_id>/<pid>', methods=['GET','POST'])
def delete_item(user_id,pid):
    user = User.get_by_uid(user_id)
    Cart.delete_item(current_user.id, pid)
    cart_items = Cart.get(current_user.id)   
    cart_found  = any(not cart.c_status for cart in cart_items)
    saved_found = any( cart.c_status for cart in cart_items)
    cart_total_price=0
    for cart in cart_items:
        if cart.c_status== False:
            cart_total_price += cart.total_price
    return render_template('carts.html', user=user,cart_items=cart_items,cart_found=cart_found,saved_found=saved_found,cart_total_price=cart_total_price)

@bp.route('/cart/sdfl/<int:user_id>/<pid>', methods=['GET','POST'])
def save_for_later(user_id,pid):
    user = User.get_by_uid(user_id)
    Cart.save_for_later(current_user.id, pid)
    cart_items = Cart.get(current_user.id)   
    cart_found  = any(not cart.c_status for cart in cart_items)
    saved_found = any( cart.c_status for cart in cart_items)
    cart_total_price=0
    for cart in cart_items:
        if cart.c_status==False:
            cart_total_price += cart.total_price
    return render_template("carts.html", user=user,cart_items=cart_items,cart_found=cart_found,saved_found=saved_found,cart_total_price=cart_total_price)

@bp.route('/cart/mdtc/<int:user_id>/<pid>', methods=['GET','POST'])
def move_to_cart(user_id,pid):
    user = User.get_by_uid(user_id)
    Cart.move_to_cart(current_user.id, pid)
    cart_items = Cart.get(current_user.id)   
    cart_found  = any(not cart.c_status for cart in cart_items)
    saved_found = any( cart.c_status for cart in cart_items)
    cart_total_price=0
    for cart in cart_items:
        if cart.c_status==False:
            cart_total_price += cart.total_price
    return render_template("carts.html", user=user,cart_items=cart_items,cart_found=cart_found,saved_found=saved_found,cart_total_price=cart_total_price)

@bp.route('/cart/cq/<int:user_id>/<pid>', methods=['GET','POST'])
def change_quantity(user_id,pid):
    user = User.get_by_uid(user_id)
    new_quantity = request.form.get('quantity', type=int)
    Cart.change_quantity(current_user.id, pid, new_quantity)
    cart_items = Cart.get(current_user.id)   
    cart_found  = any(not cart.c_status for cart in cart_items)
    saved_found = any( cart.c_status for cart in cart_items)
    cart_total_price=0
    for cart in cart_items:
        if cart.c_status==False:
            cart_total_price += cart.total_price
    return render_template("carts.html", user=user,cart_items=cart_items,cart_found=cart_found,saved_found=saved_found,cart_total_price=cart_total_price)


@bp.route('/cart/checkout/<int:user_id>', methods=['GET','POST'])
def checkout(user_id): 
    address_x = request.form.get('addr_x')
    address_y = request.form.get('addr_y')
    user = User.get_by_uid(user_id)
    Cart.checkout(current_user.id)
    Order.add_order(current_user.id)
    cart_items = Cart.get(current_user.id) 
    cart_found  = any(not cart.c_status for cart in cart_items)
    saved_found = any( cart.c_status for cart in cart_items)
    cart_total_price=0
    return render_template("order_detail.html")

@bp.route('/cart/go_to_checkout/<int:user_id>', methods=['GET', 'POST'])
def go_to_checkout(user_id): 
    user = User.get_by_uid(user_id)
    cart_items = Cart.get(current_user.id) 
    cart_found  = any(not cart.c_status for cart in cart_items)
    cart_total_price=0
    for cart in cart_items:
        if cart.c_status==False:
            cart_total_price += cart.total_price
    return render_template("checkout.html",user=user,cart_items=cart_items,cart_found=cart_found,cart_total_price=cart_total_price)

# #seller part
# @bp.route('/edit_products')
# def edit_products():
#     if not current_user.is_authenticated or not current_user.isSeller:
#         flash('You must be logged in as a seller to access this page.')
#         return redirect(url_for('users.login'))

#     products = Product.get_products_by_seller_id(current_user.id)  
#     products_not_in_sell = Product.get_products_by_seller_id_not_in_sell(current_user.id)
#     return render_template('edit_products.html', products=products, products_not_in_sell=products_not_in_sell)
