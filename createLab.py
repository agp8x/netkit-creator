import json
import subprocess
import argparse


def toDot(input="lab.json"):
    print(input)
    with open(input) as file:
        data = json.load(file)
        # print(data)
        domains = {}
        for host in data['topo']:
            for net in host['net']:
                if not net['domain'] in domains:
                    domains[net['domain']] = []
                # dot += "\t" + host['host'] + " -> " + net['domain'] + ";\n"
                domains[net['domain']].append(host['host'])
        dot = "digraph net{\n"
        for domain in domains:
            hosts = []
            for host in domains[domain]:
                for host2 in domains[domain]:
                    if host == host2 or host2 in hosts:
                        continue
                    dot += "\t{} -> {} [dir=\"none\",label=\" {}\"];\n".format(host, host2, domain)
                    hosts.append(host)
        dot += "}"
        with open(data['name'] + ".dot", "w") as out:
            out.write(dot)
        subprocess.call(["dot", "-Tpng", data['name'] + ".dot", "-o", data['name'] + ".png"])


def createLab(inputFile="lab.json"):
    print("using " + inputFile)
    with open(inputFile) as file:
        data = json.load(file)
    subprocess.call(["mkdir", data['name']])
    # create lab.dep
    subprocess.call(["touch", data['name'] + "/lab.dep"])
    # create lab.conf
    labFile = "LAB_DESCRIPTION=\"{}\"\n".format(data['name'])
    with open("templates/lab.conf") as tpl:
        labFile += "".join(tpl.readlines())
    labFile += "machines=\""
    labFile += " ".join(x['host'] for x in data['topo'])
    labFile += "\"\n\n"
    for host in data['topo']:
        hostConf = ""
        for i, net in enumerate(host['net']):
            hostConf += "{}[{}]={}\n".format(host['host'], i, net['domain'])
        labFile += hostConf + "{}[mem]={}\n\n".format(host['host'], data['mem'])
    with open(data['name'] + "/lab.conf", "w") as out:
        out.write(labFile)
    # create *.startup
    for host in data['topo']:
        with open(data['name'] + "/{}.startup".format(host['host']), "w") as startup:
            startup.write("sleep 1\n")
            for i, net in enumerate(host['net']):
                startup.write("ip addr add dev eth{} {}\n".format(i, net['ip']))
            startup.write("sleep 1\n")
            for i, net in enumerate(host['net']):
                startup.write("ip link set eth{} up\n".format(i))
            startup.write("sleep 1\n")
    # copy files
    for host in data['topo']:
        subprocess.call(["cp", "-rv", "templates/conf/", data['name'] + "/{}/".format(host['host'])])


def wipe(labFile='lab.json'):
    with open(labFile) as file:
        data = json.load(file)
    input("DELETE " + data['name'] + "? [Y]")
    subprocess.call(["rm", data['name'] + ".dot", data['name'] + ".png"])
    subprocess.call(["rm", "-rfv", data['name']])


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="create Netkit labs")
    parser.add_argument("--lab", "-l", default="lab.json", help="Lab definition JSON")
    parser.add_argument("--plot", "-p", action='store_true')
    parser.add_argument("--create", "-c", action='store_true')
    parser.add_argument("--force", "-f", action='store_true')
    parser.add_argument("--wipe", "-w", action='store_true')
    args = parser.parse_args()
    if args.wipe:
        wipe(args.lab)
    if args.plot:
        toDot(args.lab)
    if args.create:
        if not args.force:
            input("create lab? [Y]")
        createLab(args.lab)
