class Entity(Object):
    def __init__ (self,node,engine):
        self.node = node
        self.engine = engine
        self.velocity = Vec3(0.0,0.0,0.0)
        
    def update(self, deltaT):
        self.node.setPos(self.node.getPos()+self.velocity)