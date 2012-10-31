import direct.directbase.DirectStart #starts Panda
from pandac.PandaModules import * #basic Panda modules
from direct.showbase.DirectObject import DirectObject #for event handling
from direct.actor.Actor import Actor #for animated models
from direct.interval.IntervalGlobal import * #for compound intervals
from direct.task import Task #for update functions
from direct.gui.OnscreenText import OnscreenText
from direct.gui.DirectGui import *
from direct.distributed.PyDatagram import PyDatagram 
from direct.distributed.PyDatagramIterator import PyDatagramIterator
import math, sys, random, socket
import engineStateManager


class Game(DirectObject):
    
    def __init__ (self):
        #Allows custom camera positioning
        base.disableMouse()
        self.reset_keymap()
        self.prevTime = 0
        self.playerID = -1
        self.stateManager = engineStateManager.EngineFSM(self)
        self.stateManager.request('Menu')
        self.accept("p",self.printText,[self.stateManager.state])
        
        self.load_assets()
        self.setup_collision()
        
        
        self.marco = False
        
    def load_assets(self):

    
        #Loads the plain, throws it into the scene graph and then scales it
        self.terrain = loader.loadModel("models/Playground")
        self.terrain.reparentTo(render)
        self.terrain.setScale(1)
        self.terrain.setPos(0,0,0)

        #startup connection
        self.server = Client(ClientProtocol(self))
        
     
        render.setAntialias(AntialiasAttrib.MMultisample)
        
        self.players = []
        
        for i in range (0,5):
            if i == 0:
                tempPlayer = loader.loadModel('models/Le-a_Default_Anim')
            elif i == 1:
                tempPlayer = loader.loadModel('models/Girl Lin Default')
            elif i == 2:
                tempPlayer = loader.loadModel('models/Gus_default_Anim')
            elif i == 3:
                tempPlayer = loader.loadModel('models/Tony_Default_Anim')
            elif i == 4:
                tempPlayer = loader.loadModel('models/Le-a_Default_Anim')
            else:
                tempPlayer = loader.loadModel('models/Le-a_Default_Anim')
            tempPlayer.reparentTo(render)
            tempPlayer.setScale(0.25)
            tempPlayer.setY(9999)
            tempPlayer.setName(str(i))
            self.players.append(tempPlayer)
        
        self.players[0].setPos(0,0,0)
        self.cameraPos = render.attachNewNode("cameraPos")
        self.cameraPos.setPos(0,20,5)
        camera.lookAt(render)
        
        #Loads the enemies
        '''
        self.obstacles = []
        for i in range(10):
            self.obstacles.append(0)
            self.obstacles[i] = loader.loadModel('models/proton')
            self.obstacles[i].reparentTo(render)
            self.obstacles[i].setScale(0.5)
            self.obstacles[i].setY(9999)
            self.obstacles[i].setName(str(i))
            
            #obstacle.reparentTo(render)
            #self.obstacles.append(obstacle)
        ''' 
        #Creates the lights in the world
        self.ambientLightSource = AmbientLight("ambientLight")
        self.ambientLightSource.setColor((0.3,0.2,0.4,1.0))
        render.setLight(render.attachNewNode(self.ambientLightSource))
        
        self.directionalLightSource = DirectionalLight("dirLight")
        self.directionalLightSource.setColor((0.6,0.4,0.5,1.0))
        render.setLight(render.attachNewNode(self.directionalLightSource))
        
    
    def setup_collision(self):
        #Starts by setting up Collision detection stuff
        base.cTrav = CollisionTraverser()
        self.pusher = CollisionHandlerPusher()
        self.pusher.setInPattern("%in")
        
        
        for player in self.players:
            cNode = CollisionNode(player.getName())
            cNode.addSolid(CollisionSphere((0,0,3),3))
            cNode.setFromCollideMask(0x1)
            
            cNodePath = player.attachNewNode(cNode)
        
            base.cTrav.addCollider(cNodePath,self.pusher)
            self.pusher.addCollider(cNodePath, player)
        
        #Sets up collision for the terrain
        cNode = CollisionNode("terrain")
        cNode.addSolid(CollisionPlane(Plane()))
        render.attachNewNode(cNode)
        self.terrain.node().setIntoCollideMask(0x1)
        
        cNode = CollisionNode("terrainleft")
        cNode.addSolid(CollisionPlane(Plane(Vec3(1,0,0),Point3(-30,0,0))))
        render.attachNewNode(cNode)
        
        cNode = CollisionNode("terrainright")
        cNode.addSolid(CollisionPlane(Plane(Vec3(-1,0,0),Point3(30,0,0))))
        render.attachNewNode(cNode)
        '''
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
        '''
        
    def toggle_headLights(self):
        if self.stateManager.state == 'Game':
            self.stateManager.request('Menu')
        else:
            self.stateManager.request('Game')
            
    def player_hit (self, cEntry):
        data = PyDatagram()
        data.addInt8(38)
        self.server.send(data)
        
    def move_player(self, task):
        dt = task.time - self.prevTime
        
        if self.keyMap['left']: 
            self.players[self.playerID].setH(self.players[self.playerID].getH() + dt*100)
        if self.keyMap['right']:
            self.players[self.playerID].setH(self.players[self.playerID].getH() - dt*100)
        if self.keyMap['forward']:
            dist = 1
            angle = deg2Rad(self.players[self.playerID].getH())
            dx = dist * math.sin(angle)
            dy = dist * -math.cos(angle)
            self.players[self.playerID].setPos(self.players[self.playerID].getX() + dx, self.players[self.playerID].getY() + dy, self.players[self.playerID].getZ())
        if self.keyMap['back']:
            dist = -1
            angle = deg2Rad(self.players[self.playerID].getH())
            dx = dist * math.sin(angle)
            dy = dist * -math.cos(angle)
            self.players[self.playerID].setPos(self.players[self.playerID].getX() + dx, self.players[self.playerID].getY() + dy, self.players[self.playerID].getZ())
            
        self.players[self.playerID].setZ(self.players[self.playerID].getZ()-0.1)
        
        return task.cont
        
    def move_camera(self,task):
        dt = task.time - self.prevTime
        
        #Sets the camera's position to the cameraPos (which was offset from self.player), and then makes the camera look at the player
        camera.setPos(self.cameraPos,0,0,0)
        camera.lookAt(self.players[self.playerID])
        
        camera.setP(camera.getP()+17)
        
        return task.cont
        
    def rotate_camera_around(self,task):
        self.cameraRotParent.setH(task.time*60) #this will rotate it 60 degrees around the point every second
        if self.playerID == -1:
            camera.lookAt(render)
            
        else:
            camera.lookAt(self.players[self.playerID])
            
        return task.cont
        
    def reparent_camera(self):
        
        self.cameraRotParent = render.attachNewNode("cameraRotNode")
        
        camera.wrtReparentTo(self.cameraRotParent) 
        camera.setPos(0,-30,15) # 10 = distance between cam and point 
        
    def update_prev_time(self,task):
        self.prevTime = task.time
        
        return task.cont
    
    def update_obstacles(self,task):
        '''dt = task.time - self.prevTime
        
        for obstacle in self.obstacles:
            if obstacle.getName()=="electron":
                obstacle.lookAt(self.player)
            if obstacle.getName()=="neutron":
                pass
        '''
        return task.cont
        
    def goto_state(self,toState):
        if self.engineState == 0:
            if toState == 1:
                self.stateManager.request('Game')
                
        if self.engineState == 1:
            if toState == 0:
                self.stateManager.request('Menu')
                
                
    def reset_keymap(self):
        self.keyMap = {"left":False, "right":False, "forward":False, "back":False}
            
    def setKey(self,key,value):
        self.keyMap[key] = value
        
    def printText(self,string):
        print string
    
    
    def connect_ip(self,ip):
        print 'IP = ' , ip
        try:
            socket.inet_aton(ip)
            print "Looks like a valid IP, let's connect!"
            return self.server.connect(ip, 9999, 3000)
            
        except socket.error:
            print "That doesn't look like a valid IP to me"
        
        return False
       
        
           
        
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
                #print "Sending a reply"
                self.writer.send(reply, data.getConnection())
            else:
                print "there wasn't a reply"
       
        return task.cont

     
class Client(NetCommon):

    def __init__(self, protocol):
        NetCommon.__init__(self, protocol)
    
    def connect(self, host, port, timeout):
        self.connection = self.manager.openTCPClientConnection(host, port, timeout)
        
        if self.connection:
            self.connection.setNoDelay(True)
            self.reader.addConnection(self.connection)
            print "Client: Connected to server."
            return True
        return False
            
    def send(self, datagram):
        if self.connection:
            self.writer.send(datagram, self.connection)
            print "sent data to server"
        else:
            print "failed to send data"
            

       
class ClientProtocol(Protocol):

    def __init__(self, game):
        self.game = game
        self.clientID = -1
    
    def process(self, data):
        it = PyDatagramIterator(data)
        mssgID = it.getUint8()
        if mssgID == 42:
        
            self.clientID = it.getInt8()
           
            self.game.playerID = self.clientID
            self.game.cameraPos = self.game.players[self.game.playerID].attachNewNode("cameraPos")
            self.game.players[0].setY(9999)
            self.game.players[self.game.playerID].setPos(0,0,0)
            self.game.cameraPos.setPos(0,40,15)
            print "My player ID is ", self.clientID
          
            
        elif mssgID == 13:
            tempID = it.getInt8()
            print "Server received ID is ", tempID , " locally stored ID ", self.clientID
            if tempID != self.clientID:
            
                '''
                self.game.players[tempID].setX(it.getFloat32())
                self.game.players[tempID].setY(it.getFloat32())
                self.game.players[tempID].setZ(it.getFloat32())
                self.game.players[tempID].setH(it.getFloat32())
                self.game.players[tempID].setP(it.getFloat32())
                self.game.players[tempID].setR(it.getFloat32())
                '''
                moveInterval = self.game.players[tempID].posInterval(0.25,(it.getFloat32(),it.getFloat32(),it.getFloat32()))
                hprInterval = self.game.players[tempID].hprInterval(0.25,(it.getFloat32(),it.getFloat32(),it.getFloat32()))
                
                moveInterval.start()
                hprInterval.start()
                
      
              #self.game.players[tempID].setPythonTag("velocity",it.getFloat32())
            
        elif mssgID == 38:
            print "Marco Won"
            self.game.stateManager.request("MarcoWins")
            
        elif mssgID == 39:
            print "Marco lost"
            winner = it.getInt8()
            
            
        elif mssgID == 101:
            scores = []
            for i in range(0,5):
                scores.append(it.getFloat32())
            self.game.stateManager.inflate(scores)
            
            
        '''
        vel = it.getFloat32()
        z = it.getFloat32()
        x = it.getFloat32()
        y = it.getFloat32()
        checksum = it.getFloat32()
        
        #print "velocity:" , vel ,
        #" Z position:" , z , " Checksum " , checksum
        
        newx = x
        #zdiff = z - self.smiley.getZ()
        #self.smiley.setPythonTag("velocity", vel + zdiff * 0.03)
        
        #self.smiley.setX(x)
        #self.smiley.setZ(z)
        #self.smiley.setY(y)
        '''

        data = PyDatagram()
        
        data.addUint8(13)
        data.addInt8(self.clientID)
        data.addFloat32(self.game.players[self.game.playerID].getX())
        data.addFloat32(self.game.players[self.game.playerID].getY())
        data.addFloat32(self.game.players[self.game.playerID].getZ())
        data.addFloat32(self.game.players[self.game.playerID].getH())
        data.addFloat32(self.game.players[self.game.playerID].getP())
        data.addFloat32(self.game.players[self.game.playerID].getR())
        
        if self.game.keyMap['forward'] and not self.game.keyMap['back']:
            data.addFloat32(1.0)
        elif not self.game.keyMap['forward'] and self.game.keyMap['back']:
            data.addFloat32(-1.0)
        else:
            data.addFloat32(0)
        
        #data.addString("w") #change this to key being pressed forward
        
        #print "in ClientProtocol.process()"
        #data.addString("OH HI MARTK!!")
        
        
        return data

 
 
if __name__ == '__main__': 
    engine = Game()
    run() 