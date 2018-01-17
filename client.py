#client.py
import socket
import  cPickle as pickle

import os

SESSION_BEGIN = 0
SESSION_IN_PROGRESS = 1
SESSION_COMPLETE = 2

#messages for detecting acks or nacks
ACK_CHUNK = 1
NACK_CHUNK = 2
ACK_FILE = 3
NACK_FILE = 4

TIMES = 0
FILE_SIZE = None
CHUNK_SIZE = 1

FILENAME = "my_file.txt"

BLOCKING_MODE = 0
TIMEOUT = 5.0



HOST = 'localhost'    # The remote host
PORT = 6000           # The same port as used by the server
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((HOST, PORT))
s.setblocking(BLOCKING_MODE)
s.settimeout(TIMEOUT)


#defining flags for sending and receiving
sending = True
receiving = False

#getting the size of the file
statinfo = os.stat(FILENAME)
FILE_SIZE = statinfo.st_size

#a flag to read from the file in case there are no errors
read_from_file = True

#chunk is the variable that holds the data of every chunk read from the file
chunk = ""


#define the data
TIMES = 1
data = {'message_type': SESSION_BEGIN, 'times': TIMES, 'file_size': FILE_SIZE, 'chunk_size': CHUNK_SIZE, 'data':""}

with open(FILENAME) as f:
    while True:
        if read_from_file:
            chunk = f.read(CHUNK_SIZE)
        data['data'] = chunk
        print chunk
        if chunk == "":
            sending = False
            receiving = False
            print "EOF reached, check data on server side"
            try:
                data['message_type'] = SESSION_COMPLETE
                data['times'] = TIMES
                s.sendall(pickle.dumps(data))
            except socket.timeout:
                print "Oops: timeout trying receiving again"
                continue
            except:
                print "Oops: Socket error"
                continue
                
            try:
                got = s.recv(1024)
                print 'Received', repr(pickle.loads(got))
                break
            except socket.timeout:
                print "Oops: timeout trying receiving again"
                continue
            except:
                print "Oops: Socket error"
                continue
        else:
            #sending data
            while(sending):
                try:
                    if(TIMES != 1):
                        data['message_type'] = SESSION_IN_PROGRESS
                        data['times'] = TIMES   
                    #print data
                    s.sendall(pickle.dumps(data))
                    sending = False
                    receiving = True
                except socket.timeout:
                    print "Oops: timeout trying sending again"
                    sending = True
                    receiving = False
                except:
                    print "Oops: Socket Error"
                    sending = False
                    receiving = False

            #receiving data
            while(receiving):
                try:
                    got = pickle.loads(s.recv(1024))
                    print 'Received', repr(got)
                    
                    if got['message_type'] == SESSION_BEGIN or got['message_type'] == SESSION_IN_PROGRESS:
                        if got['chunk_ack'] == NACK_CHUNK:
                            #dont read from the file
                            read_from_file = False
                        else:
                            TIMES = TIMES + 1
                    elif got['message_type'] == SESSION_COMPLETE:
                        if got['file_ack'] == NACK_FILE:
                            #dont read from the file, start from beginning
                            read_from_file = True
                            TIMES = 1
                            data['message_type'] = SESSION_BEGIN
                        else:
                            TIMES = TIMES + 1
                    else:
                        #dont read from the file start from beginning
                        read_from_file = True
                        TIMES = 1
                        data['message_type'] = SESSION_BEGIN
                    receiving = False
                    sending = True
                except socket.timeout:
                    print "Oops: timeout trying receiving again"
                    receiving = True
                    sending = False
                except:
                    print "Oops: Socket error"
                    receiving = False
                    sending = False




#print pickle.loads(data)
s.close()