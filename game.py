import direct.directbase.DirectStart #starts Panda
from pandac.PandaModules import * #basic Panda modules
from direct.showbase.DirectObject import DirectObject #for event handling
from direct.actor.Actor import Actor #for animated models
from direct.interval.IntervalGlobal import * #for compound intervals
from direct.task import Task #for update functions
from direct.gui.OnscreenText import OnscreenText
from direct.distributed.PyDatagram import PyDatagram 
from direct.distributed.PyDatagramIterator import PyDatagramIterator
import math, sys, random

class Game(DirectObject):
    
    def __init__ (self):
        #Allows custom camera positioning
        base.disableMouse()
        self.keyMap = {"left":False, "right":False, "forward":False, "back":False}
        self.prevTime = 0
        
        taskMgr.add(self.move_player, "moveTask",priority=1)
        taskMgr.add(self.move_camera, "cameraTask",priority=5)
        taskMgr.add(self.update_prev_time, "timeTask",priority=6)
        taskMgr.add(self.update_obstacles, "obstacleUpdateTask",priority=2)
        taskMgr.add(self.update_terrain, "terrainUpdateTask", priority=3)
        taskMgr.add(listenerPolling, "connectionOpener", priority=4)
        taskMgr.add(readerPolling, "connectionOpener", priority=4)
        
        self.accept("escape", sys.exit)
        self.accept("arrow_up", self.setKey, ["forward", True])
        self.accept("arrow_left", self.setKey, ["left", True])
        self.accept("arrow_right", self.setKey, ["right", True])
        self.accept("arrow_down", self.setKey, ["back", True])
        self.accept("arrow_up-up", self.setKey, ["forward", False])
        self.accept("arrow_left-up", self.setKey, ["left", False])
        self.accept("arrow_right-up", self.setKey, ["right", False])
        self.accept("arrow_down-up", self.setKey, ["back", False])
        self.accept("h",self.toggle_headLights,[])
        self.accept("proton-electron",self.player_hit,[])
        
        self.load_assets()
        self.setup_collision()
        self.setupNetworking()
        
        self.headlightson = True
        self.playerHits = 0
        
        self.hpPrompt = OnscreenText(text = 'HitPoints:', pos = (-0.55, -0.2), scale = 0.07)
        self.hpText = OnscreenText(text = str(10-self.playerHits), pos = (-0.35, -0.2), scale = 0.07)
        
    def setup_networking(self)
        #Basic networking manager
        self.cManager = QueuedConnectionManager()
         
        #Listens for new connections and queue's them 
        self.cListener = QueuedConnectionListener(self.cManager, 0) 

        #Reads data send to the server 
        self.cReader = QueuedConnectionReader(self.cManager, 0) 

        #Writes / sends data to the client 
        self.cWriter = ConnectionWriter(self.cManager,0)
         
         self.connections = []
        
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
            if random.randint(0,1) == 1:
                cNode = CollisionNode("electron")
            else:
                cNode = CollisionNode("neutron")
                
            cNode.addSolid(CollisionSphere((0,0,3),3))
            obstacle.attachNewNode(cNode)
            cNodePath = obstacle.attachNewNode(cNode)
            
            base.cTrav.addCollider(cNodePath,self.pusher)
            self.pusher.addCollider(cNodePath, obstacle)
        
        
    def toggle_headLights(self):
        if self.headlightson:
            render.clearLight(self.headlight)
            self.headlightson = False
        else:
            render.setLight(self.headlight)
            self.headlightson = True
            
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
        
        return task.cont
        
         
    def listenerPolling(task):
        if self.cListener.newConnectionAvailable():
            rendezvous = PointerToConnection()
            netAddress = NetAddress()
            newConnection = PointerToConnection()
     
        if self.cListener.getNewConnection(rendezvous,netAddress,newConnection):
            newConnection = newConnection.p()
            activeConnections.append(newConnection) # Remember connection
            self.cReader.addConnection(newConnection)     # Begin reading connection
        return task.cont
      
    def readerPolling(task):
        if self.cReader.dataAvailable():
            data = NetDatagram()
            if self.cReader.getData(data):
                self.processNetworkingData(data)
        return task.cont
        
    def processNetworkingData(data):
        print data
        
    def setKey(self,key,value):
        self.keyMap[key] = value
        

engine = Game()
run()