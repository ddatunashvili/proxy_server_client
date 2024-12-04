import select
import socket
import threading
import signal
import sys

config = {
    "HOST_NAME": "0.0.0.0",
    "BIND_PORT": 2001,
    "MAX_REQUEST_LEN": 1024,
    "CONNECTION_TIMEOUT": 5
}

def HTTP_request_he_to_she(http_request):
    try:
        http_request = http_request.decode('utf-8')
    except UnicodeDecodeError:
        return False  
    
    lines = http_request.split('\n')
    index = False
    text = ""
    for i in range(len(lines)):
        if lines[i] == "":
            try:
                index = i + 1
                text = lines[i + 1]
            except IndexError:
                return False

        if "Content-Type: image" in lines[i]:
            return False

    text = text.replace(" he ", " she ")
    print(text)
    if index is not False:
        lines[index] = text
    else:
        return False
    return '\n'.join(lines).encode('utf-8')

class Server:

    def __init__(self, config):
        signal.signal(signal.SIGINT, self.shutdown)  
        self.serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  
        self.serverSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  
        self.serverSocket.bind((config['HOST_NAME'], config['BIND_PORT']))  
        self.serverSocket.listen(10)  
        self.__clients = {}

    def listenForClient(self):
        while True:
            (clientSocket, client_address) = self.serverSocket.accept()  
            d = threading.Thread(name=self._getClientName(client_address), target=self.proxy_thread, args=(clientSocket, client_address))
            d.daemon = True  
            d.start()
        self.shutdown(0, 0)

    def proxy_thread(self, conn, client_addr):
        """
        A thread to handle request from browser
        """

        request_from_browser = conn.recv(config['MAX_REQUEST_LEN'])  
        request_from_proxy = request_from_browser

        try:
            request_from_browser = request_from_browser.decode('utf-8')
        except UnicodeDecodeError:
            print("Failed to decode request from browser")
            conn.close()
            return

        first_line = request_from_browser.split('\n')[0]
        print(first_line[:50])
        try:
            url = first_line.split(' ')[1]
        except IndexError:
            url = ""
        print(url[:50])

        
        if first_line.startswith("CONNECT"):
            target = url.split(':')
            if len(target) == 1:
                target.append('443')  
            host, port = target
            port = int(port)
            try:
                
                conn.send(b'HTTP/1.1 200 Connection Established\r\n\r\n')
                
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(config['CONNECTION_TIMEOUT'])
                s.connect((host, port))

                
                while True:
                    r_list = [conn, s]
                    readable, _, _ = select.select(r_list, [], [])
                    for r in readable:
                        data = r.recv(config['MAX_REQUEST_LEN'])
                        if r is conn:
                            if data:
                                s.sendall(data)
                            else:
                                s.close()
                                conn.close()
                                return
                        elif r is s:
                            if data:
                                conn.sendall(data)
                            else:
                                s.close()
                                conn.close()
                                return
            except socket.error as error_msg:
                print('ERROR: ', client_addr, error_msg)
                if s:
                    s.close()
                if conn:
                    conn.close()

        else:
            
            http_pos = url.find("://")  
            if (http_pos == -1):
                temp = url
            else:
                temp = url[(http_pos + 3):]  

            port_pos = temp.find(":")  

            
            webserver_pos = temp.find("/")
            if webserver_pos == -1:
                webserver_pos = len(temp)

            webserver = ""
            port = -1
            if (port_pos == -1 or webserver_pos < port_pos):  
                port = 80
                webserver = temp[:webserver_pos]
            else:  
                port = int((temp[(port_pos + 1):])[:webserver_pos - port_pos - 1])
                webserver = temp[:port_pos]

            try:
                
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(config['CONNECTION_TIMEOUT'])
                s.connect((webserver, port))
                s.sendall(request_from_proxy)  

                while True:
                    data_from_server = s.recv(config['MAX_REQUEST_LEN'])  
                    if (len(data_from_server) > 0):
                        conn.send(data_from_server)  
                    else:
                        break
                s.close()
                conn.close()
            except socket.error as error_msg:
                print('ERROR: ', client_addr, error_msg)
                if s:
                    s.close()
                if conn:
                    conn.close()


    def _getClientName(self, cli_addr):
        return "Client"

    def shutdown(self, signum, frame):
        self.serverSocket.close()
        sys.exit(0)

if __name__ == "__main__":
    print("the program is starting")
    server = Server(config)
    server.listenForClient()