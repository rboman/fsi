#!/usr/bin/env python
# -*- coding: latin-1; -*-
# dummy fsi program
# ~/dev/Offi/oo_metaB/bin/Metafor -nogui ./onemeta.py

import math
#from toolbox.utilities import 
#workdir = 'workspace/beam'

#def getMetafor(p={}):
#    import apps.ale.coining3D as m
#    return m.getMetafor(p)

#def main():
#    load(__name__)
#    setDir(workdir)
#    meta()

class MtfSolver:
    def __init__(self, bndno):
        #self.volno = volno
        self.bndno = bndno
        self.fnods = {}

    def prepro(self):
        import beam
        metafor = beam.getMetafor()

        groupset = metafor.getDomain().getGeometry().getGroupSet()
        gr = groupset(self.bndno)
        nbnods = gr.getNumberOfMeshPoints()
        
        # build a list (dict) of nodes
        for i in range(nbnods):
            node = gr.getMeshPoint(i)
            self.fnods[node] = (0.0, 0.0) # node => nodal force to be prescribed

    def dummyload(self, time):
        """
        calculates some dummy forces (as a function of time)
        these forces will be sent to the Metafor model
        """
        # calculate L (max length along x)
        xmin=1e10
        xmax=-1e10
        for node in self.fnods.iterkeys():
            px = node.getPos0().get1()
            if px<xmin: xmin=px
            if px>xmax: xmax=px
        print "(xmin,xmax)=(%f,%f)" % (xmin,xmax)
        L = xmax-xmin
        print "L=%f" % L
        
        # evaluates some function (fx,fy)_nod = f(x,time)     
        for node in self.fnods.iterkeys(): 
            px = node.getPos0().get1()
            fx = 0.0
            fy = time*math.sin(8*math.pi*px/L)
            self.fnods[node] = (fx,fy)

        # write these loads to a file
        f = open('forces.txt','w')
        for node in self.fnods.iterkeys():
            fx,fy = self.fnods[node]
            f.write("%d %20.15e %20.15e\n" % (node.getNo(), fx,fy))
        f.close()


    def run(self):
        import beam
        metafor = beam.getMetafor()


    
        return 0.0


if __name__ == "__main__":

    solid = MtfSolver(103)
    solid.prepro()
    solid.dummyload(0.01)
    solid.run()
    print solid.fnods
    
    
    

