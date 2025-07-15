import sys
import os

from os.path import abspath,dirname

sys.path.append( dirname(dirname(abspath(__file__))))

from digitalcorpora_app.main import get_dbreader

def test_dbreader():
    dbreader = get_dbreader()
    assert dbreader is not None
    return dbreader

if __name__=='__main__':
    print("testing dbreader for AWS Secrets")
    dbreader = test_dbreader()
    print(f"Successfully obtained dbreader under AWS. dbreader=",dbreader)
