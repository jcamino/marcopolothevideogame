from direct.showbase.ShowBase import ShowBase
from panda3d.core import *
from direct.distributed.PyDatagram import PyDatagram
from direct.distributed.PyDatagramIterator import PyDatagramIterator
from time import time
import random

class Application(ShowBase):
    def __init__(self):
        
        ShowBase.__init__(self)
        
        self.smiley = loader.loadModel("smiley")
        self.smiley.setPythonTag("velocity", 0)
        self.smiley.reparentTo(render)
        self.smiley.setPos(0, 0, 30)
        self.cam.setPos(0, -100, 10)
        
        client = Client(ClientProtocol(self.smiley))
        client.connect("localhost", 9999, 3000)
        
        taskMgr.add(self.updateSmiley, "updateSmiley")
        


    def updateSmiley(self, task):
        pass
    '''return task.cont
    
        #print "Updating client smiley"
        vel = self.smiley.getPythonTag("velocity")
        
        #z = self.smiley.getPythonTag("znew")
        z = self.smiley.getZ()
        
        if z <= 0:
            vel = random.uniform(0.1, 0.8)
        
        self.smiley.setZ(z + vel)
        self.smiley.setX(20)
        vel -= 0.01
        self.smiley.setPythonTag("velocity", vel)'''
        

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
            
        
class ClientProtocol(Protocol):
    def __init__(self, smiley):
        self.smiley = smiley
    
    def process(self, data):
        it = PyDatagramIterator(data)
        vel = it.getFloat32()
        z = it.getFloat32()
        x = it.getFloat32()
        y = it.getFloat32()
        checksum = it.getFloat32()
        
        print "velocity:" , vel ,
        " Z position:" , z , " Checksum " , checksum
        
        newx = x
        zdiff = z - self.smiley.getZ()
        #self.smiley.setPythonTag("velocity", vel + zdiff * 0.03)
        
        self.smiley.setX(x)
        self.smiley.setZ(z)
        self.smiley.setY(y)
        return None

        
        