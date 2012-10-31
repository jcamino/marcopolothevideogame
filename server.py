from direct.showbase.ShowBase import ShowBase
from panda3d.core import *
from direct.distributed.PyDatagram import PyDatagram
from direct.distributed.PyDatagramIterator import PyDatagramIterator
from time import time
import random

direction = {1: -1, 2: -1, 3:-1, 4:-1, 5:-1}

class Application(ShowBase):
    def __init__(self):
    
        
        
        ShowBase.__init__(self)
        
        server = Server(Protocol(self), 9999,self)
        
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
        #taskMgr.add(self.updateSmiley, "updateSmiley")
        taskMgr.doMethodLater(0.25, self.syncSmiley, "syncSmiley")
        
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
                for client in range(1,len(direction)):
                    if direction[client] == -1:
                        direction[client] = 0
                        print "Client ID ",client
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
            
            #sync.addFloat32(float(self.Server.players[tempID].getTag("velocity")))
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
        print "Got some data"
        it = PyDatagramIterator(data)
        msgid = it.getUint8()
        
        if msgid == 1:
            direction['1']=it.getString()
            #self.printMessage("Server received:", direction['1'])
        
        #standard update
        if msgid == 13:
            tempID = it.getInt8()
            print "updating position for player ", tempID
            
            self.Application.players[tempID].setX(it.getFloat32())
            self.Application.players[tempID].setY(it.getFloat32())
            self.Application.players[tempID].setZ(it.getFloat32())
            self.Application.players[tempID].setH(it.getFloat32())
            self.Application.players[tempID].setP(it.getFloat32())
            self.Application.players[tempID].setR(it.getFloat32())
            
            self.Application.players[tempID].setPythonTag("velocity",it.getFloat32())
            #self.printMessage("Server received:", direction[2])        
        
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
        
        
        #CODE FROM GAME.PY
        
        '''
    def __init__ (self):
        #Allows custom camera positioning
        base.disableMouse()
        self.reset_keymap()
        self.prevTime = 0
        
        self.stateManager = engineStateManager.EngineFSM(self)
        self.stateManager.request('Game')
        self.accept("p",self.printText,[self.stateManager.state])
        
        self.load_assets()
        self.setup_collision()
        
        self.headlightson = True
        self.playerHits = 0
        
        self.hpPrompt = OnscreenText(text = 'HitPoints:', pos = (-0.55, -0.2), scale = 0.07)
        self.hpText = OnscreenText(text = str(10-self.playerHits), pos = (-0.35, -0.2), scale = 0.07)
        
    def load_assets(self):
    
        #Loads the plain, throws it into the scene graph and then scales it
        self.terrain = loader.loadModel("models/plain")
        self.terrain.reparentTo(render)
        self.terrain.setScale(50)
        self.terrain.setPos(0,0,0)
        
        #Adds the edges of the collider
        self.terrain = loader.loadModel("models/plain")
        self.terrain.reparentTo(render)
        self.terrain.setScale(50)
        self.terrain.setPos(-22,0,0)
        self.terrain.setR(90)
        
        self.terrain = loader.loadModel("models/plain")
        self.terrain.reparentTo(render)
        self.terrain.setScale(50)
        self.terrain.setPos(22,0,0)
        self.terrain.setR(-90)
        
        self.terrain = loader.loadModel("models/plain")
        self.terrain.reparentTo(render)
        self.terrain.setScale(50)
        self.terrain.setPos(0,0,22)
        self.terrain.setR(180)
        
        #Loads the player model, throws it into the scene graph and scales/positions it
        self.player = loader.loadModel("models/proton")
        self.player.reparentTo(render)
        self.player.setScale(.5)
        self.player.setPos(0,0,0)
        self.player.setH(180)
        
        self.cameraPos = self.player.attachNewNode("cameraPos")
        self.cameraPos.setPos(0,20,5)
        
        render.setAntialias(AntialiasAttrib.MMultisample)
        
        #Loads the enemies
        self.obstacles = []
        for i in range(10):
            if random.randint(0,1) == 1:
                obstacle = loader.loadModel("models/electron")
                obstacle.setScale(.5)
                obstacle.setPos(random.randint(-20, 20), random.randint(80, 200), 0)
                obstacle.setName("electron")
            else:
                obstacle = loader.loadModel("models/Neutron")
                obstacle.setScale(.5)
                obstacle.setPos(random.randint(-20, 20), random.randint(80, 200), 2)
                obstacle.setName("neutron")
            
            obstacle.reparentTo(render)
            self.obstacles.append(obstacle)
            
        #Creates the lights in the world
        self.ambientLightSource = AmbientLight("ambientLight")
        self.ambientLightSource.setColor((0.3,0.2,0.4,1.0))
        render.setLight(render.attachNewNode(self.ambientLightSource))
        
        self.directionalLightSource = DirectionalLight("dirLight")
        self.directionalLightSource.setColor((0.6,0.4,0.5,1.0))
        render.setLight(render.attachNewNode(self.directionalLightSource))
        
        self.headlight = self.player.attachNewNode(Spotlight('headlight'))
        self.headlight.node().setColor(Vec4(0.9,0.9,0.9,1))
        self.headlight.setH(180)
        render.setLight(self.headlight)
        
    def setup_collision(self):
        #Starts by setting up Collision detection stuff
        base.cTrav = CollisionTraverser()
        self.pusher = CollisionHandlerPusher()
        self.pusher.setInPattern("%fn-%in")
    
        #Sets up collision for the player
        cNode = CollisionNode("proton")
        cNode.addSolid(CollisionSphere((0,0,3),3))
        cNode.setIntoCollideMask(BitMask32.allOff()) #turns off "into" collision on player
        
        
        cNodePath = self.player.attachNewNode(cNode)
        
        base.cTrav.addCollider(cNodePath,self.pusher)
        self.pusher.addCollider(cNodePath, self.player)
        
        #Sets up collision for the terrain
        cNode = CollisionNode("terrain")
        cNode.addSolid(CollisionPlane(Plane()))
        render.attachNewNode(cNode)
        
        cNode = CollisionNode("terrainleft")
        cNode.addSolid(CollisionPlane(Plane(Vec3(1,0,0),Point3(-22,0,0))))
        render.attachNewNode(cNode)
        
        cNode = CollisionNode("terrainright")
        cNode.addSolid(CollisionPlane(Plane(Vec3(-1,0,0),Point3(22,0,0))))
        render.attachNewNode(cNode)
        
        for obstacle in self.obstacles:
            if obstacle.getName() == 'electron':
                cNode = CollisionNode("electron")
            else:
                cNode = CollisionNode("neutron")
                
            cNode.addSolid(CollisionSphere((0,0,3),3))
            obstacle.attachNewNode(cNode)
            cNodePath = obstacle.attachNewNode(cNode)
            
            base.cTrav.addCollider(cNodePath,self.pusher)
            self.pusher.addCollider(cNodePath, obstacle)
        
        
    def toggle_headLights(self):
        if self.stateManager.state == 'Game':
            self.stateManager.request('Menu')
        else:
            self.stateManager.request('Game')
            
    def player_hit (self, cEntry):
        self.playerHits += 1
        self.obstacles.remove(cEntry.getIntoNodePath().getParent())
        cEntry.getIntoNodePath().getParent().remove()
        
        self.hpText.destroy()
        self.hpText = OnscreenText(text = str(10-self.playerHits), pos = (-0.35, -0.2), scale = 0.07)
        
        if self.playerHits >= 10:
            sys.exit()
        elif self.playerHits >8:
            self.imminentDeathText = OnscreenText(text = "ABOUT TO DIE!!", pos = (-0.35, -0.4), scale = 0.07)
        
    def move_player(self, task):
        dt = task.time - self.prevTime
        
        if self.keyMap['left']: 
            self.player.setH(self.player.getH() + dt*100)
        if self.keyMap['right']:
            self.player.setH(self.player.getH() - dt*100)
        if self.keyMap['forward']:
            dist = 1
            angle = deg2Rad(self.player.getH())
            dx = dist * math.sin(angle)
            dy = dist * -math.cos(angle)
            self.player.setPos(self.player.getX() + dx, self.player.getY() + dy, self.player.getZ())
        if self.keyMap['back']:
            dist = -1
            angle = deg2Rad(self.player.getH())
            dx = dist * math.sin(angle)
            dy = dist * -math.cos(angle)
            self.player.setPos(self.player.getX() + dx, self.player.getY() + dy, self.player.getZ())
            
        self.player.setZ(self.player.getZ()-0.1)
        
        return task.cont
        
    def move_camera(self,task):
        dt = task.time - self.prevTime
        
        #Sets the camera's position to the cameraPos (which was offset from self.player), and then makes the camera look at the player
        camera.setPos(self.cameraPos,0,0,0)
        camera.lookAt(self.player)
        
        return task.cont
        
    def update_prev_time(self,task):
        self.prevTime = task.time
        
        return task.cont
    
    def update_obstacles(self,task):
        dt = task.time - self.prevTime
        
        for obstacle in self.obstacles:
            if obstacle.getName()=="electron":
                obstacle.lookAt(self.player)
            if obstacle.getName()=="neutron":
                pass
        
        return task.cont
        
    def update_terrain (self, task):
        dt = task.time - self.prevTime
        
        self.terrain.setY(((self.terrain.getY()-0.5))%100)
        
        return task.cont'''