#!/usr/bin/env python3            

import argparse
import subprocess
import editor
from os import kill, path, unlink
from os.path import expanduser
from signal import SIGTERM
from socket import socket as SOCKET, AF_UNIX, SOCK_DGRAM, error as sock_error
from time import sleep



SERVER_ADDR = expanduser('~/clj/.run/clj_socket_main')
CLIENT_ADDR = expanduser('~/clj/.run/clj_socket_clj')

def killDaemon():
    p1 = subprocess.Popen(["ps", "a"], stdout=subprocess.PIPE)
    p2 = subprocess.Popen(["grep", "cljd"], stdin=p1.stdout, stdout=subprocess.PIPE)
    p3 = subprocess.Popen(["grep", "python"], stdin=p2.stdout, stdout=subprocess.PIPE)
    p1.stdout.close()
    p2.stdout.close()
    lines = str(p3.communicate()[0].decode(encoding="utf-8")).splitlines()
    for line in lines:
        pid = int(line.split()[0])
        try:
            kill(pid, SIGTERM)
        except:
            pass

def startDaemon():
    killDaemon()
    subprocess.Popen(["./cljd.py"])

def sendto_server(data):
    ret =""
    #chk client address path and remove it if there
    try:
        unlink(CLIENT_ADDR)
    except OSError:
        if(path.exists(CLIENT_ADDR)):
           raise
        
    with SOCKET(AF_UNIX, SOCK_DGRAM) as socket:
        try:
            socket.bind(CLIENT_ADDR)
            socket.sendto(bytes(data, "utf-8"), SERVER_ADDR)
            ret, address = socket.recvfrom(256)
            
        except (sock_error) as msg:
            print("ERR::> " + str(msg))
            #shutdown_event.set();
    return ret


  
parser = argparse.ArgumentParser("clj")
subparsers = parser.add_subparsers(help='[sub-command] help', dest='cmd')

parser_start = subparsers.add_parser('start', help='Req parameter journal_name')
parser_start.add_argument('journal_name', action='store', type=str)
parser_start

parser_start = subparsers.add_parser('note')
parser_start = subparsers.add_parser('stop')
parser_start = subparsers.add_parser('list')

args = parser.parse_args()
print(args.cmd)
if(args.cmd == 'start'):
    print("\n*** Starting new command line journal '" + args.journal_name + "'. Run 'clj note' to enter notes. Run 'clj stop' to stop. ***\n")
##    startDaemon()
    sleep(0.1)
    data = sendto_server('start ' + args.journal_name)
    print(data)
elif(args.cmd == 'note'):
    note = editor.edit(contents='', use_tty='use_tty')
    
    data = sendto_server('note')
    data = sendto_server(str(note))
    
elif(args.cmd == 'stop'):
    data = sendto_server('stop')
elif(args.cmd == 'list'):
    data = sendto_server('status')
    print("status: ")
    print(data)                                                                                                                                      


