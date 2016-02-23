# -*- coding: latin-1; -*-
# bends a simple beam from a gmsh file

from wrap import *

metafor = None

def params(q={}):
    """ default model parameters
    """
    p={}
    p['gmshfile']      = "CantileverSquare.geo"   # gmsh
    p.update(q)
    return p

def getMetafor(p={}):
    global metafor
    if metafor: return metafor
    metafor = Metafor()

    p = parms(p)

    domain = metafor.getDomain()
    geometry = domain.getGeometry()
    geometry.setDimPlaneStrain(1.0)

    # import .geo
    from toolbox.gmsh import GmshImport
    f = os.path.join(os.path.dirname(__file__), p['gmshfile'])
    importer = GmshImport(f, domain)
    importer.execute()

    groupset = domain.getGeometry().getGroupSet()    

    # elements
    interactionset = domain.getInteractionSet()

    app1 = FieldApplicator(1)
    app1.push( groupset(300) )
    interactionset.add( app1 )

    # material
    materset = domain.getMaterialSet()
    materset.define( 1, ElastHypoMaterial )
    mater1 = materset(1)
    mater1.put(MASS_DENSITY,    8.93e-9)
    mater1.put(ELASTIC_MODULUS, 2000.0)
    mater1.put(POISSON_RATIO,   0.3)

    prp = ElementProperties(Volume2DElement)
    app1.addProperty(prp)
    prp.put (MATERIAL, 1)

    # boundary conditions
    loadingset = domain.getLoadingSet()

    loadingset.define(groupset(200), Field1D(TX,RE))
    loadingset.define(groupset(200), Field1D(TY,RE))
    
    def funct(a): return a
    fct1 = PythonOneParameterFunction(funct)
    
    # Time integration
    tsm = metafor.getTimeStepManager()
    tsm.setInitialTime(0.0, 1.0e-6)
    tsm.setNextTime(1.0, 1, 1.0e-2)

    mim = metafor.getMechanicalIterationManager()
    mim.setMaxNbOfIterations(4)
    mim.setResidualTolerance(1.0e-4)

    ti = AlphaGeneralizedTimeIntegration(metafor)
    metafor.setTimeIntegration(ti)






