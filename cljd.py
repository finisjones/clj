#!/usr/bin/env python3

import threading 
from time import sleep
from socket import socket as SOCKET, AF_UNIX, SOCK_DGRAM, error as sock_error
from os import path, unlink, getcwd
from inotify_simple import INotify, flags 
import shutil
import difflib
import subprocess
from datetime import datetime

SERVER_ADDR = path.expanduser('~/clj/.run/clj_socket_main')
HISTORY_FILE = path.expanduser('~/.local/share/fish/fish_history')
CLJ_DIR = path.expanduser('~/clj/')

# not used right now
#DAEMON_LOG_FILE = open(path.expanduser('~/clj/.cljd.log'), "a")

STATUS = 'stopped'
JOURNAL_NAME = ''

def sendto_server(data):
    with SOCKET(AF_UNIX, SOCK_DGRAM) as socket:
        try:

            socket.sendto(bytes(data, "utf-8"), SERVER_ADDR)
        except (sock_error) as msg:
            print("server>> ERR::> ", str(msg))
            #shutdown_event.set();

            


def history_watcher(shutdown_event, session_start_event, session_stop_event):
    while(not(shutdown_event.isSet())):
        session_start_event.wait()
        
            
            

        inotify = INotify()
        watch_flags = flags.MODIFY
        shutil.copy(HISTORY_FILE, HISTORY_FILE + "_clj")   
        
        wd = inotify.add_watch(HISTORY_FILE, watch_flags)
        print("IDK")
        while(not(session_stop_event.isSet())):
            print("yada")
            for event in inotify.read():
                dp = subprocess.Popen(['diff', HISTORY_FILE, HISTORY_FILE + '_clj'], \
                                      stdout=subprocess.PIPE)
                gp = subprocess.Popen(['grep', 'cmd'], \
                                      stdin=dp.stdout, \
                                      stdout=subprocess.PIPE)
                dp.stdout.close()
                r_stdout, r_stderr = gp.communicate()
                cmd_ln = r_stdout.decode().split('cmd: ')[1]
                print(cmd_ln)
                
                
                write_journal((("___________________________________________________\n"), \
                             (getcwd() + "> " + cmd_ln), \
                             (datetime.now().strftime("%m/%d/%Y %H:%M:%S") + '\n\n')))
                shutil.copy(HISTORY_FILE, HISTORY_FILE + "_clj")
        sleep(0.1)

def write_journal(data):
    global journal_nowrite_event
    journal_nowrite_event.wait()
    journal_nowrite_event.clear()
    with open(CLJ_DIR + JOURNAL_NAME, 'a') as file:
        if(data == type(()) is str):
            file.write(data)
        elif(data == type(()) is tuple):
            for tup in data:
                file.write(tup)
    journal_nowrite_event.set()


def start_session(journal_name, shutdown_event, session_start_event, session_stop_event):
    global JOURNAL_NAME 
    JOURNAL_NAME = journal_name
    pad = 23 - len(JOURNAL_NAME)
    if(pad < 0):
        pad =0
    j_name = JOURNAL_NAME
    while(pad > 0):
        j_name = j_name + ' '
        pad = pad -  1
    write_journal((("***************************************************\n"),
                  ("***************************************************\n"),
                  ("** Command Line Journal - " + j_name + "**\n"),
                  ("***************************************************\n"),
                  ("***************************************************\n")))
    shutil.copy(HISTORY_FILE, HISTORY_FILE + "_clj")
    
    session_stop_event.clear()
    session_start_event.set()
    return "session_started"

def udp_listener(shutdown_event, session_start_event, session_stop_event):
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
                   data = data.decode().split()
                   if(data[0] == "start"):
                        ret = start_session(data[1], shutdown_event, session_start_event, session_stop_event)
                        sock.sendto(bytes(ret, "utf-8"), address)
                   elif(data[0] == "note"):
                        sock.sendto(bytes('go', "utf-8"), address)
                        data, address = sock.recvfrom(2048)
                        write_journal((("____________________ Note _________________________\n"), \
                                       (str(data)), \
                                       (datetime.now().strftime("%m/%d/%Y %H:%M:%S") + '\n\n')))
                        
                        sock.sendto(bytes('ok', "utf-8"), address)
                   elif(data[0] == "stop"):
                       session_stop_event.set()
                       sleep(0.2)
                       shutdown_event.set()
                       sleep(0.2)
                       sock.sendto(bytes('bye', "utf-8"), address)
                       
               else:
                   break
        finally:
           sock.close()
           pass


journal_nowrite_event = threading.Event()

def main():
    shutdown_event = threading.Event()
    session_start_event = threading.Event()
    session_stop_event = threading.Event()
    global journal_nowrite_event
    journal_nowrite_event.set()

                          
    t_udp_listener = threading.Thread(name="clj-ul", target=udp_listener, args=[shutdown_event, session_start_event, session_stop_event])
    t_udp_listener.start()
    sleep(0.1)
    t_history_watcher = threading.Thread(name="clj-hw", target=history_watcher, args=[shutdown_event, session_start_event, session_stop_event])
    t_history_watcher.start()
    
    shutdown_event.wait()

if __name__ == '__main__':
    main()
