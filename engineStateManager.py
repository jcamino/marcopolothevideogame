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
        self.engine.accept("0",self.engine.player_hit,[])
        
        self.engine.reset_keymap()
        
        self.winnerLabels = []
        for i in range(0,5):
            self.winnerLabels.append(DirectLabel(text=str(i),text_scale=(0.05,0.05),text_pos=(-0.9,1-0.2*i),relief=None))
        
       
    def exitGame(self):
        taskMgr.remove("moveTask")
        taskMgr.remove("cameraTask")
        taskMgr.remove("timeTask")
        taskMgr.remove("obstacleUpdateTask")
        
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
        
        self.engine.reset_keymap()
        
    def enterMenu(self):
        self.engine.accept("escape", sys.exit)
        
        taskMgr.add(self.engine.rotate_camera_around, "rotateCameraTask", priority=1)
        
        self.engine.reparent_camera()
        
        self.gameButton = DirectButton(text=("Go to Game", "Into the game!","You sure?", "disabled"),text_scale=(0.2,0.2),text_pos=(0,0.5),relief=3,borderWidth=(0.05,0.05),command=self.request,extraArgs=['Game'])
        
        
        self.multiPlayerButton = DirectButton(text=("Server Settings", "Server Settings","Server Settings", "disabled"),text_scale=(0.2,0.2),text_pos=(0,-0.5),relief=3,borderWidth=(0.05,0.05),command=self.request,extraArgs=['ServerSettings'])

    def exitMenu(self):
        self.engine.ignore("escape")
        self.gameButton.destroy()
        self.multiPlayerButton.destroy()
        taskMgr.remove('rotateCameraTask')
        
        
    def enterServerSettings(self):
    
        self.engine.accept("escape", sys.exit)
        taskMgr.add(self.engine.rotate_camera_around, "rotateCameraTask", priority=1)
        
        self.engine.reparent_camera()
                
        def clearText():
            self.ipEntry.enterText('')
        self.ipEntry = DirectEntry(initialText='Enter IP Address of Server', numLines=1,text_scale = (0.2,0.2),text_pos=(-1.0,-0.5),focus=0,focusInCommand=clearText)
        

        self.gameButton = DirectButton(text=("Go to Game", "Into the game!","You sure?", "disabled"),text_scale=(0.2,0.2),text_pos=(0,0.5),relief=3,borderWidth=(0.05,0.05),command=self.request,extraArgs=['Game'])
        
   
    def exitServerSettings(self):
        if self.newState == 'Game':
            if not self.engine.connect_ip(self.ipEntry.get()):
                self.demand('ServerSettings')
        
        self.engine.ignore("escape")
        taskMgr.remove('rotateCameraTask')
        self.gameButton.destroy()
        self.ipEntry.destroy()
        
    def enterMarcoWins(self):
        self.menuButton = DirectButton(text=("Go to Menu", "Into the menu!","You sure?", "disabled"),text_scale=(0.2,0.2),text_pos=(0,0.5),relief=3,borderWidth=(0.05,0.05),command=self.request,extraArgs=['Game'])
        
        self.winnerLabel = DirectLabel(text="Marco Won!",text_scale=(0.2,0.2),text_pos=(0,0.5),relief=3,borderWidth=(0.1,0.1))
        
        self.engine.accept("escape", sys.exit)
        taskMgr.add(self.engine.rotate_camera_around, "rotateCameraTask", priority=1)
        
        self.engine.reparent_camera()
        
    def exitMarcoWins(self):
        self.menuButton.destroy()
        self.winnerLabel.destroy()
        self.engine.ignore("escape")
        taskMgr.remove('rotateCameraTask')
        
    def inflate(self,scores):
        for i in range(0,5):
            self.winnerLabels[i]['text_scale'] =(scores[i],scores[i])
        