from pandac.PandaModules import * #basic Panda modules
from direct.showbase.DirectObject import DirectObject #for event handling
from direct.actor.Actor import Actor #for animated models
from direct.interval.IntervalGlobal import * #for compound intervals
from direct.task import Task #for update functions
from direct.gui.OnscreenText import OnscreenText
from direct.gui.DirectGui import *
from direct.distributed.PyDatagram import PyDatagram 
from direct.distributed.PyDatagramIterator import PyDatagramIterator
from direct.fsm.FSM import FSM
import math, sys, random, socket

class EngineFSM(FSM):
    def __init__(self,engine):
        FSM.__init__(self, 'EngineFSM')
        self.engine=engine
    def enterGame(self):
        taskMgr.add(self.engine.move_player, "moveTask",priority=1)
        taskMgr.add(self.engine.move_camera, "cameraTask",priority=5)
        taskMgr.add(self.engine.update_prev_time, "timeTask",priority=6)
        taskMgr.add(self.engine.update_obstacles, "obstacleUpdateTask",priority=2)
        taskMgr.add(self.engine.update_terrain, "terrainUpdateTask", priority=3)
        
        self.engine.accept("escape", sys.exit)
        self.engine.accept("arrow_up", self.engine.setKey, ["forward", True])
        self.engine.accept("arrow_left", self.engine.setKey, ["left", True])
        self.engine.accept("arrow_right", self.engine.setKey, ["right", True])
        self.engine.accept("arrow_down", self.engine.setKey, ["back", True])
        self.engine.accept("arrow_up-up", self.engine.setKey, ["forward", False])
        self.engine.accept("arrow_left-up", self.engine.setKey, ["left", False])
        self.engine.accept("arrow_right-up", self.engine.setKey, ["right", False])
        self.engine.accept("arrow_down-up", self.engine.setKey, ["back", False])
        self.engine.accept("h",self.engine.toggle_headLights,[])
        self.engine.accept("proton-electron",self.engine.player_hit,[])
        
        self.engine.reset_keymap()
        
    def exitGame(self):
        taskMgr.remove("moveTask")
        taskMgr.remove("cameraTask")
        taskMgr.remove("timeTask")
        taskMgr.remove("obstacleUpdateTask")
        taskMgr.remove("terrainUpdateTask")
        
        self.engine.ignore("escape")
        self.engine.ignore("arrow_up")
        self.engine.ignore("arrow_left")
        self.engine.ignore("arrow_right")
        self.engine.ignore("arrow_down")
        self.engine.ignore("arrow_up-up")
        self.engine.ignore("arrow_left-up")
        self.engine.ignore("arrow_right-up")
        self.engine.ignore("arrow_down-up")
        self.engine.ignore("h")
        self.engine.ignore("proton-electron")
        
    def enterMenu(self):
        self.engine.accept("escape", sys.exit)
        self.engine.accept("h",self.engine.toggle_headLights,[])
        
        taskMgr.add(self.engine.rotate_camera_around, "rotateCameraTask", priority=1)
        
        self.engine.reparent_camera()
        
        self.gameButton = DirectButton(text=("Go to Game", "Into the game!","You sure?", "disabled"),text_scale=(0.2,0.2),text_pos=(0,0.5),relief=3,borderWidth=(0.05,0.05),command=self.request,extraArgs=['Game'])
        
    def exitMenu(self):
        self.engine.ignore("escape")
        self.engine.ignore("h")
        self.gameButton.destroy()