import getopt, sys
from .ui_lib import pretty_json
from .cli import CLI, CLICommand, InvalidOptions, InvalidArguments
from .cli.tabular import Table, Column

#Usage = """
#show rse [-j] <name>                        - show RSE information
#set rse -a (yes|no) <name>                  - set RSE availability (requires admin privileges)
#"""

RSEOpts = "e:d:t:a:o:m:l:i:u:p:f:j"
RSEUsage = """

-e (True|False)                           -- the RSE should be enabled
-d <description>                          -- description of RSE
-t (True|False)                           -- the RSE is tape
-a (True|False)                           -- the RSE should be available
-o <preference>                           -- preference of RSE (integer)

-m <prefix>                               -- add prefix
-l <prefix>                               -- remove prefix

For dCache RSEs only:
-i (wlcg|native)                          -- interface
-u <url>                                  -- pin/discovery url
-p <prefix>                               -- pin prefix
-f <url>                                  -- poll url (only for native, not used for wlcg)

-j                                        -- json output

"""
def bool_input(opt):
    if opt in ("True", "true"):
        val = True
    elif opt in ("False", "false"):
        val = False
    else:
        val = None
    return val

def rse_input(opts):
    params = {
        'description': opts.get("-d"),
        'is_enabled': bool_input(opts.get("-e")),
        'is_tape': bool_input(opts.get("-t")),
        'is_available': bool_input(opts.get("-a")),
        'preference': int(opts.get("-o")) if opts.get("-o") is not None else None,
        'add_prefix': opts.get("-m"),
        'remove_prefix': opts.get("-l"),
        'interface': opts.get("-i"),
        'pin_url': opts.get("-u"),
        'pin_prefix': opts.get("-p"),
        'poll_url': opts.get("-f")
    }
    return params

class ShowCommand(CLICommand):
    
    Opts = "j"
    Usage = """[-j] <rse>                    -- show RSE information
        -j          -- JSON output
    """
    MinArgs = 1
    
    def __call__(self, command, client, opts, args):
        name = args[0]
        rse_info = client.get_rse(name)
        if rse_info is None:
            print(f"RSE {name} not found")
            sys.exit(1)
        if "-j" in opts:
            print(pretty_json(rse_info))
        else:
            print("RSE:           ", name)
            print("Preference:    ", rse_info["preference"])
            print("Tape:          ", "yes" if rse_info["is_tape"] else "no")
            print("Available:     ", "yes" if rse_info["is_available"] else "no")
            print("Pin URL:       ", rse_info.get("pin_url") or "")
            print("Poll URL:      ", rse_info.get("poll_url") or "")
            print("Remove prefix: ", rse_info["remove_prefix"])
            print("Add prefix:    ", rse_info["add_prefix"])

class SetAvailability(CLICommand):

    Usage = "Deprecated. Please use ddisp rse update instead."

    #Usage = "(up|down) <rse>                 - set RSE availability (requires admin privileges)"
    #MinArgs = 2
    
    #def __call__(self, command, client, opts, args):
    #    up_down, name = args
    #    if up_down not in ("up", "down"):
    #        print(Usage)
    #        sys.exit(2)
    #    return client.set_rse_availability(name, up_down == "up")
    
class ListTabularCommand(CLICommand):

    Opts = "j"
    Usage = """[-j]                          -- JSON output"""

    def __call__(self, command, client, opts, args):
        rses = sorted(client.list_rses(), key=lambda r: r["name"])
        if "-j" in opts:
            print(pretty_json(rses))
        elif rses:
            table = Table(Column("Name", min_width=30, left=True), 
                "Tape", "Status", "Enabled", 
                Column("Description", min_width=60, left=True)
            )

            for rse in rses:
                table.add_row(rse["name"],
                    "tape" if rse["is_tape"] else "",
                    "up" if rse["is_available"] else "down",
                    "yes" if rse["is_enabled"] else "no",
                    rse["description"])
            table.print()
    
class ListCommand(CLICommand):

    Opts = "j"
    Usage = """[-j]                         -- JSON output"""

    def __call__(self, command, client, opts, args):
        rses = sorted(client.list_rses(), key=lambda r: r["name"])
        if "-j" in opts:
            print(pretty_json(rses))
        elif rses:
            print("%-40s %3s %6s %s" % (
                    "Name", "Tape", "Status", "Description"
                )) 
            print("%s" % ("-"*105,)) 

            for rse in rses:
                print("%-40s %3s %6s %s" % (
                    rse["name"],
                    "tape" if rse["is_tape"] else "    ",
                    "up" if rse["is_available"] else "down",
                    rse["description"]
                ))
            print("%s" % ("-"*105,)) 

class CreateCommand(CLICommand):

    MinArgs = 1
    Opts = RSEOpts
    Usage = "[options] <rse_name>          -- create RSE" + RSEUsage

    def __call__(self, command, client, opts, args):
        p = rse_input(opts)
        name = args[0]
        rse_info = client.create_rse(name, p["description"], p["is_enabled"], p["is_available"], p["is_tape"], p["pin_url"], p["poll_url"], p["remove_prefix"], p["add_prefix"], p["pin_prefix"], p["preference"], p["interface"])

        if "-j" in opts:
            print(pretty_json(rse_info))
        else:
            print("RSE:           ", name)
            print("Preference:    ", rse_info["preference"])
            print("Tape:          ", "yes" if rse_info["is_tape"] else "no")
            print("Available:     ", "yes" if rse_info["is_available"] else "no")
            print("Pin URL:       ", rse_info.get("pin_url") or "")
            print("Poll URL:      ", rse_info.get("poll_url") or "")
            print("Remove prefix: ", rse_info["remove_prefix"])
            print("Add prefix:    ", rse_info["add_prefix"])

        
class UpdateCommand(CLICommand):

    Opts = RSEOpts
    Usage = "[options] <rse_name>        -- update RSE" + RSEUsage

    MinArgs = 1

    def __call__(self, command, client, opts, args):
        name = args[0]
        updates = rse_input(opts)

        #print(name, updates)
        rse_info = client.update_rse(name, **updates)
        
        if "-j" in opts:
            print(pretty_json(rse_info))
        else:
            print("RSE:           ", name)
            print("Preference:    ", rse_info["preference"])
            print("Tape:          ", "yes" if rse_info["is_tape"] else "no")
            print("Available:     ", "yes" if rse_info["is_available"] else "no")
            print("Pin URL:       ", rse_info.get("pin_url") or "")
            print("Poll URL:      ", rse_info.get("poll_url") or "")
            print("Remove prefix: ", rse_info["remove_prefix"])
            print("Add prefix:    ", rse_info["add_prefix"])

class DeleteCommand(CLICommand):

    Usage = """<rse_name>                    -- remove RSE"""
    MinArgs = 1

    def __call__(self, command, client, opts, args):
        rse_name = args[0]
        client.delete_rse(rse_name)

    
RSECLI = CLI(
    "list",         ListTabularCommand(),
    "show",         ShowCommand(),
    "create",       CreateCommand(),
    "update",       UpdateCommand(),
    "delete",       DeleteCommand(),
    "set",          SetAvailability()
)        
    
    
