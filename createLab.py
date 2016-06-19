import json
import subprocess


def toDot(input="lab.json"):
    print(input)
    with open(input) as file:
        data = json.load(file)
        # print(data)
        dot = "digraph net{\n"
        for host in data['topo']:
            for net in host['net']:
                dot += "\t" + host['host'] + " -> " + net['domain'] + ";\n"
        dot += "}"
        with open("tmp.dot", "w") as out:
            out.write(dot)
        print(" ".join(["dot", "-Tpdf", "tmp.dot", "-o", "dot.pdf"]))
        subprocess.call(["dot", "-Tpng", "tmp.dot", "-o", "dot.png"])


def createLab(inputFile="lab.json"):
    print("using " + inputFile)
    with open(inputFile) as file:
        data = json.load(file)
    # create lab.dep
    subprocess.call(["touch", "lab.dep"])
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
        labFile += hostConf+"{}[mem]={}\n\n".format(host['host'], data['mem'])
    with open("lab.conf","w") as out:
        out.write(labFile)
    # create *.startup
    for host in data['topo']:
        with open("{}.startup".format(host['host']),"w") as startup:
            startup.write("sleep 1\n")
            for i,net in enumerate(host['net']):
                startup.write("ip addr add dev eth{} {}\n".format(i, net['ip']))
            startup.write("sleep 1\n")
            for i,net in enumerate(host['net']):
                startup.write("ip link set eth{} up\n".format(i))
            startup.write("sleep 1\n")
    # copy files
    for host in data['topo']:
        subprocess.call(["cp", "-rv", "templates/conf", host['host']])

if __name__ == "__main__":
    # toDot()
    createLab()
