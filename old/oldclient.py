from pandac.PandaModules import * 
import direct.directbase.DirectStart 
from direct.distributed.PyDatagram import PyDatagram 
from direct.distributed.PyDatagramIterator import PyDatagramIterator 

from direct.gui.DirectGui import * 
import sys 


######################################3 
## 
## Config 
## 

IP = '127.0.0.1' 
PORT = 9099 
USERNAME = "yellow" 
PASSWORD = "mypass" 


######################################3 
## 
## Defines 
## 
## Quote Yellow: This are server opcodes. It tells the server 
## or client what pkt it is receiving. Ie if the pkt starts 
## with 3, the server knows he has to deal with a chat msg 

MSG_NONE            = 0 
CMSG_AUTH           = 1 
SMSG_AUTH_RESPONSE  = 2 
CMSG_CHAT           = 3 
SMSG_CHAT           = 4 
CMSG_DISCONNECT_REQ = 5 
SMSG_DISCONNECT_ACK = 6 

class Client(DirectObject): 
    def __init__(self): 
        self.accept("escape", self.sendMsgDisconnectReq) 
        
        # Create network layer objects 
   ## This is madatory code. Don't ask for now, just use it ;) 
   ## If something is unclear, just ask. 
    
    self.cManager = QueuedConnectionManager() 
        self.cListener = QueuedConnectionListener(self.cManager, 0) 
        self.cReader = QueuedConnectionReader(self.cManager, 0) 
        self.cWriter = ConnectionWriter(self.cManager,0) 

        self.Connection = self.cManager.openTCPClientConnection(IP, PORT,1) 
        self.cReader.addConnection(self.Connection) 

        # Start tasks 
        taskMgr.add(self.readTask, "serverReaderPollTask", -39) 

        # Send login msg to the server 
   ## required to get the whole thing running. 
        self.sendMsgAuth() 

    ######################################## 
    ## 
    ## Addition: 
    ## If in doubt, don't change the following. Its working. 
    ## Here are the basic networking code pieces. 
    ## If you have questions, ask... 
    ## 
    
    def readTask(self, task): 
        while 1: 
            (datagram, data, msgID) = self.nonBlockingRead(self.cReader) 
            if msgID is MSG_NONE: 
                break 
            else: 
                self.handleDatagram(data, msgID) 
                
        return Task.cont 

    def nonBlockingRead(self,qcr): 
        """ 
        Return a datagram iterator and type if data is available on the 
        queued connection reader 
        """ 
        if self.cReader.dataAvailable(): 
            datagram = NetDatagram() 
            if self.cReader.getData(datagram): 
                data = PyDatagramIterator(datagram) 
                msgID = data.getUint16() 
            else: 
                data = None 
                msgID = MSG_NONE 
        else: 
            datagram = None 
            data = None 
            msgID = MSG_NONE 
        # Note, return datagram to keep a handle on the data 
        return (datagram, data, msgID) 

    def handleDatagram(self, data, msgID): 
        """ 
        Check if there's a handler assigned for this msgID. 
        Since we dont have case statements in python, 
        we're using a dictionary to avoid endless elif statements. 
        """ 
    
   ######################################################## 
   ## 
   ## Of course you can use as an alternative smth like this: 
   ## if msgID == CMSG_AUTH: self.msgAuth(msgID, data, client) 
   ## elif... 
    
        if msgID in Handlers.keys(): 
            Handlers[msgID](msgID,data) 
        else: 
            print "Unknown msgID: %d" % msgID 
            print data 
        return        

    def sendMsgAuth(self): 
        
   ######################################################### 
   ## 
   ## This handles the sending of the auth request. 
   ## 
    
   ## 1st. We need to create a buffer 
   pkg = PyDatagram() 
        
   ## 2nd. We put a UInt16 type Number in it. Here its CMSG_AUTH 
   ## what means that the corresponding Value is "1" 
   pkg.addUint16(CMSG_AUTH) 
    
   ## 3rd. We add the username to the buffer after the UInt. 
        pkg.addString(USERNAME) 
    
   ## 4th. We add the password for the username after the username 
        pkg.addString(PASSWORD) 
    
   ## Now that we have a Buffer consisting of a Number and 2 Strings 
   ## we can send it. 
        self.send(pkg) 

    def sendMsgDisconnectReq(self): 
        ##################################################### 
   ## 
   ## This is not used right now, but can be used to tell the 
   ## server that the client is disconnecting cleanly. 
   ## 
   pkg = PyDatagram() 
        
   ## Will be a short paket... we are just sending 
   ## the Code for disconnecting. The server doesn't 
   ## need more information anyways... 
   pkg.addUint16(CMSG_DISCONNECT_REQ) 
        self.send(pkg) 

    def msgAuthResponse(self, msgID, data): 
        
    ################################################## 
    ## 
    ## Here we are going to compare the auth response 
    ## we got from the server. Yellow kept it short, but 
    ## if the server sends a 0 here, it means, the User 
    ## doesn't exist. 1 means: user/pwd combination 
    ## successfull. If the server sends a 2: Wrong PWD. 
    ## Note that its a security risk to do so. That way 
    ## you can easily spy for existing users and then 
    ## check for their passwords, but its a good example 
    ## to show, how what is working. 
    
   flag = data.getUint32() 
        if flag == 0: 
            print "Unknown user" 
        
        if flag == 2: 
            print "Wrong pass, please try again..." 

   if flag == 1: 
            print "Authentication Successfull" 
            
       ###################################################### 
       ## 
       ## Now that we are known and trusted by the server, lets 
       ## send some text! 
       ## 
       
       ## creating the buffer again 
       pkg = PyDatagram() 
       
       ## Putting the Op-Code into the buffer saying that this is 
       ## going to be a chat message. (if you read the buffer you 
       ## would see then a 3 there. Why? Because CMSG_CHAT=3 
            pkg.addUint16(CMSG_CHAT) 
       
       ## Next we are going to add our desired Chat message 
       ## to the buffer. Don't get confused about the %s 
       ## its a useable way to use variables in C++ 
       ## you can write also: 
       ## pkg.addString('Hey, ',USERNAME,' is calling!') 
            pkg.addString("%s is calling in and is glad to be here" % USERNAME) 
            
       ## Now lets send the whole thing... 
       self.send(pkg) 
            
  
    def msgChat(self, msgID, data): 
        
   ########################################################## 
   ## 
   ## Here comes the interaction with the data sent from the server... 
   ## Due to the fact that the server does not send any data the 
   ## client could display, its only here to show you how it COULD 
   ## be used. Of course you can do anything with "data". The 
   ## raw print to console should only show a example. 
   ## 
    
   print data.getString() 

    def msgDisconnectAck(self, msgID, data): 
        
   ########################################################### 
   ## 
   ## If the server sends a "close" command to the client, this 
   ## would be handled here. Due to the fact that he doesn't do 
   ## that, its just another example that does show what would 
   ## be an example about how to do it. I would be careful with 
   ## the example given here... In that case everything a potential 
   ## unfriendly person needs to do is sending you a paket with a 
   ## 6 in it coming from the server (not sure if it even needs to 
   ## be from the server) the application will close... You might 
   ## want to do a double checking with the server again to ensure 
   ## that he sent you the paket... But thats just a advice ;) 
   ## 
    
   ## telling the Manager to close the connection    
   self.cManager.closeConnection(self.Connection) 
        
   ## saying good bye 
   sys.exit() 
    

    def send(self, pkg): 
        self.cWriter.send(pkg, self.Connection) 

    def quit(self): 
        self.cManager.closeConnection(self.Connection) 
        sys.exit() 
        
###################################################################### 
## 
## OK! After all of this preparation lets create a Instance of the 
## Client Class created above. Call it as you wish. Make sure that you 
## use the right Instance name in the dictionary "Handlers" as well... 
## 

aClient = Client() 

###################################################################### 
## 
## That is the second piece of code from the 
## def handleDatagram(self, data, msgID): - Method. If you have 
## trouble understanding this, please ask. 
## 

Handlers = { 
    SMSG_AUTH_RESPONSE  : aClient.msgAuthResponse, 
    SMSG_CHAT           : aClient.msgChat, 
    SMSG_DISCONNECT_ACK : aClient.msgDisconnectAck, 
    } 

####################################################################### 
## 
## As Examples for other Instance names: 
## 
## justAExample = Client() 
## 
## Handlers = { 
##    SMSG_AUTH_RESPONSE  : justAExample.msgAuthResponse, 
##    SMSG_CHAT           : justAExample.msgChat, 
##    SMSG_DISCONNECT_ACK : justAExample.msgDisconnectAck, 
##    } 

    
######################################################################## 
## 
## We need that loop. Otherwise it would run once and then quit. 
##    
run() 