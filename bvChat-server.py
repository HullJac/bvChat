from socket import *
import threading
import hashlib
import sys
import os
import random
import time
import linecache

port=55555

# Creation connection dictionary
clientList = {}
clientListLock = threading.Lock()

# list to see which client are currently connected
clientsConnected = []

# Set up listening socket
listener = socket(AF_INET, SOCK_STREAM)
listener.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
listener.bind(('', port))
listener.listen(32) # Support up to 32 simultaneous connections

if os.path.exists("accounts.txt"):
    pass
else:
    f = open("accounts.txt", 'w')
    f.close()

f = open("motd.txt", 'w')
f.write("Message of the day.\nWelcome to bvChat.\nLooking good hot stuff.")
f.close()
f = open("motd.txt", 'r')

message = linecache.getline('motd.txt', random.randint(0, 2))


def getFullMsg(conn, msgLength):
    msg = b''
    while len(msg) < msgLength:
        retVal = conn.recv(msgLength - len(msg))
        msg += retVal
        if len(retVal) == 0:
            break    
    return msg

def getLine(conn):
    msg = b''
    while True:
        ch = conn.recv(1)
        msg += ch
        if ch == b'\n' or len(ch) == 0:
            break
    return msg.decode()


# Produces a newline delimited string of client descriptors
def getClientListMsg():
    clientMsg = ""
    clientListLock.acquire()
    numClients = len(clientList)
    for addr in clientList.items():
        clientMsg += "%s:%d\n" % (addr[0], addr[1])
    clientListLock.release()
    return (numClients, clientMsg)

def printClientList():
  print("Updated List of Peers in Swarm")
  for client in clientList.items():
    print("%s:%d" % (client[0], client[1]))

# Adds or updates the chunkMask for a client participating in the swarm
def updateClientInfo(clientIP, clientPort):
    clientListLock.acquire()
    printClientList()
    clientListLock.release()

# Removes a pre-existing client from participation in the swarm
def removeClientInfo(clientIP, clientPort):
    clientListLock.acquire()
    del clientList[(clientIP,clientPort)]
    printClientList()
    clientListLock.release()

def firstClientConn(connInfo):
    clientConn, clientAddr = connInfo
    clientIP = clientAddr[0]
    clientPort = clientAddr[1]
    print("Received connection from %s:%d" %(clientIP, clientPort))

    try:
        clientConnected = True
        # receive username and password
        # if new add it 

        #### actually receive stuff #########
        username = getLine(clientConn)
        print("username: " + username)
        password = getLine(clientConn)
        print("password: " + password)
        
        f = open('accounts.txt', 'r')
        contents = f.readlines()
        for line in contents:
            line = line.split(':')
            # if user in not a new user
            if username == line[0] and password == line[1]
                # log them in
                clientsConnected.append(username)
                # send message of the day
                clientConn.send(message.encode())
                # call funciton to listen for commands from client possibly in a thread
            elif username == line[0] and password == line[1] and username in clientsConnected:
                print("You are already logged in. You can only login once.")
            elif username in clientsConnected:
                print("Username is taken already.")
            else:
                # add client to
                #############################################

            f = open('accounts.txt', 'a')
        #send motd if username and password are good

        while clientConnected:
            threading.Thread(target=listenForMessages, args=(connInfo), daemon=True).start()

    except Exception:
        print("Exception occurred, closing connection")

    clientConn.close()
    removeClientInfo(clientIP, clientPort)
    

running = True
while running:
    try:
        threading.Thread(target=firstClientConn, args=(listener.accept(),), daemon=True).start()
    except KeyboardInterrupt:
        print('\n[Shutting down]')
        running = False
