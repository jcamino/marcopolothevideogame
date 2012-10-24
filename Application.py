from direct.showbase.ShowBase import ShowBase
from panda3d.core import *
from direct.distributed.PyDatagram import PyDatagram
from direct.distributed.PyDatagramIterator import PyDatagramIterator

class Application(ShowBase):
    def __init__(self):
        print "Starting server"
        ShowBase.__init__(self)
        server = Server(ServerProtocol(), 9999)
        client = Client(ClientProtocol())
        client.connect("localhost", 9999, 3000)
        data = PyDatagram()
        data.addUint8(0)
        data.addString("Hello!")
        client.send(data)

class NetCommon:
    def __init__(self, protocol):
        self.manager = ConnectionManager()
        self.reader = QueuedConnectionReader(self.manager, 0)
        self.writer = ConnectionWriter(self.manager, 0)
        self.protocol = protocol
        taskMgr.add(self.updateReader, "updateReader")
        
    def updateReader(self, task):
        if self.reader.dataAvailable():
            data = NetDatagram()
            self.reader.getData(data)
            reply = self.protocol.process(data)
        
            if reply != None:
                self.writer.send(reply, data.getConnection())
       
        return task.cont


class Server(NetCommon):
    def __init__(self, protocol, port):
        NetCommon.__init__(self, protocol)
        self.listener = QueuedConnectionListener(self.manager, 0)
        socket = self.manager.openTCPServerRendezvous(port, 100)
        self.listener.addConnection(socket)
        self.connections = []
        
        taskMgr.add(self.updateListener, "updateListener")
        
    def updateListener(self, task):
        if self.listener.newConnectionAvailable():
            connection = PointerToConnection()
            if self.listener.getNewConnection(connection):
                connection = connection.p()
                self.connections.append(connection)
                self.reader.addConnection(connection)
                print "Server: New connection established."
                
                
        return task.cont
        
        
class Client(NetCommon):
    def __init__(self, protocol):
        NetCommon.__init__(self, protocol)
    
    def connect(self, host, port, timeout):
        self.connection = self.manager.openTCPClientConnection(host, port, timeout)
        if self.connection:
            self.reader.addConnection(self.connection)
            print "Client: Connected to server."
            
    def send(self, datagram):
        if self.connection:
            self.writer.send(datagram, self.connection)
            
            
class Protocol:
    def process(self, data):
        return None
  
    def printMessage(self, title, msg):
        print "%s %s" % (title, msg)
   
    def buildReply(self, msgid, data):
        reply = PyDatagram()
        reply.addUint8(msgid)
        reply.addString(data)
        return reply
            
            
            
            
class ServerProtocol(Protocol):
    def process(self, data):
        it = PyDatagramIterator(data)
        msgid = it.getUint8()
        if msgid == 0:
            return self.handleHello(it)
        elif msgid == 1:
            return self.handleQuestion(it)
        elif msgid == 2:
            return self.handleBye(it)
        
    
    def handleHello(self, it):
        self.printMessage("Server received:", it.getString())
        return self.buildReply(0, "Hello, too!")
        
    
    def handleQuestion(self, it):
        self.printMessage("Server received:", it.getString())
        return self.buildReply(1, "I'm fine. How are you?")
        
    
    def handleBye(self, it):
        self.printMessage("Server received:", it.getString())
        return self.buildReply(2, "Bye!")
                    
                
                
                
class ClientProtocol(Protocol):
    def process(self, data):
        it = PyDatagramIterator(data)
        msgid = it.getUint8()
        if msgid == 0:
            return self.handleHello(it)
        elif msgid == 1:
            return self.handleQuestion(it)
        elif msgid == 2:
            return self.handleBye(it)
        
    def handleHello(self, it):
        self.printMessage("Client received:", it.getString())
        return self.buildReply(1, "How are you?")
        
    def handleQuestion(self, it):
        self.printMessage("Client received:", it.getString())
        return self.buildReply(2, "I'm fine too. Gotta run! Bye!")
        
    def handleBye(self, it):
        self.printMessage("Client received:", it.getString())
        return None
                    
           