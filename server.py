# Echo server program
import socket
import  cPickle as pickle
import sys

import os

HOST = ''                 # Symbolic name meaning all available interfaces
PORT = 6000             # Arbitrary non-privileged port
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind((HOST, PORT))
s.listen(1)

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
CHUNK_SIZE = None

FILENAME = "my_file_server.txt"
file_data = ""

#deleting the file if it does exist
try:
    os.remove(FILENAME)
except OSError:
    pass

#the file variable
f = None

conn, addr = s.accept()
print 'Connected by', addr
while 1:
    data = conn.recv(1024)
    try:
        u_data = pickle.loads(data)
        if(u_data['message_type'] == SESSION_BEGIN):
            if(u_data['file_size']<u_data['chunk_size']):
                u_data["chunk_ack"] = NACK_CHUNK
                u_data["file_ack"] = NACK_FILE
            else:
                FILE_SIZE = u_data['file_size']
                CHUNK_SIZE = u_data['chunk_size']
                u_data["chunk_ack"] = ACK_CHUNK
                u_data["file_ack"] = NACK_FILE
                TIMES = u_data["times"]
                f= open(FILENAME,"w+")
                f.write(u_data["data"])
                TIMES = TIMES + 1
		print 'Session begins, wrote data of size{0} and acked chunk'.format(CHUNK_SIZE)
        elif(u_data['message_type'] == SESSION_IN_PROGRESS):
            if u_data['file_size']<u_data['chunk_size'] or u_data['file_size']!=FILE_SIZE or u_data['chunk_size']!=CHUNK_SIZE or u_data['times']!=TIMES:
                u_data["chunk_ack"] = NACK_CHUNK
                u_data["file_ack"] = NACK_FILE
            else:
                u_data["chunk_ack"] = ACK_CHUNK
                u_data["file_ack"] = NACK_FILE
                TIMES = TIMES + 1
                f.write(u_data["data"]);
                print 'Received and wrote data of size{0} and acked chunk'.format(CHUNK_SIZE)
        elif(u_data['message_type'] == SESSION_COMPLETE):
            if u_data['file_size']<u_data['chunk_size'] or u_data['file_size']!=FILE_SIZE or u_data['chunk_size']!=CHUNK_SIZE or u_data['times']!=TIMES:
                u_data["chunk_ack"] = NACK_CHUNK
                u_data["file_ack"] = NACK_FILE
            else:
                f.close()
                statinfo = os.stat(FILENAME)
                if(statinfo.st_size != FILE_SIZE):
                    u_data["file_ack"] = NACK_FILE
                else:
                    u_data["file_ack"] = ACK_FILE
		    print 'Session complete, wrote file of size {0} bytes with the name {1}'.format(FILE_SIZE, FILENAME)
                    
        else:
            u_data["chunk_ack"] = NACK_CHUNK
            u_data["file_ack"] = NACK_FILE
        #deleting these 3 values from dict in all messages
        del u_data['times']
        del u_data['chunk_size']
        del u_data['data']
    except EOFError:
        a = 1
        #print "Ignore this error, it does come in unpickling, but does not affect the logic of the program"
    #print 'Received'
    if not data: break
    conn.sendall(pickle.dumps(u_data))
conn.close()