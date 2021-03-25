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

if len(sys.argv) > 3:
    print("Too many arguments try again.")
    sys.exit(0)
elif len(sys.argv) < 2:
    print("Not enough arguments try again.")
    sys.exit(0)
else:
    bitIP = sys.argv[1]
    bitPort = int(sys.argv[2])

ourConnectionPort = 69420
ourListeningPort = 0

# first three variables sent from tracker
filename = ""
chunkSize = 0
numChunks = 0

# list of lists to hold all the chunksizes and their digests
chunkSizesAndDigests = []

# our chunkMask
chunkMask = []

# list of nubmers that correspond to chunks that we dont have
chunksWeDontHave = []

# list of clients that we can connect to 
clientList = []

# list of lists of data that we have so far
chunksData = [] 

# how many peers there are right now
numPeers = 0

# varibale to refer to listener socket later
listener = ""

# simplifes reading things separated by newlines
def getLine(conn):
    msg = b''
    while True:
        ch = conn.recv(1)
        msg += ch
        if ch == b'\n' or len(ch) == 0:
            break
    return msg.decode()


# function that gets inital setup into swarm done
def connectToTorrent(bitIP, bitPort, clientSock):
    try:
        global filename
        # receives the filename
        filename = getLine(clientSock)
        filename = filename[:-1]
        print ("received filename: " + filename)

        # receives chunkSize
        chunkSize = int(getLine(clientSock))
        print ("received chunkSize: " + str(chunkSize))

        # receives numChunks
        numChunks = int(getLine(clientSock))
        print ("received numChunks: " + str(numChunks))

        # initalizes chunkMask with all zeros based on numChunks
        # also adds lists to chunksWeHave and chunksData
        for i in range(numChunks):
            chunkMask.append("0")
            chunksWeDontHave.append(i)
            chunksData.append([])

        # receiving all the chunksizes and digests
        for i in range(numChunks):
            csAndDs = getLine(clientSock)[:-1]
            chunkSizesAndDigests.append(csAndDs.split(','))

        # setting up string of port and mask
        stringChunkMask = "".join(chunkMask)
        portMask = str(ourListeningPort) + "," + stringChunkMask + "\n"

        # sending port and chunkMask
        clientSock.send(portMask.encode())

    except Exception:
        print("Exception occurred when connecting to torrent, closing connection")
        clientSock.close()
        sys.exit(0)


# function to actually send data to a peer
def giveDataToPeer(connInfo):
    try:
        # connect to peer
        clientConn, clientAddr = connInfo
        clientIP = clientAddr[0]
        print("Received connection from %s:%d" %(clientIP, clientAddr[1]))

        # receive the number for chunk they want
        chunkNum = int(getLine(clientConn))
        print ("received chunkNum: " + str(chunkNum))

        # send the chunk they want
        clientConn.send(chunksData[chunkNum][0])

        # close connection
        clientConn.close()

    except Exception:
        print("Exception occurred, closing connection")
        print("Something bad happened while giving data to a peer.")
        clientConn.close()


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
            

# function that gets chunks from another peer
def connectToPeer(peerIP, peerPort, chunkWeWant, clientSock):
    try:
        print("Connecting to: [" + peerIP + " : " + peerPort + "]")
        # making sure to cast peerPort as an int so the connection is made
        peerPort = int(peerPort)
        # connect to peer
        peerSock = socket(AF_INET, SOCK_STREAM)
        peerSock.connect( (peerIP, peerPort) )
        
        # sending the chunknum we want
        ChNum = str(chunkWeWant) + "\n"
        peerSock.send(ChNum.encode())
   
        # receiving all the chunkData
        chunkData = recvAll(peerSock, int(chunkSizesAndDigests[chunkWeWant][0]))
   
        # if you get a zero
        if len(chunkData) == 0:
            print("The Peer didn't send anything.")
            peerSock.close()
            return

        # close connection
        peerSock.close()

        # get digest for the chunk we have received
        dataDigest = hashlib.sha224(chunkData).hexdigest()  
        # check chunk digest
        if dataDigest == chunkSizesAndDigests[chunkWeWant][-1]:
            chunkMask[chunkWeWant] = "1"
            chunksWeDontHave.remove(chunkWeWant)
            # add data to our data array
            chunksData[chunkWeWant].append(chunkData)
        
        else:
            print("That chunk had some bad data.")
            print("We did not add it to chunksData")
            return

        '''
        Here is where we are sending our updated mask and getting the new list of updated peers.
        '''

        # report back to the tracker what you have
        clientSock.send("UPDATE_MASK\n".encode())
        stringChunkMask = "".join(chunkMask)
        stringChunkMask = stringChunkMask + "\n"
        clientSock.send(stringChunkMask.encode())

        # ask for the newest version of connections available.
        clientSock.send("CLIENT_LIST\n".encode())

        # receive int of numclients
        numPeers = int(getLine(clientSock))
        print ("received numPeers: " + str(numPeers))

        # receive that many client ip, port, and masks.
        clientList = []
        for i in range(numPeers):
            clientList.append(getLine(clientSock))

    except Exception:
        print("Exception occurred, closing connection")
        print("Something is wrong with the connection to that peer")
        peerSock.close()


# random sort of way of determining who to grab chunks from.
def determineChunk():
    try:
        chunksPeersHave = []
        for i in range(numPeers):
            clientChunkMask = clientList[i].split(",")[-1]
            for j in range( len(clientChunkMask) - 1 ):
                if (chunkMask[j] == "0" and clientChunkMask[j] == "1"):
                    chunksPeersHave.append((clientList[i].split(":")[0], clientList[i].split(",")[0].split(":")[-1], j ))
                    #The append above adds the ClientIP, ClientPort, and an index to a chunks that peers have to the list
        chunkWeWant = random.choice(chunksPeersHave)
        return chunkWeWant

    except Exception:
        print("No one has that chunk")
        # keeping the number of return values consistent to check later
        return (0,0,0)


# determines chunks and connects to peers and writes to files
def getFile():
    # boolean values 
    written = False
    running = True
    while running:
        try:
            if numPeers > 1 and running == True:
                if written == False:
                    peerIP, peerPort, chunkWeWant = determineChunk()
                    # this is if no one has the chunk
                    if peerIP == 0 and peerPort == 0 and chunkWeWant == 0:
                        pass
                    else:
                        print("peerIP: " + peerIP)
                        print("peerPort: " + peerPort)
                        print("chunkWeWant: " + str(chunkWeWant))
                        # We are creating one connection to another peer at a time 
                        connectToPeer(peerIP, peerPort, chunkWeWant, clientSock)
                        if len(chunksWeDontHave) == 0:
                            with open(filename, 'wb') as outf:
                                # write bytes to file
                                for chunk in chunksData:
                                    outf.write(chunk[0])
                            written = True
                else:
                    running = False
            else:
                running = True
        
        except KeyboardInterrupt:
            print('\n[mainThread shutting down]')
            running = False


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
