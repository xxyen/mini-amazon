import threading
import time
import world_amazon_pb2 as amazon_pb
import amazon_ups_pb2 as amz_ups
import socket
from google.protobuf.internal.decoder import _DecodeVarint32
from google.protobuf.internal.encoder import _EncodeVarint
import psycopg2
import math

WAIT_FOR_ACK = 30
# WorldHost = "0.0.0.0"
WorldHost = "vcm-38048.vm.duke.edu"
WorldPort = 23456
UpsHost = ""
UpsPort = ""
worldSeqnums = []
worldAcks = []
### connect to db
conn = psycopg2.connect(
    database='amazon',
    user='postgres',
    password='123456',
    host='localhost',
    port='5432'
)
ups_socket = 0
world_socket = 0
seqnum = 0
seqnumLock = threading.Lock()

def send_message(sock, message):
    """ Send a protobuf message to the server. """
    data = message.SerializeToString()
    _EncodeVarint(sock.sendall, len(data))
    sock.sendall(data)

# def receive_message(sock, message_type):
#     """ Receive a protobuf message from the server. """
#     var_int_buff = []
#     while True:
#         buf = sock.recv(1)
#         var_int_buff += buf
#         print(var_int_buff)
#         length, pos = _DecodeVarint32(var_int_buff, 0)
#         if pos != 0:
#             break
#     data = sock.recv(length)
#     message = message_type()
#     try:
#         message.ParseFromString(data)
#     except Exception as e:
#         print("Failed to parse message:", str(e))
#         print("Data received:", data)
#         return None
#     return message
def receive_message(sock, response_type):
    data = read_varint_delimited_stream(sock)
    response = response_type()
    response.ParseFromString(data)
    return response
    

# read google buffer protocol response from a socket, return the raw data
def read_varint_delimited_stream(sock):
    print("socket in receive")
    print(sock)
    size_variant = b''
    while True:
        size_variant += sock.recv(1)
        try:
            size = _DecodeVarint32(size_variant, 0)[0]
        except IndexError:
            continue # if decode failed, read one more byte from stream
        break # else if decode succeeded, break. Size is available
    
    data = sock.recv(size) # data in string format
    return data

def connect_world(sock, connect):
    """ Connect to the simulated world, creating a new world if no world_id is provided. """
    send_message(sock, connect)
    print(connect)
    connected = receive_message(sock, amazon_pb.AConnected)

    if connected and connected.result == "connected!":
        print(f"Successfully connected to world {connected.worldid}.")
        return connected.worldid
    else:
        print("Failed to connect:", connected.result if connected else "No response")
        return None


def initWarehouse():
    cursor = conn.cursor()
    cursor.execute("TRUNCATE TABLE inventories, warehouse;")
    cursor.execute("ALTER SEQUENCE warehouse_w_wid_seq RESTART WITH 1;")
    cursor.execute("ALTER SEQUENCE inventories_inv_invid_seq RESTART WITH 1;")
    conn.commit()
    warehouse_locations = [(10, 10), (50, 50), (100, 100)]
    warehouses = []
    for x, y in warehouse_locations:
        sql = f"INSERT INTO warehouse (w_x, w_y) VALUES ({x}, {y}) RETURNING w_wid;"
        cursor.execute(sql)
        warehouse_id = cursor.fetchone()[0]
        warehouses.append({'id': warehouse_id, 'x': x, 'y': y})
        print(f"warehouse id:{warehouse_id} x:{x}")
    
    conn.commit()
    cursor.close()
    return warehouses

### update stock
def update_stock(purchase):
    print("update stock!!!")
    whnum = purchase.whnum
    cursor = conn.cursor()
    try:
        for product in purchase.things:
            productId = product.id
            count = product.count
            
            sql = f"SELECT inv_qty FROM inventories WHERE inv_pid = {str(productId)} AND inv_wid = {str(whnum)};"
            cursor.execute(sql)
            row = cursor.fetchone()

            if row is None:
                print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
                print(whnum)
                print(productId)
                print(count)
                sql = f"INSERT INTO inventories (inv_wid, inv_pid, inv_qty) VALUES ({str(whnum)}, {str(productId)}, {str(count)});"
                # cursor.execute("INSERT INTO inventories (inv_wid, inv_pid, inv_qty) VALUES (%s, %s, %s);", (whnum, productId, count))
                print(sql)
                cursor.execute(sql)
            else:
                current_inventory = row[0]
                new_inventory = current_inventory + count
                cursor.execute("UPDATE inventories SET inv_qty = %s WHERE inv_pid = %s AND inv_wid = %s",
                               (new_inventory, productId, whnum))

        conn.commit()
    except Exception as e:
        conn.rollback()  # Roll back the transaction in case of error
        print("Failed to update inventory:", e)
    finally:
        cursor.close()  # Ensure the cursor is closed after operation

def confirmPackedAndAskTruck(pack):
    try:
        orderId = pack.shipid
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE orders SET o_fulfilment = %s WHERE o_orderKey = %s",
            ('packed', orderId)
        )
        conn.commit()
    except Exception as e:
        conn.rollback() 
        print("An error occurred:", e)
    finally:
        cursor.close() 
        request_truck_to_ups(orderId)

def confirmLoadedAndAskDeliver(load):
    try:
        orderId = load.shipid
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE orders SET o_fulfilment = %s WHERE o_orderKey = %s",
            ('loaded', orderId)
        )
        conn.commit()
        cursor.execute("SELECT truck_id FROM orders WHERE o_orderKey = %s",(orderId))
        truckId = cursor.fetchone()[0]
    except Exception as e:
        conn.rollback() 
        print("An error occurred:", e)
    finally:
        cursor.close()  

        load_package_to_ups(orderId,truckId)
        
def worldWithAmz():
    while True:
        response = receive_message(world_socket,amazon_pb.AResponses)
        print(response)
        for error in response.error:
            ack_msg = amazon_pb.ACommands()
            ack_msg.acks.append(error.seqnum)
            send_message(world_socket,ack_msg)
            if error.seqnum in worldSeqnums:
                continue
            else:
                worldSeqnums.append(error.seqnum)
        for ack in response.acks:
            worldAcks.append(ack)
        for purchase in response.arrived:
            ack_msg = amazon_pb.ACommands()
            ack_msg.acks.append(purchase.seqnum)
            send_message(world_socket,ack_msg)
            if purchase.seqnum in worldSeqnums:
                continue
            else:
                worldSeqnums.append(purchase.seqnum)
            threadOfPurchase = threading.Thread(target=update_stock,args=(purchase,))
            threadOfPurchase.start()
        for pack in response.ready:
            ack_msg = amazon_pb.ACommands()
            ack_msg.acks.append(pack.seqnum)
            send_message(world_socket,ack_msg)
            if pack.seqnum in worldSeqnums:
                continue
            else:
                worldSeqnums.append(pack.seqnum)
            threadOfPack = threading.Thread(target=confirmPackedAndAskTruck, args=(pack,))
            threadOfPack.start()
        for load in response.loaded:
            ack_msg = amazon_pb.ACommands()
            ack_msg.acks.append(load.seqnum)
            send_message(world_socket,ack_msg)
            if load.seqnum in worldSeqnums:
                continue
            else:
                worldSeqnums.append(load.seqnum)
            threadOfLoad = threading.Thread(target=confirmLoadedAndAskDeliver, args=(load,))
            threadOfLoad.start()
        
        if response.finished == True:
            world_socket.close()

def findBestWarehouse(orderId):
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT o_address_x, o_address_y FROM orders WHERE o_orderKey = %s;",
                (orderId,)
            )
            destination = cur.fetchone()
            if destination is None:
                raise ValueError(f"No destination found for package ID {orderId}")

            dest_x, dest_y = destination
            cur.execute("SELECT w_wid, w_x, w_y FROM warehouse;")
            warehouses = cur.fetchall()

            # Determine the closest warehouse
            min_distance = float('inf')
            chosen_warehouse_id = None
            for warehouse in warehouses:
                distance = math.sqrt((warehouse[1] - dest_x) ** 2 + (warehouse[2] - dest_y) ** 2)
                if distance < min_distance:
                    min_distance = distance
                    chosen_warehouse_id = warehouse[0]

            if chosen_warehouse_id is None:
                raise ValueError("No warehouse available for assignment.")

            # Assign the closest warehouse to the package
            cur.execute("UPDATE orders SET warehouse_id = %s WHERE o_orderKey = %s;",
                (chosen_warehouse_id, orderId)
            )
            conn.commit()
            return chosen_warehouse_id

    except (Exception, psycopg2.DatabaseError) as error:
        print(f"An error occurred: {error}")
        conn.rollback()
        return None
    finally:
        if cur is not None:
            cur.close()

### manage sequence number in multi-threaded env
def seqnumAdd():
    with seqnumLock:
        global seqnum
        seqnum = seqnum+1
        return seqnum
    
def purchase(whnum,productIds,descriptions,numbers):
    msg_purchase = amazon_pb.ACommands()
    buy = msg_purchase.buy.add()
    buy.whnum = whnum
    print("purchase")
    print(whnum)
    for index in range(len(productIds)):
        product = buy.things.add()
        product.id = productIds[index]
        product.description = descriptions[index]
        product.count = numbers[index]
    buy.seqnum = seqnumAdd()
    send_message(world_socket,msg_purchase)
    print(msg_purchase)
    #### validate ack
    while True:
        time.sleep(WAIT_FOR_ACK)
        if buy.seqnum in worldAcks:
            break
        else:
            send_message(world_socket,msg_purchase)

    
### check the inventory
def checkInventory(warehouse_id,productIds,numbers):
    
    for index in range(len(productIds)):
        cursor = conn.cursor()
        # sql = f"SELECT inv_qty FROM inventories WHERE inv_pid={str(productIds[index])} AND inv_wid={str(warehouse_id)};"
        # cursor.execute(sql)
        print(productIds[index])
        print(warehouse_id)
        cursor.execute("SELECT inv_qty FROM inventories WHERE inv_pid=%s AND inv_wid=%s;", (productIds[index], warehouse_id))
        # print(cursor.fetchone())
        inventory = cursor.fetchone()[0]
        conn.commit()
        cursor.close()
        #### under stock
        if inventory < numbers[index]:
            return False
        
    return True

### packing
def pack(warehouse_id,productIds,numbers,descriptions,oid):
    msg_pack = amazon_pb.ACommands()
    packs = msg_pack.topack.add()
    packs.whnum = warehouse_id
    packs.shipid = oid
    packs.seqnum = seqnumAdd()
    cursor = conn.cursor()

    for index in range(len(productIds)):
        product = packs.things.add()
        product.id = productIds[index]
        product.description = descriptions[index]
        product.count = numbers[index]
        #### reduce stock
        cursor.execute("SELECT inv_qty FROM inventories WHERE inv_pid = %s AND inv_wid = %s", (productIds[index], warehouse_id))
        inventory = cursor.fetchone()[0]
        cursor.execute('UPDATE inventories SET inv_qty = %s WHERE inv_pid = %s AND inv_wid = %s',
                    (inventory-numbers[index], productIds[index], warehouse_id))
        # conn.commit()
    
    send_message(world_socket,msg_pack)
    cursor.execute(
            'UPDATE orders SET o_fulfilment = %s WHERE o_orderKey = %s',
            ('packing', oid)
        )
    conn.commit()
    cursor.close()


def amzWithWorld():
    print("amz with world")
    while True:
        cursor = conn.cursor()
        cursor.execute("SELECT o_orderKey FROM orders WHERE o_fulfilment = 'processing';")
        time.sleep(5)
        orders = cursor.fetchall()
        print(orders)
        for order in orders:
            print(order[0])
            findBestWarehouse(order[0])
            index_order = order[0]
            print(index_order)
            # sql = "SELECT o.warehouse_id, p.p_pid, p.p_description, li.li_number FROM lineItems li JOIN products p ON p.p_pid = li.li_pid JOIN orders o ON o.o_orderKey = li.li_orderKey WHERE o.o_orderKey=" + str(index_order) + ";"
            # print(sql)
            # cursor.execute(sql)
            cursor.execute( "SELECT o.warehouse_id, p.p_pid, p.p_description, li.li_number FROM lineItems li INNER JOIN products p ON p.p_pid = li.li_pid INNER JOIN orders o ON o.o_orderKey = li.li_orderKey WHERE o.o_orderKey=%s", (index_order,))

            results = cursor.fetchall()
            print(results)
            descriptions = []
            numbers = []
            productIds = []
            warehouse_id = results[0][0]
            for row in results:
                # if index == 0:
                #     warehouse_id = row[0]
                # Append data to lists
                productIds.append(row[1])
                descriptions.append(row[2])
                numbers.append(row[3])

            ### buy
            purchase(warehouse_id,productIds,descriptions,numbers)
            sql = f"UPDATE orders SET o_fulfilment = 'processed' WHERE o_orderKey = 1;"
            print(sql)
            cursor.execute(sql)
            # conn.commit()
            # cursor.execute("UPDATE orders SET o_fulfilment = 'processed' WHERE o_orderKey = %s", (order[0],)) 

            ### check stock and pack
            while True:
                if checkInventory(warehouse_id,productIds,numbers):
                    pack(warehouse_id,productIds,numbers,descriptions,order[0])
                    break
                time.sleep(1)

        conn.commit()
        cursor.close()        
            
### ask world to load 
def toLoad(msg_truck_arrive):
    msg_toload = amazon_pb.ACommands()
    toLoad = msg_toload.load.add()
    toLoad.whnum = msg_truck_arrive.warehouse_id
    toLoad.truckid = msg_truck_arrive.truck_id
    toLoad.shipid = msg_truck_arrive.package_id
    toLoad.seqnum = seqnumAdd()
    send_message(world_socket,msg_toload)
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE orders SET o_fulfilment = 'loading' WHERE o_orderKey = %s", (msg_truck_arrive.package_id,))
        conn.commit()
    except Exception as e:
        conn.rollback()
        print("Failed to update to delivering status:", e)
    finally:
        cursor.close()


#========================== Amazon with UPS ============================

# Add truck_id to the pakcage and send toLoad msg to the world
def handle_truck_arrive(msg_truck_arrive):
    truck_id = msg_truck_arrive.truck_id
    package_id = msg_truck_arrive.package_id
    # Add truck_id to the order/package
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE orders SET truck_id = %s WHERE o_orderKey = %s", (truck_id, package_id))
        conn.commit()
        # Send msg to warehouse to load the pacakge
        # TBD
        toLoad(msg_truck_arrive)
    except Exception as e:
        conn.rollback()
        print("Failed to add truck_id to packed pakcage:", e)
    finally:
        cursor.close() 

# Send request_truck msg to UPS after received ready msg from world
def request_truck_to_ups(package_id):
    command = amz_ups.AUCommands()
    request_truck = amz_ups.request_truck()
    request_truck.package_id = package_id
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT warehouse_id, o_address_x, o_address_y FROM orders WHERE o_orderKey = %s", (package_id,))
        row = cursor.fetchone()
        print(row)
        request_truck.warehouse_id = row[0]
        request_truck.dest_x = row[1]
        request_truck.dest_y = row[2]

        cursor.execute("SELECT w_x, w_y FROM warehouse WHERE w_wid = %s", (request_truck.warehouse_id,))
        
        row = cursor.fetchone()
        print(row)
        request_truck.warehouse_x = row[0]
        request_truck.warehouse_y = row[1]

        cursor.execute("SELECT li_pid FROM lineItems WHERE li_orderKey = %s", (package_id,))
        rows = cursor.fetchAll()
        print(rows)
        for row in rows:
            cursor.execute("SELECT p_productName, p_stock FROM products WHERE p_pid= %s", (row[0],))
            row_product = cursor.fetchone()
            item = amz_ups.Item()
            item.name = row_product[0]
            item.qunatity = row_product[1]
            request_truck.items.append(item)
    
        conn.commit()

    except Exception as e:
        conn.rollback()
        print("Failed to get address of loaded package:", e)
    finally:
        cursor.close()
    
    command.truck_req.CopyFrom(request_truck)
    print(command.truck_req)
    send_message(ups_socket, command)

# Send load_package msg to UPS after received loaded msg from world
# Let the truck go
def load_package_to_ups(package_id, truck_id):
    command = amz_ups.AUCommands()
    loaded = amz_ups.load_package()
    loaded.package_id = package_id
    loaded.truck_id = truck_id
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT o_address_x, o_address_y FROM orders WHERE o_orderKey = %s", (package_id))
        row = cursor.fetchone()
        loaded.dest_x = row[0]
        loaded.dest_y = row[1]

        conn.commit()

    except Exception as e:
        conn.rollback()
        print("Failed to get address of loaded package:", e)
    finally:
        cursor.close()
    
    command.load_pack.CopyFrom(loaded)
    send_message(ups_socket, command)

# Send request_destination_change msg to UPS
# Not change address until receive response msg from UPS
def request_destination_chagne_to_ups(package_id, new_x, new_y):
    command = amz_ups.AUCommands()
    dest_ch = amz_ups.request_destination_change()
    dest_ch.package_id = package_id
    dest_ch.new_dest_x = new_x
    dest_ch.new_dest_y = new_y
    command.dest_ch.CopyFrom(dest_ch)
    send_message(ups_socket, command)


# Change the package status to delivering
def handle_start_deliver(msg_start_deliver):
    package_id = msg_start_deliver.package_id
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE orders SET o_fulfilment = 'delivering' WHERE o_orderKey = %s", (package_id))
        conn.commit()
    except Exception as e:
        conn.rollback()
        print("Failed to update to delivering status:", e)
    finally:
        cursor.close()

# Change the package status to delivered
def handle_delivered_package(msg_deliverd_package):
    package_id = msg_deliverd_package.package_id
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE orders SET o_fulfilment = 'delivered' WHERE o_orderKey = %s", (package_id))
        conn.commit()
    except Exception as e:
        conn.rollback()
        print("Failed to update to delivered status:", e)
    finally:
        cursor.close()

def handle_res_dest_changed(msg_res_dest_changed):
    package_id = msg_res_dest_changed.pacakge_id
    new_x = msg_res_dest_changed.new_dest_x
    new_y = msg_res_dest_changed.new_dest_y
    if(msg_res_dest_changed.success):
        cursor = conn.cursor()
        try:
            cursor.execute("UPDATE orders SET o_address_x = %s, o_address_y = %s WHERE o_orderKey = %s", (new_x,new_y, package_id))
            conn.commit()
        except Exception as e:
            conn.rollback()
            print("Failed to update to new address:", e)
        finally:
            cursor.close()
    
def handle_dest_changed_from_ups(msg_dest_changed):
    package_id = msg_dest_changed.package_id
    new_x = msg_dest_changed.new_dest_x
    new_y = msg_dest_changed.new_dest_y
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE orders SET o_address_x = %s, o_address_y = %s WHERE o_orderKey = %s", (new_x,new_y, package_id))
        conn.commit()
    except Exception as e:
        conn.rollback()
        print("Failed to update to new address:", e)
    finally:
        cursor.close()

def amzWithUPS():
    while True:
        response = receive_message(ups_socket,amz_ups.UACommands)
        for msg_truck_arrive in response.truck_arrive:
            threadOfTruckArrive = threading.Thread(target=handle_truck_arrive,args=(msg_truck_arrive,))
            threadOfTruckArrive.start()
        for msg_start_deliver in response.start_deliver:
            threadOfStartDeliver = threading.Thread(target=handle_start_deliver, args=(msg_start_deliver,))
            threadOfStartDeliver.start()
        for msg_deliverd_package in response.package_delivered:
            threadOfDeliverdPack = threading.Thread(target=handle_delivered_package, args=(msg_deliverd_package,))
            threadOfDeliverdPack.start()
        for msg_res_dest_changed in response.dest_response:
            threadOfDestChanged = threading.Thread(target=handle_res_dest_changed, args=(msg_res_dest_changed,))
            threadOfDestChanged.start()
        for msg_dest_changed in response.dest_notification:
            threadOfDestChangedUPS = threading.Thread(target=handle_dest_changed_from_ups, args=(msg_dest_changed,))
            threadOfDestChangedUPS.start()
        for msg_disconnect in response.disconnect:
            if(msg_disconnect == True):
                ups_socket.close()


# def main():



if __name__ == '__main__':
        # ### connect to UPS and get worldId
    # ups = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # ups.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    # ups.connect((UpsHost,UpsPort))
    # ups_socket = ups
    # #### amz send connected msg to ups
    # msg_ups_connect = amz_ups.AUCommands()
    # msg_ups_connect.connected = True
    # send_message(ups,msg_ups_connect)

    # msg = receive_message(ups,amazon_pb.UACommands)
    # worldId = msg.world_id
    ### connect to world
    amz = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    amz.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    amz.connect((WorldHost, WorldPort))
    world_socket = amz
    #### initialize the warehouse
    warehouses = initWarehouse()
    connect = amazon_pb.AConnect()
    connect.isAmazon = True
    # connect.worldid = worldId
    # Test connect world
    # connect.worldid = 1
    
    # connect = amazon_pb.AConnect()
    for warehouse in warehouses:
        connect.initwh.add(id=warehouse['id'], x=warehouse['x'], y=warehouse['y'])
    ### Test create a new world (new_world_id is None -- unconnected else connected)
    new_world_id = connect_world(amz, connect)
    if new_world_id:
        print(f"New world created with ID {new_world_id} and connected successfully.")
    else:
        print("Failed to create a new world.")

    if new_world_id:
        handlers = [worldWithAmz, amzWithWorld]
        threads = []
        for handler in handlers:
            thread = threading.Thread(target=handler)
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()
    conn.close()   