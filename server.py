from direct.showbase.ShowBase import ShowBase
from panda3d.core import *
from direct.gui.OnscreenText import OnscreenText
from direct.gui.DirectGui import *
from direct.distributed.PyDatagram import PyDatagram
from direct.distributed.PyDatagramIterator import PyDatagramIterator
from time import time
import random, math

direction = {0:-1, 1: -1, 2: -1, 3:-1, 4:-1, 5:-1}

class Application(ShowBase):
    def __init__(self):
    
        
        
        ShowBase.__init__(self)
        
        self.server = Server(Protocol(self), 9999,self)
        
        self.smiley = loader.loadModel("smiley")
        self.smiley.setPythonTag("velocity", 0)
        self.smiley.reparentTo(render)
        self.smiley.setPos(0, 0, 30)
        self.cam.setPos(0, -100, 10)
        self.direction = "0"
        
        self.players = []
        
        for i in range (0,5):
            self.players.append(0)
            self.players[i] = loader.loadModel('models/proton')
            self.players[i].reparentTo(render)
            self.players[i].setScale(0.5)
            self.players[i].setY(9999)
            self.players[i].setName(str(i))
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
        
        #taskMgr.add(self.updateSmiley, "updateSmiley")
        
        
        

    def updateSmiley(self, task):
        #print "Updating client smiley"
        vel = self.smiley.getPythonTag("velocity")
        z = self.smiley.getZ()
        
        self.smiley.setZ(z + vel)
        self.smiley.setX(20)
        vel -= 0.01
        self.smiley.setPythonTag("velocity", vel)
        #print direction['1']
        
        return task.cont

class NetCommon:
    def __init__(self, protocol):
        self.manager = ConnectionManager()
        self.reader = QueuedConnectionReader(self.manager, 0)
        self.writer = ConnectionWriter(self.manager, 0)
        self.protocol = protocol
        taskMgr.doMethodLater(0.25,self.updateReader, "updateReader")
        
    def updateReader(self, task):
        if self.reader.dataAvailable():
            data = NetDatagram()
            self.reader.getData(data)
            reply = self.protocol.process(data)
        
            if reply != None:
                self.writer.send(reply, data.getConnection())
       
        return task.cont


class Server(NetCommon):
    def __init__(self, protocol, port,Server):
        NetCommon.__init__(self, protocol)
        self.listener = QueuedConnectionListener(self.manager, 0)
        socket = self.manager.openTCPServerRendezvous(port, 15)
        
        self.listener.addConnection(socket)
        self.connections = []
        self.smiley = ServerSmiley()
        self.Server = Server
        self.frowney = loader.loadModel("frowney")
        self.frowney.reparentTo(render)
        taskMgr.doMethodLater(.25, self.updateListener, "updateListener")
        
        self.isStarted = False
        
        self.poloScores = []
        for i in range(0,5):
            self.poloScores.append(0.0)
        #taskMgr.add(self.updateSmiley, "updateSmiley")
        taskMgr.doMethodLater(0.25, self.syncSmiley, "syncSmiley")
        self.startButton = DirectButton(text=('START','START','START','disabled'), text_bg=(1.0,0.1,0.1,1.0),text_pos=(0,-0.5),command=self.start) 
        
    def MarcoLoses(self,task):
        if self.isStarted:
            update = PyDatagram()
            update.addUint8(39)
            winner = 1
            for i in range(1,len(self.Server.players)):
                if self.poloScores[i]>self.poloScores[winner]:
                    winner = i
                        
            update.addUint8(winner)
            
        return task.cont
            
        
    def start(self):
        if self.Server.players[1].getY() != 9999:
            self.isStarted = True
            taskMgr.doMethodLater(0.25,self.update_winner, "updateWinnerTask")
            taskMgr.doMethodLater(60,self.MarcoLoses,"marcoLosestask")
            self.startButton.destroy()
        
        
    def update_winner(self,task):
        closest=0
        closestDist = 999999
        for i in range(1,len(self.Server.players)):
            x=self.Server.players[i].getX()
            y=self.Server.players[i].getY()
            z=self.Server.players[i].getZ()
            mx=self.Server.players[0].getX()
            my=self.Server.players[0].getY()
            mz=self.Server.players[0].getZ()
            dist=math.sqrt((x-mx)**2+(y-my)**2+(z-mz)**2)
            
            #print i, dist
            if dist <closestDist:
                closest = i
                closestDist=dist
                    
        #print closest, " is the closest"
        self.poloScores[closest]+=100.0/24.0/10000.0
                    
        update = PyDatagram()
        update.addUint8(101)
        
        for score in self.poloScores:
            update.addFloat32(score)
        self.broadcast(update)
        return task.cont
        
        
    def updateListener(self, task):
        if self.listener.newConnectionAvailable():
            connection = PointerToConnection()
            if self.listener.getNewConnection(connection):
                connection = connection.p()
                connection.setNoDelay(True)
                self.connections.append(connection)
                self.reader.addConnection(connection)
                print "Server: New connection established."

                self.tempClientID = -1
                for client in range(0,len(direction)):
                    if direction[client] == -1:
                        direction[client] = 0
                        #print "Client ID ",client
                        self.tempClientID = client
                        break
                if self.tempClientID == -1:
                    print "Server is full, keeping connection but giving fake ID!"
                    
                reply = PyDatagram()
                reply.addUint8(42)
                reply.addInt8(self.tempClientID)
                self.writer.send(reply,connection)
                print "Giving new client ID: ",self.tempClientID
                
                
        return task.cont
        
    def updateSmiley(self, task):
        self.smiley.update()
        self.frowney.setPos(self.smiley.pos)
        return task.cont
        
    def syncSmiley(self, task):
        for tempID in range(0,5):
            sync = PyDatagram()
            sync.addUint8(13)
            sync.addInt8(tempID)
            
            sync.addFloat32(self.Server.players[tempID].getX())
            sync.addFloat32(self.Server.players[tempID].getY())
            sync.addFloat32(self.Server.players[tempID].getZ())
            sync.addFloat32(self.Server.players[tempID].getH())
            sync.addFloat32(self.Server.players[tempID].getP())
            sync.addFloat32(self.Server.players[tempID].getR())
            
            print "The velocity is ", self.Server.players[tempID].getTag("velocity")
            
            sync.addFloat32(1.0) #sync.addFloat32(float(self.Server.players[tempID].getTag("velocity")))
            self.broadcast(sync)    
            
        return task.again
        '''        
        print "SYNCING SMILEYS!"
        
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
        '''   
    def broadcast(self, datagram):
        for conn in self.connections:
            self.writer.send(datagram, conn)
        
        
            
class Protocol:
    def __init__(self, Application):
        self.Application  = Application
        
    def process(self, data):
        #print "Got some data"
        it = PyDatagramIterator(data)
        msgid = it.getUint8()
        
        if msgid == 1:
            direction['1']=it.getString()
            #self.printMessage("Server received:", direction['1'])
        
        if msgid == 23:
            print "server got shout out"
            update = PyDatagram()
            update.addUint8(23)
            self.Application.server.broadcast(update)
        #standard update
        if msgid == 13:
            tempID = it.getInt8()
            #print "updating position for player ", tempID
            
            self.Application.players[tempID].setX(it.getFloat32())
            self.Application.players[tempID].setY(it.getFloat32())
            self.Application.players[tempID].setZ(it.getFloat32())
            self.Application.players[tempID].setH(it.getFloat32())
            self.Application.players[tempID].setP(it.getFloat32())
            self.Application.players[tempID].setR(it.getFloat32())
            
            self.Application.players[tempID].setPythonTag("velocity",it.getFloat32())
            #self.printMessage("Server received:", direction[2])        
        
        
        elif msgid == 38:
            if self.Application.server.isStarted is True:
                print "Game over"
                data = PyDatagram()
                data.addInt8(38)
                self.Application.server.broadcast(data)
        '''if msgid == 3:
            direction['3']=it.getString()
           3 self.printMessage("Server received:", direction['3'])  

        if msgid == 4:
            direction['4']=it.getString()
            self.printMessage("Server received:", direction['4'])

        if msgid == 5:
            direction['5']=it.getString()
            self.printMessage("Server received:", direction['5'])
'''
            
        return None
  
    def printMessage(self, title, msg):
        print "%s %s" % (title, msg)
   
    def buildReply(self, msgid, data):
        reply = PyDatagram()
        reply.addUint8(1)
        reply.addUint8(msgid)
        reply.addString(data)
        return reply
                      
            
class ServerProtocol(Protocol):
    def process(self, data):
        print "Got some data"
        it = PyDatagramIterator(data)
        msgid = it.getUint8()
        if msgid == 0:
            print "Got 0 key mssg"
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
        