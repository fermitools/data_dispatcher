
import pytest
import os
import time

from env import env, token, auth
from test_commandline import proj_id

test_proj = "files from mengel:gen_cfg"

def test_issue_18(proj_id):
    # reserve a file as worker_id a, 
    # then try to release it as worker_id b, should fail
    # then try to release it as worker_id a, should succeed

    with os.popen("ddisp worker id -n", "r") as fin:
        wid1 = fin.read().strip()
    with os.popen("ddisp worker id -n", "r") as fin:
        wid2 = fin.read().strip()
    with os.popen(f"ddisp worker id {wid1}", "r") as fin:
        wid = fin.read().strip()
    with os.popen(f"ddisp worker next {proj_id} ", "r") as fin:
        reserved_file = fin.read().strip()
    # so now we've reserved a file
    # try to mark it done with a different worker id:
    with os.popen(f"ddisp worker id {wid2}", "r") as fin:
        wid = fin.read().strip()
    with os.popen(f"ddisp worker done {proj_id} {reserved_file} ", "r") as fin:
        out = fin.read()
    assert(out.find("wrong worker_id") >= 0)

    # now mark it done with the original worker id:
    with os.popen(f"ddisp worker id {wid1}", "r") as fin:
        wid = fin.read().strip()
    with os.popen(f"ddisp worker done {proj_id} {reserved_file} ", "r") as fin:
        out = fin.read()
    assert(len(out.strip()) == 0)
