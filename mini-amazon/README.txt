Team name: BugDance
Project: Mini-Amazon
Team members:
Qianyi Xue(qx49)  Evan Li(hl490)  Yuehan Li(yl979)  Wenye Li(wl275)  Dongyu Lan(dl393)
Repo Link:
https://gitlab.oit.duke.edu/hl490/mini-amazon.git

Demo link: https://www.youtube.com/watch?v=0b6r3II_sNM

Role:
Users Guru: responsible for Account / Purchases              --Qianyi Xue(qx49)
Products Guru: responsible for Products                      --Wenye Li(wl275)
Carts Guru: responsible for Cart / Order                     --Yuehan Li(yl979)
Sellers Guru: responsible for Inventory / Order Fulfillment  --Dongyu Lan(dl393)
Social Guru: responsible for Feedback / Messaging            --Evan Li(hl490)


Han Li(hl490):

In milestone4, my contributions are concentrated on product reviews. I edited detailed_product.html to show all the customer reviews of the product and allow authenticated user to write/revise/delete a review. Then the average score of the product will be updated. The user can also upload an image and preview it. Additionally, I wrote a python script to generate lots of fake data (meets all the reference and constraints), allowing us to better debug and demonstrate.


Qianyi Xue(qx49)

In Milestone 4, I successfully completed the development of orders.html and order_detail.html, which included implementing pagination functionalities and refining the logic on these pages. I refined database to revise some fields. I actively participated in merging the code and tried my best to promote the team intergrated seamlessly.

Yuehan Li(yl979):

In milestone4, the frontend part of my job is basically on carts.html and on detailed_products.html. The revision of the above html files makes the view of cart page more detailed and good-looking.  The backend part is  implemented in cart.py file which is located in the models folder, users.py and products.py for API implementation (including change quantities, delete items, change the item’s status and etc.) and routing purposes. 


Dongyu Lan(dl393):

edit_products.html, located in templates, enables sellers to add new products not currently on sale and manage their inventory. This page uses Jinja2 to extend the base.html layout and includes forms for product management. Backend updates include new routes in users.py and products.py for editing inventory, updating stock, deleting products, and adding new items, accessible only to authenticated sellers. Additionally, the Product.py file now contains functions for updating stock, removing products, fetching unsold products, and inserting new items into the inventory, streamlining database interactions.

Wenye Li(wl275):

In this milestone, my contributions are concentrated on enhancing product functionality. In the backend, modifications were made to product.py for both API construction and routing purposes. On the frontend, I revamped items.html to refine the layout and introduced multiple filters for product searches. Additionally, I developed detailed_product.html to provide a detailed view of product information, including a feature that allows customers to specify the quantity of products they wish to add to their cart.







