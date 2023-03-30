import time
import os
from http.server import BaseHTTPRequestHandler, HTTPServer


# HOST_NAME = '192.168.1.10'
# HOST_NAME = '10.132.248.183'
HOST_NAME = '127.0.0.1'
PORT_NUMBER = 8000

HTML_INDENT = "&nbsp&nbsp&nbsp&nbsp"


def read_file(filepath) -> str:
    file = open(filepath, "r")
    return file.read()


def time_from_seconds(total_seconds) -> str:
    hours = int(total_seconds / 3600)
    minutes = int((total_seconds % 3600) / 60)
    seconds = int((total_seconds % 3600) % 60)
    return str(hours) + "hours, "    \
        + str(minutes) + "minutes, " \
        + str(seconds) + "seconds"


# NOTE: run `man proc` to find out what exists in the /proc directory

def date_time():
    return ""


def uptime():
    s = read_file("/proc/uptime")
    total_seconds = float(s.split(' ')[0])
    return time_from_seconds(total_seconds)


def procinfo():
    lines = read_file("/proc/cpuinfo").split('\n')
    ret = "<br>"
    for line in lines:
        words = line.split(':')
        key = words[0].strip()
        value = words[1].strip()
        if key == "vendor_id" or  \
           key == "cpu family" or \
           key == "model" or      \
           key == "model name":
            ret += HTML_INDENT + key + ": " + value + "<br>"
        elif key == "cpu MHz":
            ret += HTML_INDENT + key + ": " + value + "<br>"
            break
    return ret


def proccap():
    return ""


def mem():
    "For this function, we follow the same calculations as the `free` command"
    lines = read_file("/proc/meminfo").split('\n')
    # MemTotal
    for s in lines[0].split(' '):
        if s.isnumeric():
            total = int(s)
            break
    # MemFree
    for s in lines[1].split(' '):
        if s.isnumeric():
            free = int(s)
            break
    # Buffers
    for s in lines[3].split(' '):
        if s.isnumeric():
            buffers = int(s)
            break
    # Cached
    for s in lines[4].split(' '):
        if s.isnumeric():
            cache = int(s)
            break
    # SReclaimable
    for s in lines[27].split(' '):
        if s.isnumeric():
            cache += int(s)
            break

    used = total - free - buffers - cache
    return "Total: " + str(total) + "Kb, Used: " + str(used) + "Kb"


def sysversion():
    return read_file("/proc/version")


def proc_list():
    ret = "<br>" + HTML_INDENT + "Pid Name<br>"
    for dir_entry in os.listdir("/proc"):
        if dir_entry.isnumeric():
            s = read_file("/proc/" + dir_entry + "/stat")
            pid = s.split(' ')[0]
            name = s.split(' ')[1].strip("()")
            ret += HTML_INDENT + pid + " " + name + "<br>"
    return ret


class MyHandler(BaseHTTPRequestHandler):
    def do_HEAD(s):
        s.send_response(200)
        s.send_header("Content-type", "text/html")
        s.end_headers()

    def do_GET(s):
        """Respond to a GET request."""
        s.send_response(200)
        s.send_header("Content-type", "text/html")
        s.end_headers()
        s.wfile.write("<html><head><title> SysOp T1 </title></head>".encode())
        s.wfile.write(("<body><p>Host: " + HOST_NAME + "</p>").encode())

        s.wfile.write(("<p>Date and time: " + date_time() + "</p>").encode())
        s.wfile.write(("<p>Uptime: " + uptime() + "</p>").encode())
        s.wfile.write(("<p>Processor: " + procinfo() + "</p>").encode())
        s.wfile.write((
            "<p>Processor occupied capacity: "
            + proccap() + "</p>").encode())
        s.wfile.write(("<p>Ram: " + mem() + "</p>").encode())
        s.wfile.write(("<p>Version: " + sysversion() + "</p>").encode())
        s.wfile.write(("<p>Executing processes: "
                      + proc_list() + "</p>").encode())

        # If someone went to "http://something.somewhere.net/foo/bar/",
        # then s.path equals "/foo/bar/".
        s.wfile.write(f"<p>You accessed path: {s.path}</p>".encode())
        s.wfile.write("</body></html>".encode())


if __name__ == '__main__':
    httpd = HTTPServer((HOST_NAME, PORT_NUMBER), MyHandler)
    print("Server Starts - %s:%s" % (HOST_NAME, PORT_NUMBER))
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    httpd.server_close()
    print("Server Stops - %s:%s" % (HOST_NAME, PORT_NUMBER))
