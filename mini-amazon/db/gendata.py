import random
from faker import Faker
fake = Faker()

# Number of records to create
num_users = 20
num_products = 50
num_orders = 100
num_warehouses = 10
num_ups = 5

# Data containers
users = []
ups = []
products = []
warehouses = []
orders = []
line_items = []
carts = []
feedback_products = []
product_categories = [
    'Electronics', 'Books', 'Clothing', 'Household', 'Toys', 'Food', 'Sports',
    'Beauty', 'Health', 'Jewelry', 'Outdoor', 'Automotive', 'Pet Supplies',
    'Office Supplies', 'Music', 'Movies', 'Video Games', 'Baby', 'Furniture',
    'Shoes', 'Accessories', 'Home Decor', 'Tools', 'Garden', 'Luggage', 'Watches'
]

# Create Users
for _ in range(num_users):
    users.append({
        'email': fake.email(),
        'firstname': fake.first_name(),
        'lastname': fake.last_name(),
        'address': fake.address(),
        'password': fake.sha256(),
        'balance': round(random.uniform(10, 1000), 2),
        'isSeller': fake.boolean(chance_of_getting_true=25),
        'image': fake.image_url(),
        'address_x': random.randint(0, 100),
        'address_y': random.randint(0, 100)
    })

for _ in range(num_ups):
    ups.append({'ups_name': fake.company()})

# Create Products
for _ in range(num_products):
    category = random.choice(product_categories)
    products.append({
        'category': category,
        'productName': fake.word(),
        'stock': random.randint(0, 500),
        # 'description': fake.text(max_nb_chars=40),
        'description': fake.word(),
        'image': fake.image_url(),
        'price': round(random.uniform(1, 1000), 2)
    })

# Create Warehouses
for _ in range(num_warehouses):
    warehouses.append({
        'x': random.randint(0, 100),
        'y': random.randint(0, 100)
    })

# Create Orders
for _ in range(num_orders):
    order_user_id = random.randint(1, num_users)
    orders.append({
        'processingDate': fake.date_time_this_year(),
        'uid': order_user_id,
        'fulfilment': random.choice(['processing', 'packed', 'delivering', 'delivered']),
        'address_x': users[order_user_id - 1]['address_x'],
        'address_y': users[order_user_id - 1]['address_y']
    })


# User and Product Mappings
user_ids = {user['email']: idx + 1 for idx, user in enumerate(users)}  # Map emails to IDs, assuming they're indexed from 1

# Tracking unique line items
existing_line_items = set()

# Generate Line Items with uniqueness check
for order_idx, order in enumerate(orders):
    order_id = order_idx + 1  # Assuming orders are indexed from 1
    used_products = set()  # Track products used in this order to avoid duplicates

    num_items = random.randint(1, 5)
    while len(used_products) < num_items:
        product_id = random.randint(1, num_products)
        if (order_id, product_id) not in existing_line_items:
            existing_line_items.add((order_id, product_id))
            used_products.add(product_id)
            line_items.append({
                'orderKey': order_id,
                'pid': product_id,
                'amount': products[product_id - 1]['price'],
                'number': random.randint(1, 3)
            })

# Carts
for user_email in user_ids:
    if random.choice([True, False]):  # Random choice to assign carts
        product_id = random.randint(1, num_products)
        carts.append({
            'uid': user_ids[user_email],
            'pid': product_id,
            'date': fake.date_time_this_year(),
            'quantity': random.randint(1, 3),
            'status': fake.boolean()
        })

# Feedback Products
for user_email in user_ids:
    if random.choice([True, False]):  # Random choice to give feedback
        product_id = random.randint(1, num_products)
        feedback_products.append({
            'pid': product_id,
            'uid': user_ids[user_email],
            'date': fake.date_time_this_year(),
            'content': fake.text(),
            'score': round(random.uniform(0, 5), 2),
            'image': fake.image_url()
        })


import csv

# Function to save data to CSV
def save_data_to_csv(data, filename, fieldnames):
    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for row in data:
            writer.writerow(row)

# Define fieldnames for each table
user_fieldnames = ['email', 'firstname', 'lastname', 'address', 'password', 'balance', 'isSeller', 'image', 'address_x', 'address_y']
product_fieldnames = ['category', 'productName', 'stock', 'description', 'image', 'price']
warehouse_fieldnames = ['x', 'y']
order_fieldnames = ['processingDate', 'uid', 'fulfilment', 'address_x', 'address_y']
line_item_fieldnames = ['orderKey', 'pid', 'amount', 'number']
cart_fieldnames = ['uid', 'pid', 'date', 'quantity', 'status']
feedback_product_fieldnames = ['pid', 'uid', 'date', 'content', 'score', 'image']
ups_fieldnames = ['ups_name']

# Save data to CSV
save_data_to_csv(users, 'users.csv', user_fieldnames)
save_data_to_csv(products, 'products.csv', product_fieldnames)
save_data_to_csv(warehouses, 'warehouses.csv', warehouse_fieldnames)
save_data_to_csv(orders, 'orders.csv', order_fieldnames)
save_data_to_csv(line_items, 'line_items.csv', line_item_fieldnames)
save_data_to_csv(carts, 'carts.csv', cart_fieldnames)
save_data_to_csv(feedback_products, 'feedback_products.csv', feedback_product_fieldnames)
save_data_to_csv(ups, 'ups.csv', ups_fieldnames)
