from socket import *
import threading
import hashlib
import sys
import os
import random
import time
import linecache

# Our port
port=55555

# Holds times of fails
fails = {}
failsLock = threading.Lock()

# If the user is banned
isBanned = {}

# Creation connection dictionary of people CURRENTLY CONNECTED 
# Holds the usernames and IPs and Ports
clientList = {}
clientListLock = threading.Lock()

# Dictionary of usernames from FILE
listOfUsers = {}

# Holds the offline messages
offlineMessages = {}
offlineMessagesLock = threading.Lock()

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
f.write("It's a great day to be a Beaver!\nBe like water my friend.\nLooking good hot stuff.")
f.close()
f = open("motd.txt", 'r')

# Getting a random message from the message of the day file
messageOfTheDay = linecache.getline('motd.txt', random.randint(1,3))

# Fills isBanned
def fillBanForIP(ip):
    global isBanned, fails
    isBanned[ip] = False
    failsLock.acquire()
    fails[ip] = [0,0,0]
    failsLock.release()

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
    global clientList
    clients = []
    clientListLock.acquire()
    for key in clientList:
        clients.append(key)
    clientListLock.release()
    return clients

# Removes a pre-existing client from participation in the chat
def removeClientInfo(uName):
    global clientList
    clientListLock.acquire()
    del clientList[uName]
    clientListLock.release()
    printClientList()

def broadcastMessage(message, sender):
    clients = getListOfClientsNow()
    message = "[ " + sender + " ]: " + message
    for key in clientList:
        ip = clientList[key][0]
        port = int(clientList[key][1])
        sendingSock = socket(AF_INET, SOCK_STREAM)
        sendingSock.connect( (ip, port) )
        sendingSock.send(message.encode())

def emoteMessage(message, sender):
    clients = getListOfClientsNow()
    for key in clientList:
        ip = clientList[key][0]
        port = int(clientList[key][1])
        sendingSock = socket(AF_INET, SOCK_STREAM)
        sendingSock.connect( (ip, port) )
        sendingSock.send(message.encode())

def tell(message, sender, receiver):
    ip = clientList[receiver][0]
    port = int(clientList[receiver][1])
    sendingSock = socket(AF_INET, SOCK_STREAM)
    sendingSock.connect( (ip, port) )
    clients = getListOfClientsNow()
    message = "{DM from " + sender + "}: " + message
    sendingSock.send(message.encode())

# Continuously listens for commands from the client that is passed 
def listenToClient(conn, name):
    clientConnected = True
    while clientConnected:
        clientMessage = getLine(conn)
        # If the message is a command
        try:
            if clientMessage[0] == "/":
                # Split off the command from the message
                clientMessageList = clientMessage.split(" ", 1)
                command = clientMessageList[0].lower()
                # Check what message it is
                if command == "/who":
                    ip = clientList[name][0]
                    port = int(clientList[name][1])
                    sendingSock = socket(AF_INET, SOCK_STREAM)
                    sendingSock.connect( (ip, port) )
                    # Sends the number of clients
                    # Then sends the string of clients separated by a newline
                    numClients, clientsMsg = getClientListMsg()
                    numClients = str(numClients) + "\n"
                    sendingSock.send(numClients.encode())
                    sendingSock.send(clientsMsg.encode())
                elif command == "/exit":
                    # Delete from the currently connected dict
                    removeClientInfo(name)
                    # Send who left the chat
                    message = "<Left the chat.>"
                    broadcastMessage(message, name)
                    # Disconnect from the client
                    conn.close()
                    # Stop listening to the client
                    return
                elif command == "/tell":
                    global offlineMessages
                    clientMessageList =  clientMessageList[1].split(" ", 1)
                    receiver = clientMessageList[0]
                    message = clientMessageList[1]
                    # If the receiver is logged in
                    if receiver in clientList:
                        tell(message, name, receiver)
                    # If the receiver is NOT logged in store the message for later
                    elif receiver in listOfUsers:
                        message = str("{DM from " + name + "}: " + message)
                        if receiver in offlineMessages:
                            offlineMessages[receiver].append(message)
                        else:
                            offlineMessages[receiver] = [message]
                    else:
                        print("That user does not exist.")
                elif command == "/motd":
                    ip = clientList[name][0]
                    port = int(clientList[name][1])
                    sendingSock = socket(AF_INET, SOCK_STREAM)
                    sendingSock.connect( (ip, port) )
                    sendingSock.send(messageOfTheDay.encode())
                elif command == "/me":
                    message = "*" + name + " " + clientMessageList[1]
                    emoteMessage(message, name)
                elif command == "/help":
                    ip = clientList[name][0]
                    port = int(clientList[name][1])
                    sendingSock = socket(AF_INET, SOCK_STREAM)
                    sendingSock.connect( (ip, port) )
                    helpCommands = 'The available commands are:\n/who\n/exit\n/tell <username> "message"\n/motd\n/me\n/help\n'
                    sendingSock.send(helpCommands.encode())
                else:        
                    print(command + " is an invalid command.")

            # Broadcast the message
            else:
                broadcastMessage(clientMessage, name)
        except:
            pass

# Handles the inital setup of a login or new client
def firstClientConn(connInfo):
    global isBanned, fails
    clientConn, clientAddr = connInfo
    clientIP = clientAddr[0]
    if clientIP not in isBanned:
        fillBanForIP(clientIP)
    if isBanned[clientIP] == True:
        return 
    clientPort = clientAddr[1]
    print("Received connection from %s:%d" %(clientIP, clientPort))
    try:
        # Get port the client is listening on 
        sendPort = getLine(clientConn)
        print("Client sending port: " + sendPort)
        sendPort = int(sendPort)
        # receive username and password
        username = getLine(clientConn)
        print("username: " + username)
        password = getLine(clientConn)
        print("password: " + password)
         
        # If the user enters a bad password and a good username
        if username in listOfUsers and password != listOfUsers[username]:
            # Add the latest fail to fails 
            failsLock.acquire()
            fails[clientIP][0] = fails[clientIP][1]
            fails[clientIP][1] = fails[clientIP][2]
            fails[clientIP][2] = time.time()
            failsLock.release()
            # If they fails too many time in 30 seconds ban them and make them wait
            if fails[clientIP][0] != 0 and fails[clientIP][2] - fails[clientIP][0] <= 30:
                isBanned[clientIP] = True
                ban = "ban\n"
                clientConn.send(ban.encode())
                clientConn.close()
                time.sleep(120)
                isBanned[clientIP] = False
                return
            # If they fail, but not three times in 30 seconds yet
            else:
                msg = "trying\n"
                clientConn.send(msg.encode())
                clientConn.close()
                return
        # If user is already logged in 
        elif username in clientList:
            print("That person is already logged in. You can only login once.")
            bad = "bad\n"
            clientConn.send(bad.encode())
            # disconect from client and return
            clientConn.close()
            return 
        # Log the user in if username and password matches
        elif username in listOfUsers and password == listOfUsers[username]:
            # Log them in
            clientListLock.acquire()
            clientList[username] = [clientIP, sendPort]
            clientListLock.release()
            old = "old\n"
            clientConn.send(old.encode())
            # Sending offline direct messages
            if username in offlineMessages:
                offlineMessagesLock.acquire()
                numMessages = len(offlineMessages[username])
                numMessages = str(numMessages) + "\n"
                clientConn.send(numMessages.encode())
                for m in offlineMessages[username]:
                    m = m + "\n"
                    clientConn.send(m.encode())
                del offlineMessages[username]
                offlineMessagesLock.release()
            else:
                zero = "0\n"
                clientConn.send(zero.encode())
        # Add a new user to the current users and file of users
        else:
            # Write user to file
            f = open('accounts.txt', 'a')
            f.write(username+":"+password+"\n")
            f.close()
            # Log them in
            clientListLock.acquire()
            clientList[username] = [clientIP, sendPort]
            clientListLock.release()
            ok = "new\n"
            clientConn.send(ok.encode())
            fillListOfUsers()
   
        # Send Welcome to the chat
        welcome = "Welcome to the chat. Keep it PG-13. Type '/help' to see commands.\n"
        clientConn.send(welcome.encode())
        # Send message of the day
        clientConn.send(messageOfTheDay.encode())
        # Broadcast who just joined
        message = "-- " + username + " has entered the chat --"
        emoteMessage(message, username)
        # Call function to listen for commands from client possibly in a thread
        listenToClient(clientConn, username)
    
    except Exception:
        print("Exception occurred, closing connection")
    

running = True
fillListOfUsers()
while running:
    try:
        threading.Thread(target=firstClientConn, args=(listener.accept(),), daemon=True).start()
    except KeyboardInterrupt:
        print('\n[Shutting down]')
        running = False
