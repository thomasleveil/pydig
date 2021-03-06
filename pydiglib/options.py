import os, sys, socket, base64

from .common import *
from .util import *
from .tsig import Tsig, read_tsig_params


# Global dictionary of options: many options may be overridden or set in
# parse_args() by command line arguments.
options = dict(
    server=None, 
    port=DEFAULT_PORT, 
    srcip=None, 
    use_tcp=False,
    aa=0, 
    ad=0,
    cd=0, 
    rd=1, 
    use_edns0=False, 
    dnssec_ok=0,
    hexrdata=False, 
    do_zonewalk=False, 
    do_0x20=False,
    ptr=False, 
    af=socket.AF_UNSPEC, 
    do_tsig=False,
    tsig_sigtime=None, 
    unsigned_messages="", 
    msgid=None)


def parse_args(arglist):
    """Parse command line arguments. Options must come first."""

    global DEBUG
    qtype = "A"
    qclass = "IN"
    
    i=0
    tsig = options["tsig"] = Tsig()
    
    for (i, arg) in enumerate(arglist):

        if arg.startswith('@'):
            options["server"] = arg[1:]

        elif arg == "-h":
            raise UsageError()

        elif arg.startswith("-p"):
            options["port"] = int(arg[2:])

        elif arg.startswith("-b"):
            options["srcip"] = arg[2:]

        elif arg == "+tcp":
            options["use_tcp"] = True

        elif arg == "+aaonly":
            options["aa"] = 1

        elif arg == "+adflag":
            options["ad"] = 1

        elif arg == "+cdflag":
            options["cd"] = 1

        elif arg == "+norecurse":
            options["rd"] = 0

        elif arg == "+edns0":
            options["use_edns0"] = True

        elif arg == "+dnssec":
            options["dnssec_ok"] = 1; options["use_edns0"] = True

        elif arg == "+hex":
            options["hexrdata"] = True

        elif arg == "+walk":
            options["do_zonewalk"] = True

        elif arg == "+0x20":
            options["do_0x20"] = True

        elif arg == "-4":
            options["af"] = socket.AF_INET

        elif arg == "-6":
            options["af"] = socket.AF_INET6

        elif arg == "-x":
            options["ptr"] = True

        elif arg == "-d":
            DEBUG = True

        elif arg.startswith("-k"):
            tsig_file = arg[2:]
            name, key = read_tsig_params(tsig_file)
            tsig.setkey(name, key)
            options["do_tsig"] = True

        elif arg.startswith("-i"):
            options["msgid"] = int(arg[2:])

        elif arg.startswith("-y"):
            # -y overrides -k, if both are specified
            alg, name, key = arg[2:].split(":")
            key = base64.decodestring(key)
            tsig.setkey(name, key, alg)
            options["do_tsig"] = True

        else:
            break

    if not options["server"]:         # use 1st server listed in resolv.conf
        for line in open(RESOLV_CONF):
            if line.startswith("nameserver"):
                options["server"] = line.split()[1]
                break
        else:
            raise ErrorMessage("Couldn't find a default server in %s" %
                               RESOLV_CONF)

    qname = arglist[i]

    if not options["do_zonewalk"]:
        if arglist[i+1:]:           qtype = arglist[i+1].upper()
        if arglist[i+2:]:           qclass = arglist[i+2].upper()

    if options["ptr"]:
        qname = ip2ptr(qname); qtype = "PTR"; qclass = "IN"
    else:
        if not qname.endswith("."): qname += "."

    return (qname, qtype, qclass)

