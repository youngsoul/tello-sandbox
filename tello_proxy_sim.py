#!/usr/bin/env python

"""
Tello proxy and simulator

Script can act as a standalone simulator for the Tello Drone.  Most command just return ok or a default value.
The format of the method to handle a command is:  _<command> with any '?' removed.

Proxy
Script will receive commands from a driver client, print the data, then forward the command onto to the dst
IP:Port which would typically be the Tello

Simulator TODO:
* Video

Proxy TODO:
* Video


"""
from prettytable import PrettyTable
import argparse
import signal
import logging
import socket


def _command(data):
    return b'OK'


def _battery(data):
    return b'72'


def _speed(data):
    return b'40'


def _time(data):
    return b'100'


def _wifi(data):
    return b'snr'


def _sdk(data):
    return b'2.0'


def _sn(data):
    return b'tello sn'


def _default_ok(data):
    return b'OK'


def tello_simulator(data):
    LOGGER.info(f"Incoming -> {data}")
    command = data.decode('utf-8')
    command = "_" + command.replace('?', '')
    if command in globals().keys():
        response = globals()[command](data)
    else:
        response = _default_ok(data)

    LOGGER.info(f"\tResponse <- {response}")
    return response


FORMAT = '%(asctime)-15s %(levelname)-10s %(message)s'
logging.basicConfig(format=FORMAT)
LOGGER = logging.getLogger()

BUFFER_SIZE = 2 ** 10  # 1024. Keep buffer size as power of 2.

proxy_socket = None

command_response_table = None


def signal_handler(sig, frame):
    print("Signal Handler")
    if proxy_socket is not None:
        proxy_socket.close()

    if command_response_table:
        print(command_response_table)


def simulate_tello(src):
    global proxy_socket
    LOGGER.debug('Starting UDP proxy...')
    LOGGER.debug('Src: {}'.format(src))

    proxy_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    proxy_socket.bind(ip_to_tuple(src))

    client_address = None

    LOGGER.debug('Looping proxy (press Ctrl-Break to stop)...')
    while True:
        cmd_data, address = proxy_socket.recvfrom(BUFFER_SIZE)

        if client_address == None:
            client_address = address

        if address == client_address:
            rsp_data = tello_simulator(cmd_data)
            proxy_socket.sendto(rsp_data, client_address)
        else:
            LOGGER.warning('Unknown address: {}'.format(str(address)))

        if command_response_table:
            command_response_table.add_row([cmd_data, rsp_data])


def udp_proxy(src, dst):
    global proxy_socket
    """Run UDP proxy.

    Arguments:
    src -- Source IP address and port string. I.e.: '127.0.0.1:8000'
    dst -- Destination IP address and port. I.e.: '127.0.0.1:8888'
    """
    LOGGER.debug('Starting UDP proxy...')
    LOGGER.debug('Src: {}'.format(src))
    LOGGER.debug('Dst: {}'.format(dst))

    proxy_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    proxy_socket.bind(ip_to_tuple(src))

    client_address = None
    server_address = ip_to_tuple(dst) if dst is not None else None

    LOGGER.debug('Looping proxy (press Ctrl-Break to stop)...')
    while True:
        cmd_data, client_address = proxy_socket.recvfrom(BUFFER_SIZE)

        LOGGER.info(f"From Client -> {cmd_data}")

        proxy_socket.sendto(cmd_data, server_address)

        rsp_data, server_address = proxy_socket.recvfrom(BUFFER_SIZE)

        LOGGER.info(f"\t\tFrom Tello -> {rsp_data}")

        proxy_socket.sendto(rsp_data, client_address)

        if command_response_table:
            command_response_table.add_row([cmd_data, rsp_data])


# end-of-function udp_proxy


def ip_to_tuple(ip):
    """Parse IP string and return (ip, port) tuple.

    Arguments:
    ip -- IP address:port string. I.e.: '127.0.0.1:8000'.
    """
    ip, port = ip.split(':')
    return (ip, int(port))


# end-of-function ip_to_tuple


def main():
    global command_response_table
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    """Main method."""
    parser = argparse.ArgumentParser(description='TCP/UPD proxy.')

    # TCP UPD groups
    proto_group = parser.add_mutually_exclusive_group(required=True)
    proto_group.add_argument('--proxy', action='store_true', help='UDP proxy')
    proto_group.add_argument('--sim', action='store_true', help='Simulate Tello')

    parser.add_argument('-s', '--src', required=True, help='Source IP and port, i.e.: 127.0.0.1:8000')
    parser.add_argument('-d', '--dst', required=False, help='Destination IP and port, i.e.: 127.0.0.1:8888')

    parser.add_argument('--remember', action='store_true', help='remember the command / response sequence')

    output_group = parser.add_mutually_exclusive_group()
    output_group.add_argument('-q', '--quiet', action='store_true', help='Be quiet')
    output_group.add_argument('-v', '--verbose', action='store_true', help='Be loud')
    output_group.add_argument('-i', '--info', action='store_true', help='Show only important information')

    args = parser.parse_args()

    if args.quiet:
        LOGGER.setLevel(logging.CRITICAL)
    if args.verbose:
        LOGGER.setLevel(logging.NOTSET)
    if args.info:
        LOGGER.setLevel(logging.INFO)

    if args.remember:
        command_response_table = PrettyTable(['Command', 'Response'])

    if args.proxy:
        if args.dst is None:
            raise ValueError("If UDP Proxy, destination IP and Port cannot be empty")
        udp_proxy(args.src, args.dst)
    elif args.sim:
        simulate_tello(args.src)


# end-of-function main


if __name__ == '__main__':
    main()
