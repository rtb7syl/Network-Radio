import socket,multiprocessing,json,wave,sys
import pyaudio

def tcp_client(station_no,udp_port):


    #host = socket.gethostbyname(socket.gethostname())
    host ='localhost'
    port = 5000

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((host,port))
    print('TCP client up and running')
    msg = {'station_no':station_no,'udp_port':udp_port}

    msg = json.dumps(msg)
    print('msg',msg)

    msg = msg.encode()

    s.sendall(msg)
    s.close()

def udp_client(port):
    wf = wave.open('cello.wav', 'rb')

    #host = socket.gethostbyname(socket.gethostname())
    host ='localhost'
    #port = 12345
    

    print('UDP client up and running -> ',(host,port))
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.bind((host, port))

    CHUNK = 1024
    FORMAT = pyaudio.paInt16 #Audio Codec
    CHANNELS = 2 #Stereo or Mono
    RATE = 44100 #Sampling Rate

    #instantiate PyAudio (1)
    p = pyaudio.PyAudio()

    # open stream (2)
    
    stream = p.open(format=p.get_format_from_width(wf.getsampwidth()),
                channels=wf.getnchannels(),
                rate=wf.getframerate(),
                output=True)



    
    i = 0
    while True:

        data,addr = s.recvfrom(CHUNK)
        
        if data != ''.encode():
            
            print('chunk_id,data_length,addr',i,len(data),addr)
            i +=1
            
            stream.write(data)

        else:

            print('Streaming complete')
            break
    
    print('total_chunks',i)

    
    s.close()
    #stop stream (4)
    stream.stop_stream()
    stream.close()

    #close PyAudio (5)
    p.terminate()
    


if __name__ == "__main__":

    port = int(sys.argv[1])

    tcp_process = multiprocessing.Process(target=tcp_client,args=(0,port))
    udp_process = multiprocessing.Process(target=udp_client,args=(port,))

    tcp_process.start()
    udp_process.start()