import sys
from .ui_lib import to_did, from_did, pretty_json, print_handles
from .cli import CLI, CLICommand, InvalidOptions, InvalidArguments

class ShowCommand(CLICommand):
    
    Opts = "j"
    Usage = """[-j] <project_id> <file DID>
        -j                  -- JSON output
    """
    MinArgs = 2

    def show_handle(self, client, project_id, did, opts):
        namespace, name = from_did(did)
        handle = client.get_handle(project_id, namespace, name)
        if not handle:
            print(f"Handle {handle_id} not found")
            sys.exit(1)
        if "-j" in opts:
            print(pretty_json(handle))
        else:
            for name, val in handle.items():
                if name != "replicas":
                    print(f"{name:10s}: {val}")
            if "replicas" in handle:
                print("replicas:")
                replicas = handle["replicas"]
                for rse, r in replicas.items():
                    r["rse"] = rse
                replicas = sorted(replicas.values(), key=lambda r: (-r["preference"], r["rse"]))
                for r in replicas:
                    print("  Preference: ", r["preference"])
                    print("  RSE:        ", r["rse"])
                    print("  Path:       ", r["path"] or "")
                    print("  URL:        ", r["url"] or "")
                    print("  URLs:       ", r["urls"] or "")
                    print("  Available:  ", "yes" if r["available"] else "no")

    def __call__(self, command, client, opts, args):
        did = args[1]
        project_id = int(args[0])
        return self.show_handle(client, project_id, did, opts)

class ListHandlesCommand(CLICommand):
    Opts = "js:r:"
    Usage = """[options] <project id>
        -j                  -- JSON output
        -s <handle state>   -- list handles in state
        -r <rse>            -- list handles with replicas in RSE
    """
    MinArgs = 1

    def __call__(self, command, client, opts, args):
        project_id = int(args[0])
        proj = client.get_project(project_id, with_files=True, with_replicas=True)
        lst = proj["file_handles"]
        if "-s" in opts:
            filter_state = opts["-s"]
            filtered_state=[]
            for h in lst:
                state = h["state"]
                if filter_state==state:
                    filtered_state.append(h)
        else:
            filtered_state=lst

        if "-r" in opts:
            filter_rse = opts["-r"]
            filtered_list=[]
            for h in filtered_state:
                if filter_rse in h['replicas']:
                    filtered_list.append(h)
        else:
            filtered_list=filtered_state

        if "-j" in opts:
            print(pretty_json(filtered_list))
        else:
            print_handles(filtered_list, print_replicas=False)


FileCLI = CLI(
    "show",    ShowCommand(),
    "list", ListHandlesCommand()
)
