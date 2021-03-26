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
# Holds the usernames and connection objects
clientList = {}
clientListLock = threading.Lock()

# Dictionary of usernames from FILE
listOfUsers = {}

# Holds the offline messages
offlineMessages = {}

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
messageOfTheDay = linecache.getline('motd.txt', random.randint(0, 2))

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
    print("Updated list of users in chat")
    clientListLock.acquire()
    for key in clientList:
        print(key)
    clientListLock.release()

# Creates and returns a list of client usernames currently connected 
# Helps so we can get an updated list of people connected
def getListOfClientsNow():
    clients = []
    clientListLock.acquire()
    for key in clientList:
        clients.append(key)
    clientListLock.release()
    return clients

# Removes a pre-existing client from participation in the chat
def removeClientInfo(uName):
    clientListLock.acquire()
    del clientList[uName]
    printClientList()
    clientListLock.release()

def broadcastMessage(message, sender):
    clients = getListOfClientsNow()
    message = "[ " + sender + " ]: " + message
    for key in clientList:
        conn = clientList[key]
        conn.send(message.encode())

def tell(message, sender, receiver):
    clients = getListOfClientsNow()
    message = "{DM from " + sender + "}: " + message
    conn = clientList[key]
    conn.send(message.encode())

# Continuously listens for commands from the client that is passed 
def listenToClient(conn, name):
    clientConnected = True
    while clientConnected:
        clientMessage = getLine(conn)
        # If the message is a command
        if clientMessage[0] == "/":
            # Split off the command from the message
            clientMessageList = clientMessage.split(" ", 1)
            clientMessageList[0] = clientMessageList[1:]
            command = clientMessageList[0].lower()
            # Check what message it is
            if command == "who":
                # Sends the number of clients
                # Then sends the string of clients separated by a newline
                numClients, clientsMsg = getClientListMsg()
                conn.send(numClients.encode())
                conn.send(clientsMsg.encode())
            elif command == "exit":
                # Disconnect from the client
                conn.close()
                # Delete from the currently connected dict
                removeClientInfo(name)
                # Stop listening to the client
                return
            elif command == "tell":
                clientMessageList =  clientMessageList[1].split(" ", 1)
                receiver = clientMessageList[1][0]
                message = clientMessageList[1][1]
                # If the receiver is logged in
                if receiver in clientList:
                    tell(message, name, receiver)
                # If the receiver is NOT logged in store the message for later
                elif receiver in listOfUsers:
                    message = "{DM from " + sender + "}: " + message
                    if receiver in offlineMessages:
                        offlineMessage[receiver].append(message)
                    else:
                        offlineMessages[receiver] = [message]
                else:
                    print("That user does not exist.")
            elif command == "motd":
                conn.send(messageOfTheDay.encode())
            elif command == "me":
                message = "*" + name + " " + clientMessageList[1]
                broadcastMessage(message, name)
            elif command == "help":
                #TODO Can help be on the client side??????????
            else:        
                print(command + " is an invalid command.")

        # Broadcast the message
        else:
            broadcastMessage(clientMessage, name)

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
            print("That person is already logged in. You can only login once.")
            clientConn.send("bad\n")
            # disconect from client and return
            clientConn.close()
            return 
        # If username is already taken
        elif username in listOfUsers:
            print("Username is taken already.")
            clientConn.send("bad\n")
            # disconect from client and return
            clientConn.close()
            return
        # Log the user in if username and password matches
        elif username in listOfUsers and password == listOfUsers[username]
            # Log them in
            clientListLock.acquire()
            clientList[username] = clientConn
            clientConn.send("ok\n")
            # Sending offline direct messages
            if username in offlineMessages:
                numMessages = len(offlineMessages[username])
                numMessages = str(numMessages) + "\n"
                clientConn.send(numMessages.encode())
                for m in offlineMessages[username]:
                    clientConn.send(m.encode())
            else:
                clientConn.send("0\n")
        # Add a new user to the current users and file of users
        else:
            # Write user to file
            f = open('accounts.txt', 'a')
            f.write(username+":"+password+"\n")
            f.close()
            # Log them in
            clientListLock.acquire()
            clientList[username] = clientConn
            clientListLock.release()
            clientConn.send("ok\n")

        # Send message of the day
        clientConn.send(messageOfTheDay.encode())
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
