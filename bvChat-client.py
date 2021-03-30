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
    sys.exit(0)

serverIP = sys.argv[1]
serverPort = int(sys.argv[2])

listener = ''
inp = ""
serverSock = 0

def recMSG(connInfo):
    serverConn, serverAddr = connInfo
    msg = "a"
    while len(msg) != 0:
        msg = getLine(serverConn)
        if len(msg) != 0:
            print(msg + "\n")
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
    # Start to listen for messages from the server 
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
    global listenPort, run, inp, serverSock
    # This while loop logs in the user
    logged = False
    while not logged:
        try:
            serverSock = connectToServer(serverIP, serverPort) 
            listenPort = str(listenPort) + "\n"
            serverSock.send(listenPort.encode())
            uName = ''
            while uName == '':
                uName = input("Username: ")

            pWord = ''
            while pWord == '':
                pWord = input("Password: ")
            
            print("-------------------------------------------------------")
            print("> ", end = '')
            accountName = uName+"\n" 
            accountWord = pWord+"\n"

            serverSock.send(accountName.encode())
            serverSock.send(accountWord.encode())
           
            # The type of login that the user has jsut done (new, old, bad, bad password)
            code = getLine(serverSock)
            if code == "old":
                print("-------------------------------------------------------")
                # If old, check for offline messages
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
                print(" [Failed 3 Attempts. Account is now temporarily banned for 2 minutes]")
                print(" [Rerun program after time is up.] \n {Closing Program}")
                run = False
                serverSock.close()
            elif code == "trying":
                print(" [Bad Attempt] \n [Rerun program to try again] \n {Closing Program}")
                run = False
                serverSock.close()
                sys.exit()
            else:
                print(" [You entered some bad data. Please try again.]")
                serverSock.close()
        except:
            print(" [Your IP is temporarily banned, can't login to any accounts at this moment.]")
            print(" [Rerun program after time is up.] \n {Closing Program}")
            run = False

    # Continually get input from the user after they have logged in
    exit = False
    while not exit:
        try:
            print("-------------------------------------------------------")
            inp = input("> ")
            message = inp+"\n"
            serverSock.send(message.encode())
            inp.lower()
            if inp == "/exit":
                serverSock.close()
                exit = True
                run = False
        except KeyboardInterrupt:
           # FIXME Print out shutting down, and exit the user account
           print('\n[Shutting down]')
           msg = "/exit\n"
           serverSock.send(msg.encode())
           serverSock.close()
           exit = True
           run = False

# Listen for messages from the server
listeningThread = threading.Thread(target=listenToServer, daemon=True)
listeningThread.start()

# Continually ask the user for input
mainThread = threading.Thread(target=userInput, args=(serverIP, serverPort), daemon=True)
mainThread.start()
run = True
while run:
    try:
        pass
    except KeyboardInterrupt:
        msg = "/exit\n"
        serverSock.send(msg.encode())
        print("second kb interrupt")
        print('\n[Shutting down]')
        sys.exit(0)
sys.exit(0) 
