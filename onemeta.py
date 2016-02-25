#!/usr/bin/env python
# -*- coding: latin-1; -*-

from toolbox.utilities import *
workdir = 'workspace/beam'

def getMetafor(p={}):
    import beam
    return beam.getMetafor(p)

def main():
    load(__name__)
    setDir(workdir)
    #p = {'tend' : 0.04 }
    p = {}
    metafor = instance(p)
    
    tsm = metafor.getTimeStepManager()
    tsm.setNextTime(0.1, 1, 0.01)
    meta()
    
    
    
    tsm.setNextTime(0.2, 1, 0.01)
    
    for i in range(5):
        print '='*80
        print "restarting"
        print '='*80
        loader = fac.FacManager(metafor)
        nt = loader.lookForFile(1)
        #loader.eraseAllFrom(nt)
        #restart(nt)    
        metafor.getTimeIntegration().restart(nt)
        #meta()

if __name__ == "__main__":
    
    main()


