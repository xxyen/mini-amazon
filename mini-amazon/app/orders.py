from flask import render_template, redirect, url_for, flash, request
from werkzeug.urls import url_parse
from flask_login import current_user
from flask_paginate import Pagination, get_page_args

from .models.user import User
from .models.order import Order
from .models.cart import Cart

from flask import Blueprint

bp = Blueprint('orders', __name__)

@bp.route('/order/<int:user_id>/submit',methods=['GET','POST'])
def submitOrder(user_id):
    address_x = request.form.get('addr_x')
    address_y = request.form.get('addr_y')
    if current_user.is_authenticated and current_user.id == user_id:
        ### insert into order 
        oid = Order.insert_to_orders(user_id,address_x,address_y)
        ### obtain all carts
        carts = Cart.get(user_id)
        ### insert into lineItems
        Order.insert_to_lineItems(carts,oid)
    return redirect(url_for('orders.getUserOrders',user_id=current_user.id))

@bp.route('/order/<int:user_id>/order_detail/<int:order_id>')
def getOrderDetail(user_id, order_id):
    user = User.get_by_uid(user_id) 
    if current_user.is_authenticated and current_user.id == user_id:
        orders = Order.get_by_oid_uid(user_id,order_id)
    else:
        orders = None
        return redirect(url_for('users.login'))
    return render_template('order_detail.html',user=user,orders=orders)

@bp.route('/orders/<int:user_id>', defaults={'page': 1})
@bp.route('/orders/<int:user_id>/page/<int:page>')
def getUserOrders(user_id,page):
    per_page = 10
    orders = Order.get_by_uid(user_id)
    user = User.get_by_uid(user_id)
    if current_user.is_authenticated and current_user.id == user_id:
        user_orders = orders
    else:
        user_orders = None
        return redirect(url_for('users.login'))
    
    page, per_page, offset = get_page_args(page_parameter='page', per_page_parameter='per_page')
    user_orders_paginated = user_orders[offset: offset + per_page if user_orders else None]
    pagination = Pagination(page=page, per_page=per_page, total=len(user_orders), css_framework='bootstrap4')
    next_num = page + 1 if page < pagination.total_pages else None
    prev_num = page - 1 if page > 1 else None
    return render_template('orders.html', orders=user_orders_paginated, user=user, current_page=page, user_id=user_id, pagination=pagination, next_num=next_num, prev_num=prev_num)