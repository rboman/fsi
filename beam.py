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
    p['bctype']     = 'pydeadloads'    # pressure / pydeadload1
                                       # deadload / pydeadloads
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

    #   - f(x)=x
    def funct(a): return a
    fct1 = PythonOneParameterFunction(funct)
    
    #  - basic pwl function
    fct2 = PieceWiseLinearFunction()
    fct2.setData(0.0, 0.0)
    fct2.setData(0.1, 1.0)
    fct2.setData(0.1+1e-15, 0.0)
    fct2.setData(1e10, 0.0)    

    #  - python fct
    def f(time):
        val=0
        t1=0.1
        if(time<=0.1):
           val=1.0/t1*time
        else:
           val=0.0
        #print "f(%f)=%f" % (time,val)
        return val
    fct3 = PythonOneParameterFunction(f)

    gr = groupset(103)
    if p['bctype']=='pressure':
        trac1 = LoadingInteraction(2)
        trac1.push(gr)
        interactionset.add(trac1)
        prp = ElementProperties(Traction2DElement)
        prp.put(PRESSURE, -0.1)
        prp.depend(PRESSURE, fct2, Field1D(TM,RE))
        trac1.addProperty(prp)
    elif p['bctype']=='deadload':
        loadingset.define(gr, Field1D(TY,GF1), -1e-4, fct2)
    elif p['bctype']=='pydeadload1':
        loadingset.define(gr, Field1D(TY,GF1), -1e-4, fct3) 
    elif p['bctype']=='pydeadloads':
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
    else:
        raise Exception("Unknown bctype %s" % p['bctype'])
    
    # Time integration
    tsm = metafor.getTimeStepManager()
    tsm.setInitialTime(0.0, 0.02)
    tsm.setNextTime(p['tend'], 1, p['dtmax'])

    mim = metafor.getMechanicalIterationManager()
    mim.setMaxNbOfIterations(4)
    mim.setResidualTolerance(p['tolNR'])

    ti = AlphaGeneralizedTimeIntegration(metafor)
    metafor.setTimeIntegration(ti)

    # results
    vmgr = metafor.getValuesManager()
    vmgr.add(1, MiscValueExtractor(metafor, EXT_T), 'time')
    vmgr.add(2, DbNodalValueExtractor(groupset(104), Field1D(TY,RE)), 'dy')

    # plots
    try:
        plot1 = DataCurveSet()
        vmgr = metafor.getValuesManager()
        plot1.add(VectorDataCurve(1, vmgr.getDataVector(1), vmgr.getDataVector(2)))
        win1 = VizWin()
        win1.add(plot1)
        metafor.addObserver(win1)
    except:
        pass


    return metafor





