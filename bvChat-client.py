from socket import *
import threading
import sys
import os
import copy
import random
import time
import hashlib

if len(sys.argv) != 3:
    print("Incorrect number of arguments")
    exit()

serverIP = sys.argx[1]
serverPort = int(sys.argv[2])

listener = ''

# simplifes reading things separated by newlines
def getLine(conn):
    msg = b''
    while True:
        ch = conn.recv(1)
        if ch == b'\n' or len(ch) == 0:
            break
        msg += ch
    return msg.decode()

def connectToServer(IP, Port):
    Port = int(Port)
    serverSock = socket(AF_INET, SOCL_STREAM)
    serverSock.connect( (IP, Port))
    return serverSock

# function to continuously listen for other peers
def listenToServer():
    #start to listen for other peoples connections and get stuff from others. 
    # Set up listening socket
    try:
        global listener
        listener = socket(AF_INET, SOCK_STREAM)
        listener.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        listener.bind(('', 0))
        listener.listen(1)
        while True:
                print("Listening for connections")
                threading.Thread(target=giveDataToPeer, args=(listener.accept(),), daemon=True).start()
                print("received a connection")
    except KeyboardInterrupt:
        listener.close()

def userInput(serverIP, serverPort):
    logged = False
    while not logged:
        serverSock = connectToServer(serverIP, serverPort) 
        uName = input("Username: ")
        pWord = input("Password: ")
        accountInfo = uName+"\n" + pWord+"\n"
        serverSock.send(accountInfo.encode())
        
        code = getLine(serverSock)
        if code == "ok":
            offlineInt = getLine(serverSock)
            offlineInt = int(offlineInt)
            if offlineInt > 0:
                for i in range(offlineInt):
                    print(getLine(serverSock))
            else:
                print("There were no offline messages")
            logged = True
        else:
            print("Account in use.")
            serverSock.close()

    exit = False
    while not exit:
        inp = input("> ")
        message = inp+"\n"
        serverSock.send(message.encode())



        print("Shutting down listener.")
            


'''
# main code that sends out threads besides setting up variables at the top
# setting up client socket stuff
clientSock = socket(AF_INET, SOCK_STREAM)
clientSock.connect( (clientIP, clientPort) )   
connectToServer(clientIP, clientPort, clientSock)

# getting the initial list of other peers and masks
numPeers = int(getLine(clientSock))

clientList = []
for i in range(numPeers):
    clientList.append(getLine(clientSock))
print(clientList)'''

# listen from the server
listeningThread = threading.Thread(target=listenToServer, daemon=True)
listeningThread.start()

# continually ask for chunks, then just listen for other connections.
mainThread = threading.Thread(target=userInput, daemon=True)
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
