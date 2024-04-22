-- SQL script to load data from CSV into the database
\copy users(u_email, u_firstname, u_lastname, u_address, u_password, u_balance, u_isSeller, u_image, u_address_x, u_address_y) FROM 'users.csv' WITH CSV HEADER;
\copy products(p_category, p_productName, p_stock, p_description, p_image, p_price) FROM 'products.csv' WITH CSV HEADER;
\copy warehouse(w_x, w_y) FROM 'warehouses.csv' WITH CSV HEADER;
\copy orders(o_processingDate, o_uid, o_fulfilment, o_address_x, o_address_y) FROM 'orders.csv' WITH CSV HEADER;
\copy lineItems(li_orderKey, li_pid, li_amount, li_number) FROM 'line_items.csv' WITH CSV HEADER;
\copy carts(c_uid, c_pid, c_date, c_quantity, c_status) FROM 'carts.csv' WITH CSV HEADER;
\copy feedbackProduct(fp_pid, fp_uid, fp_date, fp_content, fp_score, fp_image) FROM 'feedback_products.csv' WITH CSV HEADER;
\copy ups(ups_name) FROM 'ups.csv' WITH CSV HEADER;
