#!/usr/bin/env python
# -*- coding: latin-1; -*-
# ~/dev/Metafor/oo_metaB/bin/Metafor -nogui ./fsi.py

import math
from utilities import *
from wrap import *


# ------------------------------------------------------------------------------
# custom toolbox.utilities
# ------------------------------------------------------------------------------



# ------------------------------------------------------------------------------

class NLoad:
    """
    Nodal load
    """
    def __init__(self, val):
        self.val = val
    def __call__(self, time):
        return self.val
   
# ------------------------------------------------------------------------------
               
class MtfSolver:
    def __init__(self, testname, bndno):
        self.testname = testname  # string (name of the module of the solid model)
        self.bndno = bndno        # phygroup# of the f/s interface
        
        # internal vars
        self.fnods = {}           # dict of interface nodes / prescribed forces
        self.t1      = 0.0        # last reference time        
        self.t2      = 0.0        # last calculated time
        self.metafor = None       # link to Metafor objet

    def run(self, t1, t2):
        """
        calculates one increment from t1 to t2.
        """
        if(not self.metafor):
            self.__firstrun(t1, t2)
        else:
            self.__nextrun(t1, t2)
        self.t1 = t1
        self.t2 = t2

    def __firstrun(self, t1, t2):
        """
        performs a first run of metafor with all the required preprocessing.
        """
        # loads the python module
        #load(self.testname)         # use toolbox.utilities
        exec("import %s" % self.testname)
        exec("module = %s" % self.testname)

        # create an instance of Metafor
        p = {}                       # parameters (todo)
        #self.metafor = instance(p)  # use toolbox.utilities
        self.metafor = module.getMetafor(p)
        
        # retrieve the f/s boundary and the related nodes
        groupset = self.metafor.getDomain().getGeometry().getGroupSet()
        gr = groupset(self.bndno)
        nbnods = gr.getNumberOfMeshPoints()
        
        # builds a list (dict) of interface nodes
        # and creates the nodal prescribed loads
        loadingset = self.metafor.getDomain().getLoadingSet()
        for i in range(nbnods):
            node = gr.getMeshPoint(i)
            no = node.getNo()
            fx = NLoad(0.0)
            fy = NLoad(0.0)
            self.fnods[no] = (node, fx, fy)
            fctx = PythonOneParameterFunction(fx)
            fcty = PythonOneParameterFunction(fy)
            loadingset.define(node, Field1D(TX,GF1), 1.0, fctx) 
            loadingset.define(node, Field1D(TY,GF1), 1.0, fcty)       

        # this is the first run - initialize the timestep manager of metafor
        tsm = self.metafor.getTimeStepManager()
        dt    = t2-t1  # time-step size
        dt0   = dt     # initial time step
        dtmax = dt     # maximum size of the time step
        tsm.setInitialTime(t1, dt0)
        tsm.setNextTime(t2, 1, dtmax)
        # launches metafor from t1 to t2
        #meta()                  # use toolbox.utilities
        log = wrap.LogFile("resFile.txt")
        self.metafor.getTimeIntegration().integration()
        # at this stage, 2 archive files have been created in the workspace

    def __nextrun(self, t1, t2):
        """
        performs one time increment (from t1 to t2) of the solid model.
        this increment is a full metafor run and it may require more than 1 time step.
        """
        if self.t1==t1:
            # rerun from t1
            if self.t2!=t2:
                raise Exception("bad t2 (%f!=%f)" % (t2, self.t2)) 
            
            loader = fac.FacManager(self.metafor)
            nt = loader.lookForFile(0)
            loader.eraseAllFrom(nt)
            self.metafor.getTimeIntegration().restart(nt)
        else:
            # new time step
            tsm = self.metafor.getTimeStepManager()
            dt=t2-t1
            dtmax=dt
            tsm.setNextTime(t2, 1, dtmax)            
            
            loader = fac.FacManager(self.metafor)
            nt1 = loader.lookForFile(0)
            nt2 = loader.lookForFile(1)
            loader.erase(nt1) # delete first fac
            self.metafor.getTimeIntegration().restart(nt2) 

    def fakefluidsolver(self, time):
        """
        calculate some dummy loads as a function of timestep.
        these loads should be replaced by the fluid solver in practise.
        for each node, the fsi solver may call the "solid.applyload" function.
        """
        # calculate L (max length along x)
        xmin=1e10
        xmax=-1e10
        for no in self.fnods.iterkeys():
            node,fx,fy = self.fnods[no]
            px = node.getPos0().get1()
            if px<xmin: xmin=px
            if px>xmax: xmax=px
        #print "(xmin,xmax)=(%f,%f)" % (xmin,xmax)
        L = xmax-xmin
        #print "L=%f" % L
    
        # loop over node#
        for no in self.fnods.iterkeys():
            node,fx,fy = self.fnods[no]  # retreive data of node #no
            px = node.getPos0().get1()     # x coordinate of the node       
            valx = 0.0 
            valy = -3e-4*time*math.sin(8*math.pi*px/L) # dummy fct
            self.applyload(no, valx, valy)

    def applyload(self, no, valx, valy):
        """
        prescribes given nodal forces (valx,valy) to node #no
        """
        node,fx,fy = self.fnods[no]
        fx.val = valx
        fy.val = valy

    def getdefo(self):
        """
        returns a dict containing all the updated positions of the interface nodes.
        out[node_no] = (pos_x, pos_y)
        """
        out = {}
        for no in self.fnods.iterkeys():
            node,fx,fy = self.fnods[no]
            px0 = node.getPos0().get1()   # initial position x     
            py0 = node.getPos0().get2()   # initial position y 
            px = node.getPos(Configuration().currentConf).get1() # current x          
            py = node.getPos(Configuration().currentConf).get2() # current y                   
            vx = node.getValue(Field1D(TX,GV)) # current vx          
            vy = node.getValue(Field1D(TY,GV)) # current vy                    
            out[no] = (px,py)
        return out
         

def main():
    solid = MtfSolver('beam', 103)
    
    # --------------------------
    # fake FSI solver
    # --------------------------
    
    t1 = 0.0  # initial time
    dt = 0.5  # time step size
    
    # we want 5 time steps
    for j in range(5):
    
        # each time step is arbitrarily calculated twice (for testing purpose)
        for i in range(2):
            
            t2=t1+dt  # time to be calculated
            
            solid.fakefluidsolver(t2)  # creates some dummy loads for time=t2
            # must be replaced by a loop over the nodes of the interface and
            # several calls to "solid.applyload(node_no, force_x, force_y)"
            
            # runs solid solver
            print '='*80
            print "running from %f to %f: try #%d" % (t1,t2,i+1)
            print '='*80
            solid.run(t1,t2)
            
            # gets the deformed interface
            out = solid.getdefo()
            print out   # <= todo: give 'out' to the fluid solver and update the fluid mesh

        t1=t2 # fsi loop has converged - time t2 is accepted
    
    # end.
    
    
    
if __name__ == "__main__":
    main()
    
    
    
    


