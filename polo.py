import direct.directbase.DirectStart #starts Panda
from pandac.PandaModules import * #basic Panda modules
from direct.showbase.DirectObject import DirectObject #for event handling
from direct.actor.Actor import Actor #for animated models
from direct.interval.IntervalGlobal import * #for compound intervals
from direct.task import Task #for update functions
import math, sys, random

class World(DirectObject): #necessary to accept events
    def __init__(self):
        #turn off default mouse control
        #otherwise we can't position the camera
        base.disableMouse()
        camera.setPosHpr(0, -15, 7, 0, -15, 0)
        self.keyMap = {"left":0, "right":0, "forward":0}
        self.prevTime = 0
        taskMgr.add(self.move, "moveTask")
        self.loadModels()
        self.setupLights()
        self.setupCollisions()
        #self.pandaWalk = self.panda.posInterval(1, (0, -5, 0))
        self.accept("escape", sys.exit) #message name, function to call, (optional) list of arguments to that function
        #self.accept("arrow_up", self.walk)
        #other useful interval methods:
        # loop, pause, resume, finish
        # start can optionally take arguments: starttime, endtime, playrate
        
        #for fixed interval movement
        #self.accept("arrow_left", self.turn, [-1]) #yes, you have to use a list, event if the function only takes one argument
        #self.accept("arrow_right", self.turn, [1])
        
        #for "continuous" control
        self.accept("arrow_up", self.setKey, ["forward", 1])
        self.accept("arrow_left", self.setKey, ["left", 1])
        self.accept("arrow_right", self.setKey, ["right", 1])
        self.accept("arrow_up-up", self.setKey, ["forward", 0])
        self.accept("arrow_left-up", self.setKey, ["left", 0])
        self.accept("arrow_right-up", self.setKey, ["right", 0])
        self.accept("ate-smiley", self.eat)
    
    def setKey(self, key, value):
        self.keyMap[key] = value
        
    def loadModels(self):
        """loads initial models into the world"""
        self.env = loader.loadModel("environment")
        self.env.reparentTo(render)
        self.env.setScale(0.25)
        self.env.setPos(-8, 42, 0)
        self.panda = loader.loadModel("panda-model")
        self.panda.reparentTo(render)
        self.panda.setScale(.005)
        self.panda.setH(180)
        self.targets = []
        for i in range(10):
            target = loader.loadModel("smiley")
            target.setScale(.5)
            target.setPos(random.uniform(-20, 20), random.uniform(-20, 20), 2)
            target.reparentTo(render)
            self.targets.append(target)
            
        
    def setupLights(self):
        """loads initial lighting"""
        self.ambientLight = AmbientLight("ambientLight")
        #for setting colors, alpha is largely irrelevant
        self.ambientLight.setColor((.25, .25, .25, 1.0))
        #create a NodePath, and attach it directly into the scene
        self.ambientLightNP = render.attachNewNode(self.ambientLight)
        #the node that calls setLight is what's illuminated by the given light
        #you can use clearLight() to turn it off
        render.setLight(self.ambientLightNP)
        
        self.dirLight = DirectionalLight("dirLight")
        self.dirLight.setColor((.6, .6, .6, 1))
        self.dirLightNP = render.attachNewNode(self.dirLight)
        self.dirLightNP.setHpr(0, -25, 0)
        render.setLight(self.dirLightNP)
        
    # def walk(self):
    #     dist = 5
    #     dx = dist * math.sin(deg2Rad(self.panda.getH()))
    #     dy = dist * -math.cos(deg2Rad(self.panda.getH()))
    #     pandaWalk = self.panda.posInterval(1, (self.panda.getX() + dx, self.panda.getY() + dy, 0))
    #     pandaWalk.start()
    #     
    # def turn(self, direction):
    #     """turn the panda"""
    #     pandaTurn = self.panda.hprInterval(.2, (self.panda.getH() - (10*direction), 0 ,0))
    #     pandaTurn.start()
    
    def move(self, task):
        """compound interval for walking"""
        dt = task.time - self.prevTime
        #stuff and things
        camera.lookAt(self.panda)
        if self.keyMap["left"] == 1:
            self.panda.setH(self.panda.getH() + dt*100)
        if self.keyMap["right"] == 1:
            self.panda.setH(self.panda.getH() - dt*100)
        if self.keyMap["forward"] == 1:
            dist = .1
            angle = deg2Rad(self.panda.getH())
            dx = dist * math.sin(angle)
            dy = dist * -math.cos(angle)
            self.panda.setPos(self.panda.getX() + dx, self.panda.getY() + dy, 0)
        
        self.prevTime = task.time
        return Task.cont
        
    def setupCollisions(self):
        #make a collision traverser, set it to default
        base.cTrav = CollisionTraverser()
        self.cHandler = CollisionHandlerEvent()
        #set the pattern for the event sent on collision
        # "%in" is substituted with the name of the into object
        self.cHandler.setInPattern("ate-%in")
        
        cSphere = CollisionSphere((0,0,0), 500) #panda is scaled way down!
        cNode = CollisionNode("panda")
        cNode.addSolid(cSphere)
        #panda is *only* a from object
        cNode.setIntoCollideMask(BitMask32.allOff())
        cNodePath = self.panda.attachNewNode(cNode)
        #cNodePath.show()
        base.cTrav.addCollider(cNodePath, self.cHandler)
        
        for target in self.targets:
            cSphere = CollisionSphere((0,0,0), 2)
            cNode = CollisionNode("smiley")
            cNode.addSolid(cSphere)
            cNodePath = target.attachNewNode(cNode)
            #cNodePath.show()
        
    def eat(self, cEntry):
        self.targets.remove(cEntry.getIntoNodePath().getParent())
        cEntry.getIntoNodePath().getParent().remove()
        
w = World()
run()