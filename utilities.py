# -*- coding: latin-1; -*-
# $Id: utilities.py 2556 2016-01-29 11:41:38Z joris $
# Metafor "built-in" utilities

import wrap      # pas "from wrap import * " (Limiter les variables dans l'espace de nom local!!)
import os, os.path, sys, time, string
import socket, fnmatch
#import fac 
#import pyutils

try:
    import readline
except:
    pass

# global vars (underscore prevent them to be imported with "from module import *")

_metaOnce   = False
_theMetafor = None
_theWin     = None
_theBrowser = None
_theModule  = None
_theWDir    = None
_theBaseDir = os.getcwd()   # base directory
_theWDirRoot = os.getcwd()  # base directory du workspace
_numTasks   = 1             # nombre de taches à tourner en // (opti)

try: wrap.GUILink().setSysPath(sys.path)
except: pass

def getTheMetafor():
    global _theMetafor
    return _theMetafor

def rebase(dir):
    global _theBaseDir, _theWDirRoot
    try:
        os.chdir(dir)
    except:
        pass
    # si la base & la racine du WDir était identique => ils le restent
    if _theBaseDir == _theWDirRoot :
        _theWDirRoot = os.getcwd()
    _theBaseDir = os.getcwd()
    # check UAC (Vista) or root-protected dirs (Unix)
    if not pyutils.canCreateFile(_theBaseDir):
        text = 'You are not allowed to write something into the directory "%s" - ' % _theBaseDir
        text += 'Disable UAC (vista) or ask for root privilege (Unix) if you still want to work here.\n'
        text += 'Otherwise, rebase to another directory!'
        try: wrap.GUILink().warningMsg(text)
        except: pass

    # change sys.path
    sys.path[0] = _theBaseDir
    try: wrap.GUILink().setSysPath(sys.path)
    except: pass

def getTheBaseDir():
    global _theBaseDir
    return _theBaseDir

def getTheBaseDir():
    global _theBaseDir
    return _theBaseDir

def setTheWDirRoot(wDirRoot):
    global _theWDirRoot
    # cree le repertoire au besoin
    if not os.path.exists(wDirRoot):
        try:
            os.makedirs(wDirRoot)
        except :
            text = 'You are not allowed to create directory  "%s" - ' % wDirRoot
            text += 'Disable UAC (vista) or ask for root privilege (Unix) if you still want to work here.\n'
            text += 'Otherwise, change working dir root to another directory!'
            try: wrap.GUILink().warningMsg(text)
            except: pass
            return
    #  change the WDirRoot
    _theWDirRoot = wDirRoot
    #print "sys.path : ",sys.path
    sys.path.insert(0,wDirRoot)
    #print "sys.path : ",sys.path
    # check UAC (Vista) or root-protected dirs (Unix)
    if not pyutils.canCreateFile(_theWDirRoot):
        text = 'You are not allowed to write something into the directory "%s" - ' % _theWDirRoot
        text += 'Disable UAC (vista) or ask for root privilege (Unix) if you still want to work here.\n'
        text += 'Otherwise, rebase to another directory!'
        try: wrap.GUILink().warningMsg(text)
        except: pass
    init_py = os.path.join(wDirRoot,"__init__.py")
    if not os.path.isfile(init_py):
        #if verb: print "creating", init_py
        touchFile = open(init_py, 'w')
        touchFile.close()

    print "_theWDirRoot = ", _theWDirRoot

def getTheWDirRoot():
    global _theWDirRoot
    return _theWDirRoot

def _prepareToRun():
    """ call some funcs before running metafor integration
    """
    global _metaOnce
    if _metaOnce: raise Exception("meta/restart cannot be run more than once...\nplease, restart Metafor.")
    _metaOnce=True;
    print "\n\tStarted at", time.asctime(),
    print "on", socket.gethostname(),'\n'
    try:
        vizu()
    except:
        pass

def load(metaforTxt):
    """ load a module and make it the current one
    """
    global _theModule

    if not isinstance(metaforTxt, str): raise Exception("argument must be a string!")
    if _theModule: raise Exception("no more than one module may be loaded!")

    if metaforTxt=="__main__": # on est dans un script => getmetafor est/sera dans __main__
        _theModule = sys.modules['__main__']
    else:
        if os.path.isfile(metaforTxt): # c'est une nom de fichier => on convertit en nom de module
            module = pyutils.fileToModule(metaforTxt, verb=False)
            if not module: raise Exception('file "%s" is not a reachable python module!' % metaforTxt)
            metaforTxt = module
        # ici, on a un nom de module...
        exec("import %s" % metaforTxt) # peut on le faire plus tard?
        exec("globals()['_theModule'] = %s" % metaforTxt)
        print "module '%s' loaded!" % metaforTxt
        #print '_theModule', _theModule

    setTheWDir(metaforTxt)

    try: wrap.GUILink().setState2()
    except: pass

    return _theModule

def setTheWDir(metaforTxt):
    global _theWDir
    _theWDir = defaultWDir(metaforTxt)
    # on fait un chdir si ce rep existe!
    if os.path.isdir(_theWDir):
        setDir(_theWDir)

    print "_theWDir = ", _theWDir
    return _theWDir

def defaultWDir(moduleTxt):
    global _theWDirRoot
    return os.path.join(_theWDirRoot, os.path.join("workspace", moduleTxt.replace('.','_') )) # default WDir for the module

def forceTheWDir():
    global _theWDir
    setDir(_theWDir)

def setDir(wdir):  # (avant instance) - change le rep courant
    global _theWDirRoot
    """ change the current working directory
    """
    if wdir:
        if not os.path.isabs(wdir):
            wdir = os.path.join(_theWDirRoot, wdir)
        try:
            if not os.path.isdir(wdir):
                os.makedirs(wdir)
            os.chdir(wdir)
        except OSError, e:
            print "OSError : ", e
            # check UAC (Vista) or root-protected dirs (Unix)
            text = 'Directory "%s" may not be created.\n' % wdir
            text += 'Disable UAC (vista) or ask for root privilege (Unix) if you still want to work here.\n'
            text += 'Otherwise, rebase to another directory!'
            try: wrap.GUILink().warningMsg(text)
            except: pass
            raise Exception('directory "%s" cannot be created' % wdir)
    global _theWDir
    _theWDir = os.getcwd() # stoque un chemin absolu meme si ca a merdé.
    print "_theWDir = ", _theWDir

def instance(pars=None):
    """ calls module.getMetafor(pars) [module previously loaded with "load()"]
    """

    global _theMetafor, _theModule
    if _theMetafor: return _theMetafor
    if not _theModule: raise Exception('load a module before calling "instance"!')
    if pars==None: # not specified => try to load pars
        if os.path.isfile("pars.py"):
            print 'Info: Loading "pars.py" from %s' % os.getcwd()
            #execfile("pars.py") # impossible de changer une var locale via une fct
            try:
                exec open("pars.py").read() # exec est un keyword => ca marche
                print "Info: pars =", pars
                if pars==None:
                    raise Exception('bad "pars.py"!')
            except:
                print 'Unable to reload pars.py. => pars={}!'
                pars={}

        else:
            print 'Warning: "pars.py" not found while instantiating the analysis!'
            pars={}
    # instanciate the analysis
    _theMetafor = _theModule.getMetafor(pars)

    if _theMetafor is None:
        raise Exception("getMetafor must return a Metafor analysis!")
    # save pars
    if not os.path.isfile("pars.py"):
        file = open("pars.py",'w')
        file.write("pars=%s\n" % repr(pars))
        file.close()
    try:
        wrap.GUILink().setMainObject(_theMetafor) # info to GUI
    except: # on n'a pas de GUI
        pass
    return _theMetafor

def _chkMetafor(emptyWork=False):
    # chkDir
    global _theWDir
    print '_theWDir="%s"' %_theWDir
    setDir(_theWDir)

    # check Workspace if needed
    if emptyWork:
        _chkWorkspace()

    # instatiate metafor if not done
    global _theMetafor, _theModule
    if not _theMetafor:
        if _theModule:
            instance()
        else:
            if not _theModule: raise Exception('load first a module with "load()"')

def _chkWorkspace():
    """ Check/Clean workspace
    """
    flist=[]
    for file in os.listdir('.'):
        if os.path.isdir(file):
            raise Exception("Your workspace contains one or more directories!")
        elif os.path.isfile(file):
            for sk in ['*.fdb','*.conf','*.msh', '*.gen4', '*.gen4.md5']: # files to keep
                if fnmatch.fnmatch(os.path.basename(file), sk):
                    break
            else:
                flist.append(os.path.abspath(file))

    if flist:
        answer = True
        try: answer = wrap.GUILink().askDelete(flist)
        except: pass
        if answer:
            for file in flist:
                try:
                    os.remove(file)
                except:
                    print "Unable to remove", file
        else:
            raise Exception("meta() cancelled!")

def meta(emptyWork=True):
    """ Start Metafor integration
    """
    _chkMetafor(emptyWork)
    log = wrap.LogFile("resFile.txt");
    # start metafor integration
    _prepareToRun()
    try: wrap.GUILink().setState3()
    except: pass
    _theMetafor.getTimeIntegration().integration()
    try: wrap.GUILink().setState2()
    except: pass

def restart(step):
    """ Restart metafor - expl: restart(35)
    """
    _chkMetafor()
    log = wrap.LogFile("restartResFile.txt");
    _prepareToRun()
    try: wrap.GUILink().setState3()
    except: pass
    _theMetafor.getTimeIntegration().restart(step);
    try: wrap.GUILink().setState2()
    except: pass

def browse():
    global _theBrowser
    if not _theBrowser:
        _chkMetafor()
        _theBrowser = wrap.ObjectBrowser(_theMetafor.getDomain())
    _theBrowser.open()

# === VIZU ===

def vizu():
    """ Quick vizu of a domain
    """
    global _theWin
    if not _theWin:
        _chkMetafor()
        domain = _theMetafor.getDomain()
        domain.build()
        _theWin = wrap.VizWin()
        _theWin.add(domain.getGeometry().getPointSet())
        _theWin.add(domain.getGeometry().getCurveSet())
        _theWin.add(domain.getGeometry().getSurfaceSet())
        #_theWin.add(domain.getGeometry().getWireSet())
        #_theWin.add(domain.getGeometry().getSideSet())
        #for i in range(domain.getGeometry().getSideSet().size()):
        #    _theWin.add(domain.getGeometry().getSideSet()[i])
        for i in range(domain.getInteractionSet().size()):
            _theWin.add(domain.getInteractionSet().getInteraction(i))
        #for i in range(domain.getInteractionSet().size()):
        #   for j in range(domain.getInteractionSet().getInteraction(i).getElementSet().size()) :
        #       _theWin.add(domain.getInteractionSet().getInteraction(i).getElementSet().getElement(j))
        #for i in range(domain.getInteractionSet().size()):
        #   _theWin.add(domain.getInteractionSet().getInteraction(i).getElementSet())
#        _theWin.add(domain.getInteractionSet())
        #_theWin.add(domain.getGeometry().getSkinSet())
        #for i in range(domain.getGeometry().getSkinSet().size()):
        #    _theWin.add(domain.getGeometry().getSkinSet()[i])
        _theMetafor.addObserver(_theWin)
        _theMetafor.buildMainVizWinGUITitle()

    _theWin.open() # open / raise the window

# === GESTION DU FAC / COURBES ===

def save2vtk():
    """ Save results to vtk
    """
    # save vtk polydatas and vtk ugrids for each time step
    name = "meta2vtk_step_"
    makeAnimation(name, 12)

    # write paraview input file
    valuesmanager = _theMetafor.getValuesManager()
    valuesmanager.clear()
    valuesmanager.add(1, wrap.MiscValueExtractor(_theMetafor,wrap.EXT_T),'time')
    rebuildCurves()

    files = os.listdir(os.getcwd())
    partsInd = []
    partsName = []
    for filename in fnmatch.filter(files, name+'*_part*'):
        i = filename.split(name)[1].split('_')[0]
        j = filename.split(name+i+'_part')[1].split('_')[0]
        if j not in partsInd:
            partsInd.append(j)
            partsName.append(filename.split(name+i+'_')[1].split('.')[0] + '.pvd')

    for jj, j in enumerate(partsInd):
        pvdfile = open(partsName[jj],'w')
        pvdfile.write('<VTKFile type="Collection" version="0.1" byte_order="LittleEndian">\n')
        pvdfile.write('  <Collection>\n')
        for filename in fnmatch.filter(files, name+'*_part'+j+'_*'):
            i = filename.split(name)[1].split('_')[0]
            try:
                time = valuesmanager.getDataVector(1).getValue(int(i))
            except:
                time = i
            pvdfile.write('    <DataSet part="0"  timestep="%f" file="%s"/>\n'%(float(time),filename))
        pvdfile.write('  </Collection>\n')
        pvdfile.write('</VTKFile>\n')
        pvdfile.close()
        print "paraview intput file written to",partsName[jj]


def makeAnimation(name = "anim", captureFormat = 0):
    """ Make automatic screen captures
    """
    _chkMetafor()
    vizu()
    raw_input("Press [ENTER] when ready...\n")
    loader = fac.FacManager(_theMetafor)
    no=0
    for file in loader.facs: # loop on files
        loader.load(file)
        _theWin.update()
        _theWin.update()
        _theWin.save(name, no, captureFormat)
        no += 1

def makeStereoAnimation():
    """ Make automatic screen captures in stereo (2 sets of images for both eyes)
    """
    _chkMetafor()
    vizu()
    raw_input("Press [ENTER] when ready...\n")

    try:
        os.mkdir('left')
    except:
        pass
    try:
        os.mkdir('right')
    except:
        pass

    loader = fac.FacManager(_theMetafor)
    no=0
    for file in loader.facs: # loop on files
        loader.load(file)
        os.chdir('left')
        _theWin.setStereoType(4) # left
        _theWin.update()
        _theWin.save("img", no, wrap.SAVE_TIFF) # tiff non compressé
        os.chdir('../right')
        _theWin.setStereoType(5) # right
        _theWin.update()
        _theWin.save("img", no, wrap.SAVE_TIFF)
        os.chdir('..')
        no += 1


def loadFac(nt=None):
    _chkMetafor()
    loader = fac.FacManager(_theMetafor)
    loader.load(nt)

def saveFac(bin=True, zip=True):
    _chkMetafor()
    writer = fac.FacManager(_theMetafor)
    writer.save(bin, zip)

# ---- Converters

def rebuildCurves():
    """ rebuilds the valuesmanager (.v and .ascii) from the facs
    """
    _chkMetafor()
    _theMetafor.getDomain().build()
    valuesmanager = _theMetafor.getValuesManager()
    loader = fac.FacManager(_theMetafor)
    for file in loader.facs: # loop on files
        loader.load(file)
        valuesmanager.fillNow()
    valuesmanager.toAscii()
    valuesmanager.flush()

def rebuildAsciiFromV(nt=None):
    """ rebuilds the .ascii from .v
    """
    _chkMetafor()
    _theMetafor.getDomain().build()
    valuesmanager = _theMetafor.getValuesManager()
    valuesmanager.load()
    if nt:
        valuesmanager.resize(nt+1)
    valuesmanager.toAscii()
    #valuesmanager.flush() # Pas utile voire dangereux si on a redimensionné
    print "\nascii files created.\n"

def getValuesManager():
    """ rebuilds the .ascii from .v
    """
    _chkMetafor()
    _theMetafor.getDomain().build()
    valuesmanager = _theMetafor.getValuesManager()
    valuesmanager.load()
    #except :
    #    print "error on vm no : " , no
    print "\nascii files created.\n"
    return valuesmanager

def convertFac(bin=True, zip=True):
    _chkMetafor()
    conv = fac.FacManager(_theMetafor)
    conv.convert(bin, zip)
#------------------------------------------------------------------------------------
def asciiVector2InMemoryDataVector(fileName):
    dv = wrap.InMemoryDataVector()
    file = open(fileName,'r')
    for line in file.readlines():
        val = float(line)
        dv.pushBack(val)
    return dv
#------------------------------------------------------------------------------------
def ascii2InMemoryDataMatrix(fileName):
    file = open(fileName,'r')
    line = file.readline()
    row = str2DoubleVector(line)
    #print row
    #print "row.size() = " ,row.size()
    dm = wrap.InMemoryDataMatrix(row.size())
    dm.pushBack(row)
    line = file.readline()
    while line :
        row = str2DoubleVector(line)
        dm.pushBack(row)
        line = file.readline()
    return dm    
def str2DoubleVector(line):
    row = wrap.DoubleVector()
    #print "line = ",line
    for val in line.split():
        row.push_back(float(val))
    return row    
#------------------------------------------------------------------------------------
def rerunObjectiveFunctionSet():
    _chkMetafor()
    _theMetafor.getDomain().build()
    fobjSet = _theMetafor.getObjectiveFunctionSet()
    fobjSet.list()
    fobjSet.compute()

def getObjectiveFunctionSet():
    _chkMetafor()
    _theMetafor.getDomain().build()
    fobjSet = _theMetafor.getObjectiveFunctionSet()
    fobjSet.list()
    return fobjSet
# nbTasks
def getNumTasks():
    global _numTasks
    print "getNumTasks : ", _numTasks
    return _numTasks
def setNumTasks(numTasks):
    global _numTasks
    _numTasks = numTasks
    print "numTasks set to ",_numTasks
