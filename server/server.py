import threading
import world_amazon_pb2 as amazon_pb
import amazon_ups_pb2 as amz_ups
import socket
from google.protobuf.internal.decoder import _DecodeVarint32
from google.protobuf.internal.encoder import _EncodeVarint
import psycopg2

WorldHost = "0.0.0.0"
WorldPort = 23456
UpsHost = ""
UpsPort = ""
worldSeqnums = []
worldAcks = []
### connect to db
conn = psycopg2.connect(
    database="amazon",
    user='postgres',
    password='123456',
    host='localhost',
    port='5432'
)
ups_socket = 0
world_socket = 0

def send_message(sock, message):
    """ Send a protobuf message to the server. """
    data = message.SerializeToString()
    _EncodeVarint(sock.sendall, len(data))
    sock.sendall(data)

def receive_message(sock, message_type):
    """ Receive a protobuf message from the server. """
    var_int_buff = []
    while True:
        buf = sock.recv(1)
        var_int_buff += buf
        length, pos = _DecodeVarint32(var_int_buff, 0)
        if pos != 0:
            break
    data = sock.recv(length)
    message = message_type()
    try:
        message.ParseFromString(data)
    except Exception as e:
        print("Failed to parse message:", str(e))
        print("Data received:", data)
        return None
    return message

def connect_world(sock, connect):
    """ Connect to the simulated world, creating a new world if no world_id is provided. """
    send_message(sock, connect)
    connected = receive_message(sock, amazon_pb.AConnected)

    if connected and connected.result == "connected!":
        print(f"Successfully connected to world {connected.worldid}.")
        return connected.worldid
    else:
        print("Failed to connect:", connected.result if connected else "No response")
        return None


def initWarehouse():
    cursor = conn.cursor()
    cursor.execute("DELETE FROM warehouse;")
    cursor.execute("DELETE FROM inventories;")
    cursor.execute("ALTER SEQUENCE warehouse_w_wid_seq RESTART WITH 1;")
    cursor.execute("ALTER SEQUENCE inventories_inv_invid_seq RESTART WITH 1;")
    conn.commit()
    warehouse_locations = [(10, 10), (50, 50), (100, 100)]
    warehouses = []
    for x, y in warehouse_locations:
        cursor.execute(
            "INSERT INTO warehouse (w_x, w_y) VALUES (%s, %s) RETURNING id;", (x, y))
        warehouse_id = cursor.fetchone()[0]
        warehouses.append({'id': warehouse_id, 'x': x, 'y': y})
    
    conn.commit()
    cursor.close()
    return warehouses

### update stock
def update_stock(purchase):
    whnum = purchase.whnum
    cursor = conn.cursor()
    try:
        for product in purchase.things:
            productId = product.id
            count = product.count
            
            cursor.execute("SELECT inv_qty FROM inventories WHERE inv_pid = %s AND inv_wid = %s;", (productId, whnum))
            row = cursor.fetchone()

            if row is None:
                cursor.execute("INSERT INTO inventories (inv_wid, inv_pid, inv_qty) VALUES (%s, %s, %s);", 
                               (whnum, productId, count))
            else:
                current_inventory = row[0]
                new_inventory = current_inventory + count
                cursor.execute("UPDATE inventories SET inv_qty = %s WHERE inv_pid = %s AND inv_wid = %s;",
                               (new_inventory, productId, whnum))

        conn.commit()
    except Exception as e:
        conn.rollback()  # Roll back the transaction in case of error
        print("Failed to update inventory:", e)
    finally:
        cursor.close()  # Ensure the cursor is closed after operation



def amzWithWorld():
    while True:
        response = receive_message(world_socket,amazon_pb.AResponses)
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
            # threadOfPack = threading.Thread(target=, args=(pack,))
            # threadOfPack.start()
        for error in response.error:
            ack_msg = amazon_pb.ACommands()
            ack_msg.acks.append(error.seqnum)
            send_message(world_socket,ack_msg)
            if error.seqnum in worldSeqnums:
                continue
            else:
                worldSeqnums.append(error.seqnum)

def main():
    ### connect to UPS and get worldId
    ups = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    ups.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    ups.connect((UpsHost,UpsPort))
    ups_socket = ups
    #### amz send connected msg to ups
    msg_ups_connect = amz_ups.AUCommands()
    msg_ups_connect.connected = True
    send_message(ups,msg_ups_connect)

    msg = receive_message(ups,amazon_pb.UACommands)
    worldId = msg.world_id
    ### connect to world
    amz = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    amz.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    amz.connect((WorldHost, WorldPort))
    world_socket = amz
    #### initialize the warehouse
    warehouses = initWarehouse()
    connect = amazon_pb.AConnect()
    connect.isAmazon = True
    connect.worldid = worldId
    connect = amazon_pb.AConnect()
    for warehouse in warehouses:
        connect.initwh.add(id=warehouse['id'], x=warehouse['x'], y=warehouse['y'])
    ### Test create a new world (new_world_id is None -- unconnected else connected)
    new_world_id = connect_world(amz, connect)
    if new_world_id:
        print(f"New world created with ID {new_world_id} and connected successfully.")
    else:
        print("Failed to create a new world.")

    if new_world_id:
        thread1 = threading.Thread(target=amzWithWorld,args=())
    # Test connect to an existing world
    # connect.worldid = 9
    # if connect_world(sock, connect):
    #     print(f"Connected to existing world with ID {connect.worldid}.")
    # else:
    #     print(f"Failed to connect to existing world with ID {connect.worldid}.")



if __name__ == '__main__':
    main()