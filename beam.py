# -*- coding: latin-1; -*-
# bends a simple beam from a gmsh file

from wrap import *

metafor = None

def params(q={}):
    """ default model parameters
    """
    p={}
    p['tolNR']      = 1.0e-7        # Newton-Raphson tolerance
    p['tend']       = 2.            # final time
    p['dtmax']      = 0.005          # max time step
    
    # BC type
    #p['bctype']     = 'pressure'     # uniform pressure
    #p['bctype']     = 'deadload'     # uniform nodal load
    #p['bctype']     = 'pydeadload1'  # uniform nodal load (python)  
    p['bctype']     = 'pydeadloads'  # variable loads
    #p['bctype']     = 'slave'     # variable loads (mpi)
                                       
    p.update(q)
    return p

def getMetafor(p={}):
    global metafor
    if metafor: return metafor
    metafor = Metafor()

    p = params(p)

    domain = metafor.getDomain()
    geometry = domain.getGeometry()
    geometry.setDimPlaneStrain(1.0)

    # import .geo
    from toolbox.gmsh import GmshImport
    f = os.path.join(os.path.dirname(__file__), "beam.geo")
    importer = GmshImport(f, domain)
    importer.execute()

    groupset = domain.getGeometry().getGroupSet()    

    # solid elements / material
    interactionset = domain.getInteractionSet()

    app1 = FieldApplicator(1)
    app1.push( groupset(100) )  # physical group 100
    interactionset.add( app1 )

    materset = domain.getMaterialSet()
    materset.define( 1, ElastHypoMaterial )
    mater1 = materset(1)
    mater1.put(MASS_DENSITY,    100.0)  # [kg/m³]
    mater1.put(ELASTIC_MODULUS, 2.5e5)  # [Pa]
    mater1.put(POISSON_RATIO,   0.35)   # [-]

    prp = ElementProperties(Volume2DElement)
    app1.addProperty(prp)
    prp.put (MATERIAL, 1)
    prp.put(CAUCHYMECHVOLINTMETH,VES_CMVIM_STD)
    
    # boundary conditions
    loadingset = domain.getLoadingSet()

    #Physical Line(101) - clamped side of the beam
    loadingset.define(groupset(101), Field1D(TX,RE))
    loadingset.define(groupset(101), Field1D(TY,RE))
    
    #Physical Line(102) - free surface of the beam
    
    #Physical Line(103) - upper surface of the beam (for tests only)

    gr = groupset(103)

    # calculate xmin-xmax
    xmin=1e10
    xmax=-1e10
    nbnods=gr.getNumberOfMeshPoints()
    for i in range(nbnods):
        node = gr.getMeshPoint(i)
        px = gr.getMeshPoint(i).getPos0().get1()
        if px<xmin: xmin=px
        if px>xmax: xmax=px
    print "(xmin,xmax)=(%f,%f)" % (xmin,xmax)
    L = xmax-xmin
    print "L=%f" % L
    #raw_input()
    
    class LObj:
        def __init__(self, px, L):
            self.px=px
            self.L=L
        def __call__(self, time):
            import math
            return time*math.sin(8*math.pi*self.px/self.L)
        
    for i in range(nbnods):
        node = gr.getMeshPoint(i)
        px = gr.getMeshPoint(i).getPos0().get1()
        #print "creating load on ", node
        obj = LObj(px-xmin, L)
        fct4 = PythonOneParameterFunction(obj)
        loadingset.define(node, Field1D(TY,GF1), -3e-4, fct4)

    
    # Time integration
    #tsm = metafor.getTimeStepManager()
    #tsm.setInitialTime(0.0, 0.02)
    #tsm.setNextTime(p['tend'], 1, p['dtmax'])

    mim = metafor.getMechanicalIterationManager()
    mim.setMaxNbOfIterations(4)
    mim.setResidualTolerance(p['tolNR'])

    ti = AlphaGeneralizedTimeIntegration(metafor)
    metafor.setTimeIntegration(ti)

    # results
    vmgr = metafor.getValuesManager()
    vmgr.add(1, MiscValueExtractor(metafor, EXT_T), 'time')
    vmgr.add(2, DbNodalValueExtractor(groupset(104), Field1D(TY,RE)), 'dy')

    return metafor





