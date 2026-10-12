import os
import time

class TokenReader:

    def __init__(self):
        self.last_token = None
        self.last_fetch = 0

    def get(self):
        if not os.environ.get("BEARER_TOKEN_FILE", ""):
            # pick default file as BEARER_TOKEN_FILE if not set and it exists
            uid = os.getuid()
            deftokenf = f"/var/run/user/{uid}/bt_u{uid}"
            if os.access(deftokenf, os.R_OK):
                os.environ["BEARER_TOKEN_FILE"] = deftokenf
            else:
                return ""

        if self.last_fetch < time.time() - 5:
            # return cached if less than 5 seconds old
            with open(os.environ["BEARER_TOKEN_FILE"], "r") as tin:
                self.last_token = tin.read().strip()
            self.last_fetch = time.time()

        return self.last_token       

scitoken_obj = TokenReader()

scitoken = scitoken_obj.get
