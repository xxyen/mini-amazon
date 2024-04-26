from flask import render_template, redirect, url_for, flash, request, jsonify
from werkzeug.urls import url_parse
from flask_login import  current_user
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, TextAreaField, DecimalField
from wtforms.validators import NumberRange, Length, InputRequired

from .models.product import Product
from .models.user import User
from .models.feedback import FeedbackToProduct

from .models.cart import Cart
from .models.user import User

from flask import Blueprint
bp = Blueprint('products', __name__)


@bp.route('/products')
def show_products():
    k = request.args.get('k', default='', type=str)
    s = request.args.get('s', default='relevanceblender', type=str)
    items = Product.search_and_sort(k, s)
    return render_template('items.html', items=items)


class FeedbackForm(FlaskForm):
    score = DecimalField('Score', validators=[InputRequired(), NumberRange(min=0, max=5)], places=2)
    content = TextAreaField('Content', validators=[InputRequired(), Length(max=3000)])
    image = StringField('Image')
    submit = SubmitField('Submit')
    
# @bp.route('/items/<int:seller_id>/<int:product_id>', methods=['GET'])
def product_detail(product_id):
    if request.method == 'GET':
        form = FeedbackForm()
        product = Product.get_product_by_sid_pid(product_id)
        # seller = User.get_by_uid(seller_id)
        feedbacks = FeedbackToProduct.get_by_product(product_id)
        print(feedbacks)
        # if current_user.is_authenticated:
        #     for feedback in feedbacks:
        #         if feedback.uid == current_user.id:
        #             if feedback.image:
        #                 image_base64 = feedback.image
        #             else:
        #                 image_base64 = None
        #             form = FeedbackForm(score=feedback.score, content=feedback.content, image=image_base64)
        #             break
        return render_template('detailed_product.html', form=form, product=product, feedbacks=feedbacks)

@bp.route('/items/<int:product_id>/feedbackSubmit', methods=['POST'])
def review_submit(product_id):
    form = FeedbackForm()
    if form.validate_on_submit():
        product = Product.get_product_by_sid_pid(product_id)
        if product is None:
            return redirect(url_for('products.show_detailed_product', productId=product_id))
        if not current_user.is_authenticated:
            return redirect(url_for('products.show_detailed_product', productId=product_id))
        
        image = None
        if form.image.data:
            image = form.image.data
        
        if not FeedbackToProduct.insert_or_update(product_id, current_user.id, form.content.data, form.score.data, image):
            return redirect(url_for('products.show_detailed_product', productId=product_id))
        # Product.update_avg_review_rating(seller_id, product_id)
        return redirect(url_for('products.show_detailed_product', productId=product_id))
    else:
        print(form.errors)
        return redirect(url_for('products.show_detailed_product', productId=product_id))
    
@bp.route('/items/<int:product_id>/feedbackDelete', methods=['DELETE'])
def review_delete(product_id):
    product = Product.get_product_by_sid_pid(product_id)
    if product is None:
        return jsonify({"error": "Invalid product"}), 400
    if not current_user.is_authenticated:
        return jsonify({"error": "You are not authorized to delete feedback"}), 401
    
    if not FeedbackToProduct.delete(product_id, current_user.id):
        return jsonify({"error": "Failed to delete feedback"}), 500
    # Product.update_avg_review_rating(seller_id, product_id)
    return jsonify({"message": "Feedback deleted successfully"}), 200

@bp.route('/product/<int:productId>')
def show_detailed_product(productId):
    product = Product.get_single_product(productId)
    # similar_products = Product.get(productId)s
    if request.method == 'GET':
        form = FeedbackForm()
        product = Product.get_single_product(productId)
        # seller = User.get_by_uid(sellerId)
        feedbacks = FeedbackToProduct.get_by_product(productId)
        print(feedbacks)
        # if current_user.is_authenticated:
        #     for feedback in feedbacks:
        #         if feedback.uid == current_user.id:
        #             if feedback.image:
        #                 image_base64 = feedback.image
        #             else:
        #                 image_base64 = None
        #             form = FeedbackForm(score=feedback.score, content=feedback.content, image=image_base64)
        #             break
      
    return render_template('detailed_product.html', form=form,product=product, feedbacks=feedbacks)

@bp.route('/add_to_cart/<int:user_id>/<int:pid>/<int:quantity>',methods=['POST'])
def add_to_cart(user_id,pid,quantity): 
    user = User.get_by_uid(user_id)
    print(user_id)
    Cart.add_to_cart(user_id,pid,quantity)
    if current_user.is_authenticated and current_user.id == user_id:
        cart_items = Cart.get(current_user.id)
    else:
        # Handle unauthenticated users
        cart_items = []
    print(cart_items)
    cart_found  = any(not cart.c_status for cart in cart_items)
    saved_found = any( cart.c_status for cart in cart_items)
    cart_total_price=0
    for cart in cart_items:
        if cart.c_status==False:
            cart_total_price += cart.total_price
    return render_template('carts.html', user=user,cart_items=cart_items,cart_found=cart_found,saved_found=saved_found,cart_total_price=cart_total_price)

@bp.route('/update_product/<int:product_id>', methods=['POST'])
def update_product(product_id):
    if not current_user.is_authenticated or not current_user.isSeller:
        return redirect(url_for('users.login'))  # Ensure only sellers can update products

    new_stock = request.form.get('stock')
    if new_stock is not None and new_stock.isdigit():
        new_stock = int(new_stock)
        # Call the function to update the stock in the database
        Product.update_stock(product_id, new_stock, current_user.id)
        flash('Stock updated successfully!')
    else:
        flash('Invalid stock value.')
        
    return redirect(url_for('users.edit_products'))

@bp.route('/remove_product/<int:product_id>', methods=['POST'])
def remove_product(product_id):
    if not current_user.is_authenticated or not current_user.isSeller:
        return redirect(url_for('users.login'))  # Ensure only sellers can update products

    Product.remove_product(product_id, current_user.id)

    return redirect(url_for('users.edit_products'))

@bp.route('/add_product', methods=['POST'])
def add_product():
    if not current_user.is_authenticated or not current_user.isSeller:
        return redirect(url_for('users.login'))  # Ensure only sellers can update products

    product_id = request.form.get('product_id')
    price = request.form.get('price')
    stock = request.form.get('stock')
    Product.insert_productseller_to_current_productseller(current_user.id, product_id, price, stock)
    return redirect(url_for('users.edit_products'))