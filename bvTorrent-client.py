from socket import *
import threading
import sys
import os
import copy
import random
import time
import hashlib

'''
We decided to allow three connection from a peer to our client at a time.
We chose three becasue we didn't want to overwhelm our computers with a lot of connetions at once.
We decided to allow our client to only connect to one peer at a time.
We chose one because we figured the files were small enough and one grabbed everything fast enough.
Also, we did not want to deal with grabbing the same chunk twice
due to us randomly grabbing chunks that we need. 
We also decided to send our updated mask and ask for the new list of updated
peers everytime we grab a new chunk from other peers. 
'''
if len(sys.argv) != 3:
    print("Incorrect number of arguments")
    exit()

serverIP = sys.argx[1]
serverPort = int(sys.argv[2])

userName = input("Username: ")
passWord = input("Password: ")

ourConnectionPort = 69420
ourListeningPort = 0

# varibale to refer to listener socket later
listener = ""


# helps when reading large chunks of data
def recvAll(conn, msgLength):
    msg = b''
    while len(msg) < msgLength:
        retVal = conn.recv(msgLength - len(msg))
        msg += retVal
        if len(retVal) == 0:
            break
    return msg


# simplifes reading things separated by newlines
def getLine(conn):
    msg = b''
    while True:
        ch = conn.recv(1)
        if ch == b'\n' or len(ch) == 0:
            break
        msg += ch
    return msg.decode()


# function that gets inital setup into swarm done
def connectToServer(bitIP, bitPort, clientSock):
    try:
        global filename
        # receives the filename
        filename = getLine(clientSock)
        filename = filename[:-1]
        print ("received filename: " + filename)

        # initalizes chunkMask with all zeros based on numChunks
        # also adds lists to chunksWeHave and chunksData


    except Exception:
        print("Exception occurred when connecting to torrent, closing connection")
        clientSock.close()
        sys.exit(0)




# function to continuously listen for other peers
def listenForPeer():
    #start to listen for other peoples connections and get stuff from others. 
    # Set up listening socket
    try:
        global listener
        global ourListeningPort
        listener = socket(AF_INET, SOCK_STREAM)
        listener.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        listener.bind(('', 0))
        listener.listen(3) ### Support up to 3 simultaneous connections ###
        ourListeningPort = listener.getsockname()[1]
        while True:
                print("Listening for connections")
                threading.Thread(target=giveDataToPeer, args=(listener.accept(),), daemon=True).start()
                print("received a connection")
    except KeyboardInterrupt:
        listener.close()
        print("Shutting down listener.")
            



# main code that sends out threads besides setting up variables at the top
# setting up client socket stuff
clientSock = socket(AF_INET, SOCK_STREAM)
clientSock.connect( (bitIP, bitPort) )   
connectToTorrent(bitIP, bitPort, clientSock)

# getting the initial list of other peers and masks
clientSock.send("CLIENT_LIST\n".encode())
numPeers = int(getLine(clientSock))
print ("received numPeers: " + str(numPeers))

clientList = []
for i in range(numPeers):
    clientList.append(getLine(clientSock))
print(clientList)

# listen for other people who want stuff
listeningThread = threading.Thread(target=listenForPeer, daemon=True)
listeningThread.start()

# making sure we are getting our listening port
time.sleep(1)

# continually ask for chunks, then just listen for other connections.
mainThread = threading.Thread(target=getFile, daemon=True)
mainThread.start()

while True:
    try:
        pass
    except KeyboardInterrupt:
        # make sure the threads are done running
        # properly shutdown the listenThread
        print('\n[Shutting down]')
        listener.close()
        sys.exit(0) 
    
        clientSock.close()
