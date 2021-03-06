"""
@brief      test log(time=8s)
@author     Xavier Dupre
"""

import sys, os, unittest


try :
    import src
except ImportError :
    path =  os.path.normpath(os.path.abspath(os.path.join(os.path.split(__file__)[0], "..", "..")))
    if path not in sys.path : sys.path.append(path)
    import src
    
from src.pyquickhelper.loghelper.flog           import fLOG
from src.pyquickhelper.helpgen.sphinx_main      import generate_changes_repo

class TestSphinxDocMain (unittest.TestCase):
    
    def test_sphinx_changes(self) :
        fLOG (__file__, self._testMethodName, OutputPrint = __name__ == "__main__")
        path    = os.path.abspath(os.path.split(__file__)[0])
        file    = os.path.normpath(os.path.join(path, "..", ".."))
        assert os.path.exists(file)
        fLOG(file)
        
        rst     = generate_changes_repo(None, file)
        fLOG(rst)
        assert len(rst)>0
        assert "pyquickhelper" in rst
            
        
if __name__ == "__main__"  :
    unittest.main ()    
