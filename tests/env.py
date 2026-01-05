import os
import sys
import pytest

production=os.environ.get("DDISP_TEST_PRODUCTION", False)

if not production:
    base = os.path.dirname(os.path.dirname(__file__))
    os.environ["PATH"] = f"{base}/data_dispatcher/ui:{os.environ['PATH']}"
#    os.environ["PYTHONPATH"] = f"{base}:{base}/tests/mocks:{os.environ.get('PYTHONPATH','')}"
    os.environ["PYTHONPATH"] = f"{base}:{base}/data_dispatcher:{os.environ['PYTHONPATH']}"
    sys.path.insert(0,base)
#    sys.path.insert(0,f"{base}/tests/mocks")

@pytest.fixture(scope='session')
def env():
    if production:
       hostaport = 'https://metacat.fnal.gov:8143'
       hostport = 'https://metacat.fnal.gov:9443'
    else:
       hostaport = 'https://metacat.fnal.gov:8143'
       hostport = 'http://fermicloud761.fnal.gov:9094'


    os.environ['METACAT_AUTH_SERVER_URL'] = f'{hostaport}/auth/hypot_dev'
    os.environ['DATA_DISPATCHER_URL'] = f'{hostport}/hypot_dd/data'
    os.environ['METACAT_SERVER_URL'] = f'{hostport}/hypot_meta_dev/app'
    os.environ['DATA_DISPATCHER_AUTH_URL'] = f'{hostaport}/auth/hypot_dev'
    os.environ['BEARER_TOKEN_FILE'] = '/tmp/bt_mc_test%d' % os.getpid()
    print("METACAT_SERVER_URL=", os.environ["METACAT_SERVER_URL"])
    print("DATA_DISPATCHER_URL=", os.environ["DATA_DISPATCHER_URL"])

@pytest.fixture(scope='session')
def token(env):
    os.system("htgettoken -i hypot -a htvaultprod.fnal.gov ")
    
@pytest.fixture(scope='session')
def auth(token):
    os.system("metacat auth login -m token $USER")
    os.system("ddisp login -m token $USER")
