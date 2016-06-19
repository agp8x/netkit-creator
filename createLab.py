import json
import subprocess
import argparse


def read_json(lab_def):
    with open(lab_def) as file:
        data = json.load(file)
    return data


def dot(lab_def="lab.json"):
    data = read_json(lab_def)
    domains = {}
    for host in data['topo']:
        for net in host['net']:
            if not net['domain'] in domains:
                domains[net['domain']] = []
            domains[net['domain']].append(host['host'])
    if "tap" in domains:
        domains["tap"].append("HOST")
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


def create_lab(lab_def="lab.json"):
    data = read_json(lab_def)
    subprocess.call(["mkdir", data['name']])
    # create lab.dep
    subprocess.call(["touch", data['name'] + "/lab.dep"])
    # create lab.conf
    lab_file = "LAB_DESCRIPTION=\"{}\"\n".format(data['name'])
    with open("templates/lab.conf") as tpl:
        lab_file += "".join(tpl.readlines())
    lab_file += "machines=\""
    lab_file += " ".join(x['host'] for x in data['topo'])
    lab_file += "\"\n\n"
    for host in data['topo']:
        host_conf = ""
        for i, net in enumerate(host['net']):
            if net['domain'] == 'tap':
                continue
            host_conf += "{}[{}]={}\n".format(host['host'], i, net['domain'])
        if host['host'] == "tap":
            host_conf+="tap[{}]={}\n".format(i+1, host['tap'])
        lab_file += host_conf + "{}[mem]={}\n\n".format(host['host'], data['mem'])
    with open(data['name'] + "/lab.conf", "w") as out:
        out.write(lab_file)
    # create *.startup
    for host in data['topo']:
        startup = "sleep 1\n"
        for i, net in enumerate(host['net']):
            startup += "ip addr add dev eth{} {}\n".format(i, net['ip'])
        startup += "sleep 1\n"
        for i, net in enumerate(host['net']):
            startup += "ip link set eth{} up\n".format(i)
        startup += "sleep 1\n"
        with open(data['name'] + "/{}.startup".format(host['host']), "w") as startup_file:
            startup_file.write(startup)
    # copy files
    for host in data['topo']:
        subprocess.call(["cp", "-rv", "templates/conf/", data['name'] + "/{}/".format(host['host'])])


def wipe(lab_def='lab.json'):
    data = read_json(lab_def)
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
        dot(args.lab)
    if args.create:
        if not args.force:
            input("create lab? [Y]")
        create_lab(args.lab)
