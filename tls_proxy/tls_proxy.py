import socketserver
import logging
import select
import socket
import ssl

PROXY_PORT = 3241
USBIP_SERVER_PORT = 3240


class ProxyClientDisconnected(Exception):
    pass


class ProxyServerDisconnected(Exception):
    pass


class MyTCPHandler(socketserver.BaseRequestHandler):
    def handle(self):
        logging.info("-------- New proxy connection from {} --------".format(self.client_address[0]))
        self.data: bytes = self.request.recv(20).strip()

        proxy_server_address = self.data.decode(encoding="ascii")
        logging.info(f"proxy_server_address: {proxy_server_address}")

        context = ssl.create_default_context()
        context.check_hostname = False
        # context.verify_mode = ssl.CERT_NONE

        try:
            with socket.create_connection((proxy_server_address, USBIP_SERVER_PORT)) as sock:
                with context.wrap_socket(sock, server_hostname=None) as tls_sock:
                    logging.info(f"Connected to {proxy_server_address}:{USBIP_SERVER_PORT}")

                    self.request.setblocking(False)
                    tls_sock.setblocking(False)

                    while True:
                        read_ready, _, _ = select.select([self.request, tls_sock], [], [], 1)

                        for s in read_ready:

                            if s == self.request:
                                proxy_client_data = self.request.recv(4096 * 4)
                                if proxy_client_data:
                                    # print("client: ", usbip_client_data)
                                    tls_sock.send(proxy_client_data)
                                else:
                                    raise ProxyClientDisconnected

                            if s == tls_sock:
                                try:
                                    proxy_server_data = tls_sock.recv(4096 * 4)
                                    if proxy_server_data:
                                        # print("server: ", usbip_server_data)
                                        self.request.send(proxy_server_data)
                                    else:
                                        raise ProxyServerDisconnected
                                except ssl.SSLWantReadError:
                                    pass

        except socket.gaierror:
            logging.info(f"Failed to resolve {proxy_server_address} name")
        except ConnectionRefusedError:
            logging.info(f"Failed to connect to {proxy_server_address}:{USBIP_SERVER_PORT}. "
                         f"Check if usbipd daemon running on target host")
        except ProxyClientDisconnected:
            logging.info("Proxy client disconnected")
        except ProxyServerDisconnected:
            logging.info("Proxy client disconnected")
        finally:
            logging.info(f"XXXXXXXX Connection with {proxy_server_address} closed XXXXXXXX")


def server_run():
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("localhost", PROXY_PORT), MyTCPHandler) as server:
        server.serve_forever()


def main():
    server_run()


if __name__ == "__main__":
    main()
