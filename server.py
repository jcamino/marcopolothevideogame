from direct.showbase.ShowBase import ShowBase
from panda3d.core import *
from direct.distributed.PyDatagram import PyDatagram
from direct.distributed.PyDatagramIterator import PyDatagramIterator
from time import time
import random

class Application(ShowBase):
    def __init__(self):
        
        ShowBase.__init__(self)
        
        server = Server(Protocol(), 9999)
        
        self.smiley = loader.loadModel("smiley")
        self.smiley.setPythonTag("velocity", 0)
        self.smiley.reparentTo(render)
        self.smiley.setPos(0, 0, 30)
        self.cam.setPos(0, -100, 10)
        
        #client = Client(ClientProtocol(self.smiley))
        #client.connect("localhost", 9999, 3000)
        
        '''
        print "Starting server"
        ShowBase.__init__(self)
        
        #server = Server(ServerProtocol(), 9999)
                        
        client = Client(ClientProtocol())
        client.connect("128.113.232.77", 9999, 3000)
        data = PyDatagram()
        data.addUint8(0)
        data.addString(str(time()))
        client.send(data)

        while True:
            inputString = raw_input('\t:')
            #print inputString
            reply = PyDatagram()
            reply.addUint8(0)
            reply.addString(str(time()))
            client.send(reply)
        '''
        
        taskMgr.add(self.updateSmiley, "updateSmiley")
        

    def updateSmiley(self, task):
        #print "Updating client smiley"
        vel = self.smiley.getPythonTag("velocity")
        z = self.smiley.getZ()
        
        self.smiley.setZ(z + vel)
        self.smiley.setX(20)
        vel -= 0.01
        self.smiley.setPythonTag("velocity", vel)
        
        return task.cont

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
        self.smiley = ServerSmiley()
        self.frowney = loader.loadModel("frowney")
        self.frowney.reparentTo(render)
        taskMgr.add(self.updateListener, "updateListener")
        taskMgr.add(self.updateSmiley, "updateSmiley")
        taskMgr.doMethodLater(0.25, self.syncSmiley, "syncSmiley")
        
    def updateListener(self, task):
        if self.listener.newConnectionAvailable():
            connection = PointerToConnection()
            if self.listener.getNewConnection(connection):
                connection = connection.p()
                self.connections.append(connection)
                self.reader.addConnection(connection)
                print "Server: New connection established."
                
                
        return task.cont
        
    def updateSmiley(self, task):
        self.smiley.update()
        self.frowney.setPos(self.smiley.pos)
        return task.cont
        
    def syncSmiley(self, task):
        print "SYNCING SMILEYS!"
        sync = PyDatagram()
        sync.addFloat32(self.smiley.vel)
        sync.addFloat32(self.smiley.pos.getZ())
        print self.smiley.pos.getZ()
        sync.addFloat32(self.smiley.pos.getX())
        print self.smiley.pos.getX()
        sync.addFloat32(self.smiley.pos.getY())
        print self.smiley.pos.getY()
        sync.addFloat32(777)
        self.broadcast(sync)
        return task.again
    
    def broadcast(self, datagram):
        for conn in self.connections:
            self.writer.send(datagram, conn)
        
        
            
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
                    
  
        
class ServerSmiley:
    def __init__(self):
        self.pos = Vec3(0, 0, 30)
        self.vel = 0
        
    def update(self):
        #print "Updating server smiley"
        z = self.pos.getZ()
        if z <= 0:
            self.vel = random.uniform(0.1, 0.8)
        self.pos.setZ(z + self.vel)
        self.vel -= 0.01