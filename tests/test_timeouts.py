import pytest
import os
import time

from env import env, token, auth

test_proj = "files from mengel:gen_cfg"

@pytest.fixture(scope='session')
def proj_id(auth):
    with os.popen(f"ddisp project create -t 180 -w 100 {test_proj} ", "r") as fin:
        data = fin.read().strip()
    return data

def test_ddisp_worker_timeout(auth, proj_id):
    with os.popen(f"ddisp worker next {proj_id} ", "r") as fin:
        file = fin.read().strip()
    with os.popen(f"ddisp file list {proj_id} | grep {file} 2>&1", "r") as fin:
        data = fin.read()
    assert data.find("reserved") >= 0
    time.sleep(125)
    # the file should go back to the initial state after timing out
    with os.popen(f"ddisp file list {proj_id} | grep {file} ", "r") as fin:
        data = fin.read()
    assert data.find("initial") >= 0
    # the file should now have an attribute with the number of timeouts
    with os.popen(f"ddisp file show {proj_id} {file}", "r") as fin:
        data = fin.read()
    assert data.find("timeouts") >= 0

def test_ddisp_project_idle_timeout(auth, proj_id):
    # check that the project is active at first
    with os.popen(f"ddisp project show {proj_id} ", "r") as fin:
        data = fin.read()
    assert data.find("active") >= 0
    # check that the project is marked abandoned after timeout
    time.sleep(240)
    with os.popen(f"ddisp project show {proj_id} ", "r") as fin:
        data = fin.read()
    assert data.find("abandoned") >= 0

@pytest.fixture(scope='session')
def proj_id_noretry(auth):
    with os.popen(f"ddisp project create -w 100 -A 'retry_on_timeout=False' {test_proj} ", "r") as fin:
        data = fin.read().strip()
    return data

def test_no_retry_timeouts(auth, proj_id_noretry):
    with os.popen(f"ddisp worker next {proj_id_noretry} ", "r") as fin:
        file = fin.read().strip()
    time.sleep(125)
    # this time the file should go to the failed state after timing out
    with os.popen(f"ddisp file list {proj_id_noretry} ", "r") as fin:
        data = fin.read()
    assert data.find("failed") >= 0
