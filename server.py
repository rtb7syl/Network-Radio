import socket,multiprocessing,threading,wave,json

import pyaudio

def handle_client(conn,address,conn_queue,clients_no,lock):
    data = conn.recv(2048)
    print('data',data)

    if data:

        msg = json.loads(data.decode())

        station_no = int(msg['station_no'])
        client_udp_port = int(msg['udp_port'])

        print('station_no',station_no)
        print('client_udp_port',client_udp_port)

        client_udp_addr = (address[0],client_udp_port) 

        conn_queue.put(client_udp_addr)
        #print('conn_queue',len(conn_queue))

        with lock:
            clients_no.value += 1
            
            print('clients_no',clients_no.value)



    #conn.close()

def tcp_server(conn_queue,clients_no,lock):
    
    print("Starting TCP server...")

    #host = socket.gethostbyname(socket.gethostname())
    host ='localhost'
    port = 5000
    
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind((host, port))

    print('TCP Server hosting on -> '+str(host)+':'+str(port))

    s.listen()

    while True:
        
        (conn, address) = s.accept()
        
        t = threading.Thread(target=handle_client, args=(conn, address, conn_queue,clients_no,lock))
        
        t.start()






def stream_audio(CHUNK,thread_lock,clients_no):

    print('Streaming within server')

    global curr_fp_posn

    wf = wave.open('cello.wav', 'rb')
    wf.rewind()
    print('current pos within ',curr_fp_posn)
    


    while True:

        #print('clients_no.value within',clients_no.value)
        #print('current pos within ',curr_fp_posn)

        if (clients_no.value == 0):

            wf.setpos(curr_fp_posn)
            #print('current pos within ',curr_fp_posn)

            data = wf.readframes(CHUNK)
            #print(len(data))
            #print('data',data)            
            if (data == ''.encode()):
                
                wf.rewind()
                #break

            pos = wf.tell()
            #print('pos',pos)

            with thread_lock:

                curr_fp_posn = pos


def stream_to_client(s,client_udp_addr,CHUNK,thread_lock,clients_no,lock):

    print('Streaming to client ',client_udp_addr)

    global curr_fp_posn

    wf = wave.open('cello.wav', 'rb')
    
    #p = pyaudio.PyAudio()

    # open stream (2)
    '''
    stream = p.open(format=p.get_format_from_width(wf.getsampwidth()),
                channels=wf.getnchannels(),
                rate=wf.getframerate(),
                output=True)
    '''
    
    print('current pos client ',curr_fp_posn)
    wf.setpos(curr_fp_posn)

    initial_pos = wf.tell()

    data = wf.readframes(CHUNK)

    if (data == ''.encode()):
        
        wf.rewind()

    else:
        wf.setpos(initial_pos)


    i = 0

    while True:

        #print('clients_no.value client',clients_no.value)
        #print('current pos client',curr_fp_posn)

        

        data = wf.readframes(CHUNK)
        #stream.write(data)


        
        s.sendto(data,client_udp_addr)

        if (data == ''.encode()):
            
            with lock:
                clients_no.value = clients_no.value - 1
            
            print('clients_no',clients_no.value)

            print('Streaming to client '+ str(client_udp_addr)+ ' done')

            break

        pos = wf.tell()

        print('len_data,pos,i',len(data),pos,i)
        i += 1
        
        with thread_lock:

            curr_fp_posn = pos

    print('total',i)
    #s.close()
    #stop stream (4)
    #stream.stop_stream()
    #stream.close()

    #close PyAudio (5)
    #p.terminate()



def udp_server(conn_queue,clients_no,lock):

    print("Starting UDP server...")

    #host = socket.gethostbyname(socket.gethostname())
    #port = 12345
    
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    #s.bind((host, port))

    #print('UDP Server hosting on -> '+str(host)+':'+str(port))

    CHUNK = 1024
    global curr_fp_posn
    curr_fp_posn = 0

    thread_lock = threading.Lock()


    threading.Thread(target=stream_audio,args=(CHUNK,thread_lock,clients_no)).start()

    while True:

        client_udp_addr = conn_queue.get()
        print('client_udp_addr',client_udp_addr)

        threading.Thread(target=stream_to_client,args=(s,client_udp_addr,CHUNK,thread_lock,clients_no,lock)).start()








if __name__ == "__main__":

    conn_queue = multiprocessing.Queue()
    clients_no = multiprocessing.Value('i',0)

    lock = multiprocessing.Lock()

    tcp_process = multiprocessing.Process(target=tcp_server,args=(conn_queue,clients_no,lock))
    udp_process = multiprocessing.Process(target=udp_server,args=(conn_queue,clients_no,lock))

    tcp_process.start()
    udp_process.start()
    

