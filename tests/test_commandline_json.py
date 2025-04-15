import pytest
import os
import time
import json

from env import env, token, auth

test_proj = "files from mengel:gen_cfg"

@pytest.fixture(scope='session')
def proj_id_json(auth):
    with os.popen(f"ddisp project create -t 60 -p json {test_proj} ", "r") as fin:
        data = json.loads(fin.read())["project_id"]
    return data

def test_ddisp_project_create_json(auth, proj_id_json):
    assert int(proj_id_json) > 0
    assert type(int(proj_id_json)) == int

def test_ddisp_project_show_json(auth, proj_id_json):
    with os.popen(f"ddisp project show -j {proj_id_json}", "r") as fin:
        data = fin.read()
    assert data.find("owner") > 0
    assert data.find("state") > 0
    assert data.find("created_timestamp") > 0
    assert json.loads(data)

def test_ddisp_project_list_json(auth):
    with os.popen("ddisp project list -j", "r") as fin:
        data = fin.read()
    assert data.find("owner") > 0
    assert data.find("created_timestamp") > 0
    assert data.find("state") > 0
    assert json.loads(data)

def test_ddisp_project_list_options_json(auth):
    with os.popen("ddisp project list -j -s failed") as fin:
        data = fin.read()
    assert data.find("failed") >= 0
    assert data.find("abandoned") < 0
    assert json.loads(data)
    with os.popen("ddisp project list -j -s all -n cancelled") as fin:
        data = fin.read()
    assert data.find("abandoned") >= 0
    assert data.find("cancelled") < 0
    assert json.loads(data)

def test_ddisp_file_show_json(auth, proj_id_json):
    with os.popen(f"ddisp file show -j {proj_id_json} mengel:a.fcl ", "r") as fin:
        data = fin.read()
    assert data.find(f"{proj_id_json}") > 0
    assert data.find("namespace") > 0
    assert data.find("state") > 0
    assert json.loads(data)

def test_ddisp_file_list_json(auth, proj_id_json):
    with os.popen(f"ddisp file list -j {proj_id_json} ", "r") as fin:
        data = fin.read()
    assert data.find("state") > 0
    assert data.find("replicas") > 0
    assert data.find("name") > 0
    assert json.loads(data)

def test_ddisp_file_list_rse_json(auth, proj_id_json):
    with os.popen(f"ddisp file list -j -r FNAL_DCACHE_DISK_TEST {proj_id_json} ", "r") as fin:
        data = fin.read()
    assert data.find("a.fcl") > 0
    assert json.loads(data)
    with os.popen(f"ddisp file list -j -r TEST {proj_id_json} ", "r") as fin:
        data = fin.read()
    assert data.find("a.fcl") < 0

@pytest.fixture(scope='session')
def next_file_json(auth, proj_id_json):
    with os.popen(f"ddisp worker next -j {proj_id_json} ", "r") as fin:
        data = json.loads(fin.read())
        did = data["namespace"] + ":" + data["name"]
    return did

def test_ddisp_worker_next(auth, next_file_json):
    assert len(next_file_json) > 0

def test_ddisp_worker_list_json(auth, proj_id_json):
    with os.popen(f"ddisp worker list -j {proj_id_json} ", "r") as fin:
        data = fin.read()
    assert data.find("project_id") >= 0
    assert data.find("worker_id") >= 0
    assert data.find("namespace") >= 0
    assert json.loads(data)

def test_ddisp_worker_list_w_json(auth, proj_id_json):
    with os.popen("ddisp worker id", "r") as fin:
        wid = fin.read().strip()
    with os.popen(f"ddisp worker list -j -w {wid} {proj_id_json} ", "r") as fin:
        data = fin.read()
    assert data.find("namespace") >= 0
    assert data.find("project_id") >= 0
    assert data.find("worker_id") >= 0
    assert json.loads(data)

def test_ddisp_project_show_state_json(auth, proj_id_json):
    with os.popen(f"ddisp project show -j -f initial {proj_id_json}", "r") as fin:
        data = fin.read()
    assert data.find("initial") >= 0
    assert data.find("failed") < 0
    assert json.loads(data)
    with os.popen(f"ddisp project show -j -f done {proj_id_json}", "r") as fin:
        data = fin.read()
    assert json.loads(data)
    data = json.loads(data)
    assert data["file_handles"] == []
    with os.popen(f"ddisp project show -j -f test {proj_id_json}", "r") as fin:
        data = fin.read()
    assert data.find("Invalid file state") >= 0

def test_ddisp_file_list_state_json(auth, proj_id_json):
    with os.popen(f"ddisp file list -j -s initial {proj_id_json} ", "r") as fin:
        data = fin.read()
    assert json.loads(data)
    assert data.find("initial") > 0
    with os.popen(f"ddisp file list -j -s reserved {proj_id_json} ", "r") as fin:
        data = fin.read()
    assert data.find("reserved") > 0
    assert data.find("initial") < 0

@pytest.fixture(scope='session')
def proj_id_copy_json(auth, proj_id_json):
    with os.popen(f"ddisp project copy -p json {proj_id_json} ", "r") as fin:
        data = json.loads(fin.read())["project_id"]
    return data

def test_ddisp_project_copy_json(auth, proj_id_json, proj_id_copy_json):
    assert proj_id_copy_json != proj_id_json
    assert type(int(proj_id_copy_json)) == int

def test_ddisp_project_activate_json(auth, proj_id_copy_json):
    with os.popen(f"ddisp project activate -j {proj_id_copy_json} ") as fin:
        data = fin.read()
    assert json.loads(data)
    assert data.find("active") >= 0

def test_ddisp_project_cancel_json(auth, proj_id_copy_json):
    with os.popen(f"ddisp project cancel -j {proj_id_copy_json} ") as fin:
        data = fin.read()
    assert json.loads(data)
    assert data.find("cancelled") > 0

def test_ddisp_rse_list_json(auth):
    with os.popen("ddisp rse list -j", "r") as fin:
        data = fin.read()
    assert json.loads(data)
    assert data.find("name") >= 0
    assert data.find("description") >= 0

def test_ddisp_rse_show_json(auth):
    with os.popen("ddisp rse show -j FNAL_DCACHE_DISK_TEST", "r") as fin:
        data = fin.read()
    assert json.loads(data)
    assert data.find("name") >= 0
    assert data.find("is_available") >= 0


