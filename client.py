#client.py
import socket
import  cPickle as pickle

import os

import time

SESSION_BEGIN = 0
SESSION_IN_PROGRESS = 1
SESSION_COMPLETE = 2

#messages for detecting acks or nacks
ACK_CHUNK = 1
NACK_CHUNK = 2
ACK_FILE = 3
NACK_FILE = 4

TIMES = 0 #the intial value of the number of chunks sent
FILE_SIZE = None
CHUNK_SIZE = 500 #bytes

FILENAME = "SampleTextFile_500kb.txt"

BLOCKING_MODE = 0
TIMEOUT = 1.0



HOST = '10.0.0.3'    # The remote host
#HOST = 'localhost'    # For testing on localhost
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

start = time.time()
with open(FILENAME) as f:
    while True:
        if read_from_file:
            chunk = f.read(CHUNK_SIZE)
        data['data'] = chunk
        #print chunk
        if chunk == "":
            sending = False
            receiving = False
            try:
                data['message_type'] = SESSION_COMPLETE
                data['times'] = TIMES
                print "Sending chunk of size {0}".format(CHUNK_SIZE)
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
                end = time.time()
                print "File of size {0} bytes correctly transferred in {1} milliseconds.".format(FILE_SIZE,end-start)
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
                    print "Sending chunk of size {0}".format(CHUNK_SIZE)
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
                    #print 'Received', repr(got)
                    
                    if got['message_type'] == SESSION_BEGIN or got['message_type'] == SESSION_IN_PROGRESS:
                        if got['chunk_ack'] == NACK_CHUNK:
                            #dont read from the file
                            read_from_file = False
                            print " NACK "
                        else:
                            TIMES = TIMES + 1
                            print " ACK "
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