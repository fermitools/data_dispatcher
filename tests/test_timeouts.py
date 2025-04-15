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
    with os.popen(f"ddisp file list {proj_id} | grep {file} ", "r") as fin:
        data = fin.read()
    assert data.find("initial") >= 0

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
