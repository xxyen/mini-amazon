import world_amazon_pb2 as amazon_pb
import socket
import struct
from google.protobuf.internal.decoder import _DecodeVarint32
from google.protobuf.internal.encoder import _EncodeVarint

WorldHost = "0.0.0.0"
WorldPort = 23456

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

def main():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((WorldHost, WorldPort))

    connect = amazon_pb.AConnect()
    connect.isAmazon = True
    init_wh = connect.initwh.add()
    init_wh.id = 3
    init_wh.x = 101
    init_wh.y = 201

    # Test create a new world
    new_world_id = connect_world(sock, connect)
    if new_world_id:
        print(f"New world created with ID {new_world_id} and connected successfully.")
    else:
        print("Failed to create a new world.")

    # Test connect to an existing world
    # connect.worldid = 9
    # if connect_world(sock, connect):
    #     print(f"Connected to existing world with ID {connect.worldid}.")
    # else:
    #     print(f"Failed to connect to existing world with ID {connect.worldid}.")



if __name__ == '__main__':
    main()