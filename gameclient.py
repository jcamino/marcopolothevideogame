from direct.showbase.ShowBase import ShowBase
from panda3d.core import *

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