from socket import *
import threading
import hashlib
import sys
import os
import random
import time
import linecache

port=55555

# Creation connection dictionary of people CURRENTLY CONNECTED 
clientList = {}
clientListLock = threading.Lock()

# Dictionary of usernames from FILE
listOfUsers = {}

# Set up listening socket
listener = socket(AF_INET, SOCK_STREAM)
listener.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
listener.bind(('', port))
listener.listen(32) # Support up to 32 simultaneous connections

# Check to see if we have a file that holds all the accounts yet
if os.path.exists("accounts.txt"):
    pass
else:
    f = open("accounts.txt", 'w')
    f.close()

# Creating the message of the day file
f = open("motd.txt", 'w')
f.write("Message of the day.\nWelcome to bvChat.\nLooking good hot stuff.")
f.close()
f = open("motd.txt", 'r')

# Getting a random message from the message of the day file
message = linecache.getline('motd.txt', random.randint(0, 2))

# List to hold the types of messages 
types = ["who", "exit", "tell", "motd", "me", "help"]

# Adds all the usernames and password to a dictionary
def fillListOfUsers():
    f = open('accounts.txt', 'r')
    for line in f:
        strippedLine = line.rstrip()
        splitLine = strippedLine.split(":")
        listOfUsers[splitLine[0]] = splitLine[1]

# Retrieves the number of bytes specified
def getFullMsg(conn, msgLength):
    msg = b''
    while len(msg) < msgLength:
        retVal = conn.recv(msgLength - len(msg))
        msg += retVal
        if len(retVal) == 0:
            break    
    return msg

# Retrieves stuff until we hit a newline
def getLine(conn):
    msg = b''
    while True:
        ch = conn.recv(1)
        if ch == b'\n' or len(ch) == 0:
            break
        msg += ch
    return msg.decode()

# Produces a newline delimited string of client usernames
def getClientListMsg():
    clientMsg = ""
    clientListLock.acquire()
    numClients = len(clientList)
    for key in clientList:
        clientMsg += key + "\n"
    clientListLock.release()
    return (numClients, clientMsg)

# Displays who is connected right now
def printClientList():
    print("Updated list of peers in chat")
    clientListLock.acquire()
    for key in clientList:
        print(key + " -> "+ clientList[key])
    clientListLock.release()

# Removes a pre-existing client from participation in the chat
def removeClientInfo(uName):
    clientListLock.acquire()
    del clientList[uName]
    printClientList()
    clientListLock.release()

# Continuously listens for commands from the client that is passed 
def listenToClient(conn, name):
    #TODO
    clientConnected = True
    while clientConnected:
        clientMessage = getLine(conn)
        if clientMessage[0] == "/":
            # Split off the command from the message
            clientMessageList = clientMessage.split(" ", 1)
            clientMessageList[0] = clientMessageList[1:]
            command = clientMessageList[0]
            # Check what message it is
            if command.lower() == "who":
                #TODO
            elif command.lower() == "exit":
                #TODO
            elif command.lower() == "tell":
                #TODO
            elif command.lower() == "motd":
                #TODO
            elif command.lower() == "me":
                #TODO
            elif command.lower() == "help":
                #TODO
            else:
                #TODO
            
            # do that stuff
        else:
            # Send three things
            # 1. clientName sending the message
            # 2. b or d for if the message is broadcast or direct message
            # 3. The actual message itself
            #TODO

# Handles the inital setup of a login or new client
def firstClientConn(connInfo):
    clientConn, clientAddr = connInfo
    clientIP = clientAddr[0]
    clientPort = clientAddr[1]
    print("Received connection from %s:%d" %(clientIP, clientPort))

    try:
        # receive username and password
        username = getLine(clientConn)
        print("username: " + username)
        password = getLine(clientConn)
        print("password: " + password)
         
        # If user is already logged in 
        if username in clientList:
            print("You are already logged in. You can only login once.")
            # disconect from client and return
            clientConn.close()
            return 
        # If username is already taken
        elif username in listOfUsers:
            print("Username is taken already.")
            # disconect from client and return
            clientConn.close()
            return
        # Log the user in if username and password matches
        elif username in listOfUsers and password == listOfUsers[username]
            # log them in
            clientListLock.acquire()
            clientList[username] = [clientIP, clientPort]
        # Add a new user to the current users and file of users
        else:
            # Write user to file
            f = open('accounts.txt', 'a')
            f.write(username+":"+password+"\n")
            f.close()
            # Write user to currently connected dictionary
            clientListLock.acquire()
            clientList[username] = [clientIP, clientPort]
            clientListLock.release()
            

        # Send message of the day
        clientConn.send(message.encode())
        # Call function to listen for commands from client possibly in a thread
        listenToClient(clientConn, username)

    except Exception:
        print("Exception occurred, closing connection")

    clientConn.close()
    removeClientInfo(clientIP, clientPort)
    

running = True

fillListOfUsers()
while running:
    try:
        threading.Thread(target=firstClientConn, args=(listener.accept(),), daemon=True).start()
    except KeyboardInterrupt:
        print('\n[Shutting down]')
        running = False
