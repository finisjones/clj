#!/usr/bin/env python3

import threading 
from time import sleep
from socket import socket as SOCKET, AF_UNIX, SOCK_DGRAM, error as sock_error
from os import path, unlink
from inotify_simple import INotify, flags 

SERVER_ADDR = path.expanduser('~/clj/.run/clj_socket_main')
HISTORY_FILE = path.expanduser('~/.local/share/fish/fish_history')
DAEMON_LOG_FILE = open(path.expanduser('~/clj/.cljd.log'), "a")



def sendto_server(data):
    with SOCKET(AF_UNIX, SOCK_DGRAM) as socket:
        try:

            socket.sendto(bytes(data, "utf-8"), SERVER_ADDR)
        except (sock_error) as msg:
            print("ERR::> ", str(msg), file=DAEMON_LOG_FILE)
            shutdown_event,set();

            

def history_watcher(shutdown_event):
    inotify = INotify()
    watch_flags = flags.MODIFY;
    
    wd = inotify.add_watch(HISTORY_FILE, watch_flags)
    while(not(shutdown_event.isSet())):
        for event in inotify.read():
            print(event, file=DAEMON_LOG_FILE)
            for flag in flags.from_mask(event.mask):
                print('     ' + str(flag), file=DAEMON_LOG_FILE)
        sleep(0.1)

def udp_listener(shutdown_event):
    #chk server address path and remove it if there
    try:
        unlink(SERVER_ADDR)
    except OSError:
        if(path.exists(SERVER_ADDR)):
           raise
    sock = SOCKET(AF_UNIX, SOCK_DGRAM)
    sock.bind(SERVER_ADDR)
    while(not(shutdown_event.isSet())):
        try:
           while(not(shutdown_event.isSet())):
               data, address = sock.recvfrom(2048)
               if data:
                   print("data from client ", str(address), ": ", str(data), file=DAEMON_LOG_FILE)
               else:
                   break
        finally:
           sock.close()
           pass


     

def main():
    shutdown_event = threading.Event()
    t_udp_listener = threading.Thread(name="clj-ul", target=udp_listener, args=[shutdown_event])
    t_udp_listener.start()
    sleep(5)
    t_history_watcher = threading.Thread(name="clj-hw", target=history_watcher, args=[shutdown_event])
    t_history_watcher.start()
    
    shutdown_event.wait()

if __name__ == '__main__':
    main()
