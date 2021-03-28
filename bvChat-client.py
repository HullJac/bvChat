from socket import *
import threading
import sys
import os
import copy
import random
import time
import hashlib

listenPort = random.randint(1000,5000)

if len(sys.argv) != 3:
    print("Incorrect number of arguments")
    exit()

serverIP = sys.argv[1]
serverPort = int(sys.argv[2])

listener = ''

def recMSG(connInfo):
    print()
    serverConn, serverAddr = connInfo
    msg = "a"
    while len(msg) != 0:
        msg = getLine(serverConn)
        if len(msg) != 0:
            print(msg)
        else:
            pass

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
    serverSock = socket(AF_INET, SOCK_STREAM)
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
        listener.bind(('', listenPort))
        listener.listen(1)
        while True:
                threading.Thread(target=recMSG , args=(listener.accept(),), daemon=True).start()

    except KeyboardInterrupt:
        listener.close()

def userInput(serverIP, serverPort):
    global listenPort
    logged = False
    while not logged:
        serverSock = connectToServer(serverIP, serverPort) 
        listenPort = str(listenPort) + "\n"
        serverSock.send(listenPort.encode())
        uName = input("Username: ")
        pWord = input("Password: ")

        print("name: " + uName + " word: " + pWord)
        print("-------------------------------------------------------")
        accountName = uName+"\n" 
        accountWord = pWord+"\n"
        serverSock.send(accountName.encode())
        serverSock.send(accountWord.encode())
        
        code = getLine(serverSock)
        print(code)
        if code == "old":
            print("-------------------------------------------------------")
            offlineInt = int(getLine(serverSock))
            if offlineInt > 0:
                for i in range(offlineInt):
                    print(getLine(serverSock))
            else:
                print("There were no offline messages")
            print("-------------------------------------------------------")
            entryMSG = getLine(serverSock)
            print(entryMSG)
            motd = getLine(serverSock)
            print("Message Of The Day: " + motd)
            logged = True
        elif code == "new":
            entryMSG = getLine(serverSock)
            print(entryMSG)
            motd = getLine(serverSock)
            print("Message Of The Day: " + motd)
            logged = True
        elif code == "ban":
            print("Failed 3 Attempts. Account is now temporarily banned for 1 minute")
            serverSock.close()
        elif code == "trying":
            print("Bad Attempt")
            serverSock.close()
            #sys.exit()
        else:
            print("Account in use.")
            serverSock.close()

    exit = False
    global run
    while not exit:
        print("-------------------------------------------------------")
        inp = input("> ")
        message = inp+"\n"
        serverSock.send(message.encode())
        inp.lower()

        try:
            if inp == "/exit":
                serverSock.send(inp.encode())
                print("inside try /exit")
                serverSock.close()
                exit = True
                run = False
                #sys.exit(0)
        except KeyboardInterrupt:
            # FIXME print out exit, and exit the user account
            print("first kb interrupt")
            print('\n[Shutting down]')
            #listener.close()
            serverSock.close()
            exit = True
            run = False
            #sys.exit(0) 
    





# listen from the server
listeningThread = threading.Thread(target=listenToServer, daemon=True)
listeningThread.start()

# continually ask for chunks, then just listen for other connections.
mainThread = threading.Thread(target=userInput, args=(serverIP, serverPort), daemon=True)
mainThread.start()
run = True
while run:
    try:
        pass
    except KeyboardInterrupt:
        # FIXME print out exit, and exit the user account
        print("second kb interrupt")
        print('\n[Shutting down]')
        #listener.close()
        #serverSock.close()
        sys.exit(0)
sys.exit(0)
