# tcp-offloader
_A TCP client-server program that sends a file over intermittent mobile connectivity robustly and efficiently_

## How to run the application
1. Clone this program.
2. If you are using Mininet-wifi simulator go to `~CM/`
3. Run `sudo python base_scenario.py`
4. Then run `xterm sta1` to open the client terminal
5. Run `xterm h1` to open the server terminal
6. Run `sudo python server.py` on the server terminal
7. Run `sudo python client.py` on the client terminal
8. You will see the data being transferred.
9. To changed the `file_size`, `chunk_size` and `timeout open client.py` and change the corresponding values.

Otherwise
1. Run `sudo python server.py` and `sudo python client.py` in two different terminals to see the file transfer.

## Design Description
The protocol requires us to develop an application such that the file transfer happens between the server h1 and the client sta1 such that in loss of connection the file transfer does not cancel out, but start from the point where it is stopped when the connectivity was lost. (The h1 will referred to as the server in this document and the sta1 will be referred to as the client.)
Therefore, we made the decision that chunks of the file shall be transferred over TCP sockets and each chunk getting acknowledged back from the server to the client, and only then is the next chunk sent over to the server. The chunk size is variable and therefore we call it chunk_size. 

The client runs non-blocking sockets with a variable amount of timeout which we call timeout. Once the timeout runs out, the client starts to send the same chunk again. On the server side the TCP server socket is blocking and has no time out. We have made this decision because the server h1 is stationary and does not move, so the timeouts should only work on the clients. 
Hence by these decisions we have made all the logic that is responsible for correctly transferring the file on the client (sta1), while the server(h1) only sends the ACKs back for every chunk.
Once the whole file is transferred the server sends an ack back for the whole file and hence the client knows that the file transfer is complete. After the file transfer is successfully complete the client and the server terminated successfully.

## Description of the final implementation
Each message from the client and the server is sent as a dictionary that is ‘pickled’ i.e. serialized and de-serialized on the server side.
_Note: the clients reads the data from ‘SampleTextFile_xkb.txt’ and the server stores the data in ‘my_file_server.txt’.
Here xkb refers to the file_size done in experiment. The text files were taken from http://www.sample-videos.com/download-sample-text-file.php_

### The `SESSION_BEGIN`: starting of a session of file transfer
The client initiates a file transfer session to the server. On the client side this is what the TCP payload i.e. mesage looks like when a client wishes to initiate a file transfer session:
`{'data': 'T', 'file_size': 15, 'message_type': 0, 'chunk_size': 1, 'times': 1}`
`data:` Here data refers to the physical chunk that is being sent to the server.
`file_size:` this refers to the total file_size that is being sent over this session. This file_size is redundantly sent in all the messages from the client to the server, not just in the initiating messages. If this is inconsistent for one complete session, the server will return an error and the file transfer will have to start again. We will discuss how the server responds with such an error.
`message_type`: refers to the type of the message that is being sent from the client to the server. In reply to every message_type the server just adds the same message_type that it has received from the client. There are three kinds of message_types in our implementation.

    0: refers to the beginning of the session. It is referred to as SESSION_BEGIN in our implementation.
    1: refers to the progress of the session. It is referred to as SESSION_IN_PROGRESS in our implementation. This means that once this message is sent, the client assumes that the SESSION_BEGIN message has already been sent to the server and acknowledged by the server.
    2: refers to the end of the session. It is referred to as SESSION_END in our implementation. This means that all the data has been successfully transferred and the client is signalling to the server that for one file time, check whether or not the correct file has been transferred. This is the only message from the client to which the server replies with ACK_FILE message back which means that the whole file has been transferred successfully and now the whole server and the client can successfully terminate.
    
_Note: for simplicity we have determined that the server and the client receive and transfer only one file and then terminate. The multi-threading and scalability approach has therefore not been implemented._

`chunk_size`: is the size of the chunk that is transferred with one single message. Just like file size if this is inconsistent throughout the transfer process, the server will return an error and the transfer will start all over again.

`times`: is the size of the chunk that is transferred with one single message. Just like file size if this is inconsistent throughout the transfer process, the server will return an error and the transfer will start all over again. With every acknowledgement the client and the server increment their times variable which means that the next chunk is to be read and transferred from the file.

_Note: the first chunk is transferred with the SESSION_BEGIN message and not after it._

To the SESSION_BEGIN message from the client the server responds as such:
`{'chunk_ack': 1, 'message_type': 0, 'file_ack': 4, 'file_size': 15}`
`chunk_ack` or 1: is the acknowledge of this chunk that the client has sent. A 0 value would mean a chunk_nack which means that the chunk would have to be sent again from the client. The chunk_nack would suggest that the client should not read another chunk from the file and the times variable on the client should not be incremented.

`message_type`: is the same as the message_type sent from the client to which this server’s message is a reply to. This is just to indicate to the client that to which type of message is this message a reply to.

`file_ack`: is the message which tells the client whether or not this particular chunk has been acked or not, the whole file has not yet been transferred and the server expects further chunks until the file is transferred.

`file_size`: is a redundant reply to the client just to make the client know that the server is expecting a total file_size of 15 bytes in this session.

### The SESSION_IN_PROGRESS: transferring the chunks
The previous section explained in detail how a session initiation and a response look like. Once the initiation is done and successfully acknowledged by the server the client reads further chunks from the file and transfers them to the server. Each time incrementing the times variable and waiting for the acknowledgments from the client.
Here is a sample chain of SESSION_IN_PROGRESS messages from the client to the server.
```
{'data': 'T', 'file_size': 15, 'message_type': 0, 'chunk_size': 1, 'times': 1}
...
{'data': 'h', 'file_size': 15, 'message_type': 1, 'chunk_size': 1, 'times': 2}
...
{'data': 'i', 'file_size': 15, 'message_type': 1, 'chunk_size': 1, 'times': 3}
…
```
 
And so on. The first message is the `SESSION_BEGIN` message since message_type is 0. The second, third and further messages would be `message_type` 1 i.e. `SESSION_IN_PROGRESS` messages until all the chunks are sent. The `SESSION_IN_PROGRESS` messages receive a similar response as `SESSION_BEGIN` messages, from the server other than the fact that message_type is 1 rather than 0.
This is a sample response.
 
`{'chunk_ack': 1, 'message_type': 1, 'file_ack': 4, 'file_size': 15}`
 
You can see here that message_type message is changed to 1 rather than 0.
The `SESSION_END` message: signalling the end of transfer
The last type of message that the client sends to the server is the `SESSION_END` message which is sent to the server is upon completion a file transfer. The client sends message_type to be 2 which means that this is an end of a file transfer and that the client is receiving the final acknowledgement of the complete file transfer from the server with `file_ack` to be finally 3 which means that the complete file is transferred.

Here is a sample request and a response from the server regarding the completed file transfer.
Client request:  `{'data': '', 'file_size': 15, 'message_type': 2, 'chunk_size': 1, 'times': 16}`
Server response: `{'message_type': 2, 'file_ack': 3, 'file_size': 15}`
 
Once the client sends the request the server checks the total file size of `my_file_server.txt` to be 15 bytes in this case. If the file transfer is correct the server responds with the `file_ack` = 3 message. Otherwise it responds with a `file _ack` = 4 message. If the `message_type` = 2 (file transfer complete) and the server response is file `file_ack` = 4 (incorrect file transfer) then the file transfer begins again.
 
Incorrect file transfer server response: `{'message_type': 2, 'file_ack': 4, 'file_size': 15}`