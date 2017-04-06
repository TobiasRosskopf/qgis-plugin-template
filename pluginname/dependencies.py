import os
import importlib
import imp
import shutil
from qgis.core import *

def _packageFolder(name):
    parent = os.path.join(os.path.dirname(__file__), "ext-libs")
    for path in os.listdir(parent):
        if os.path.isdir(os.path.join(parent, path)) and path.startswith(name + "-"):
            for subpath in os.listdir(os.path.join(parent, path)):
                if os.path.isdir(os.path.join(parent, path, subpath)) and subpath.lower() != "egg-info":                        
                    return os.path.join(parent, path, subpath)

def ensureDependencies():
    '''
    This installs the dependencies in a common folder, shared by all plugins that use this function.
    Dependencies are declared in a requirements.txt file, which is also used by the paver task that 
    performs the setup. Dependencies are not install or downloaded by this function, which assumes 
    that the corresponding dependencies folders are already downloaded and stored in the appropriate 
    folder ("ext-libs").

    If a version of the dependency exists in the shared folder, it will be replaced if it's older 
    than the one to be installed. That ensures that the latest available version will be used by 
    all plugin. Whit that, we are asumming that all plugin can run on that latest version and there
    are no change in it that are not backwards compatible.

    If the library is installed by another plugin in a place other that the shared folder, there is
    nothing that can be done in that case, and we are not considering that situation.
    '''
    lines = open(os.path.join(os.path.dirname(__file__), 'requirements.txt')).readlines()
    lines = [l for l in [ l.strip() for l in lines] if l]
    try:
        idx = lines.index('# test requirements')
    except ValueError:
        idx = None
    requirements = [l.split("=")[0] for l in lines[:idx] if l[0] != '#']
    parentPath = os.path.join(QgsApplication.qgisSettingsDirPath(), "python", "ext-libs")   
    for lib in requirements:
        srcPath = _packageFolder(lib)        
        if srcPath is None:
            continue
        packageName = os.path.basename(srcPath)
        dstPath = os.path.join(parentPath, packageName)
        try:
            module = importlib.import_module(packageName)
            print module.__path__, dstPath
            if module.__path__ == dstPath:
                dstVersion = module.__version__
                srcModule = imp.load_source(packageName, srcPath + "/__init__.py")
                srcVersion = srcModule.__version__
                print srcVersion, dstVersion
                if srcVersion > dstVersion:
                    update = True
            else:
                update = True               
        except ImportError:
            update = True
    
        if update:
            shutils.rmtree(dstPath)
            shutil.copytree(srcPath, dstPath)
            module = imp.load_source(packageName, dstPath +  "/__init__.py")
            reload(module)
        
    ensureQgisCommons()

def ensureQgisCommons():
    qgiscommonDstPath = os.path.join(QgsApplication.qgisSettingsDirPath(), "python", "ext-libs", "qgiscommons")
    qgiscommonSrcPath = os.path.join(os.path.dirname(__file__), "ext-libs", "qgiscommons")
    if os.path.exists(qgiscommonDstPath):
        update = False
        try:
            versionSrcFile = os.path.join(qgiscommonSrcPath, "version.json")
            versionDstFile = os.path.join(qgiscommonDstPath, "version.json")
            with open(versionSrcFile) as f:
                versionSrc = datetime.datetime.strptime(json.load(f)["committer"]["date"], "%Y-%m-%dT%H:%M:%S")
            with open(versionDstFile) as f:
                versionDst = datetime.datetime.strptime(json.load(f)["committer"]["date"], "%Y-%m-%dT%H:%M:%S")
            update = versionSrc > versionDst
        except: #update if there are errors, assuming that existing version is older or incomplete
            update = True
    else:
        update = True
        

    if update:
        shutils.rmtree(qgiscommonDstPath)
        shutil.copytree(qgiscommonSrcPath, qgiscommonDstPath)
        module = imp.load_source("qgiscommons", qgiscommonDstPath +  "/__init__.py")
        reload(module)
        