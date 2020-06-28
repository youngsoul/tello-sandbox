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
from random import randint

_tello_commands = [
    'command',
    'takeoff',
    'land',
    'streamon',
    'streamoff',
    'emergency',
    'up',
    'down',
    'left',
    'right',
    'forward',
    'back',
    'cw',
    'ccw',
    'flip'
    'go',
    'stop',
    'curve',
    'jump',
    'speed',
    'rc',
    'wifi',
    'mon',
    'moff',
    'mdirection',
    'ap',
    'battery',
    'time',
    'sdk'
    'sn'
]


def _command(data):
    return b'OK'


def _battery_read(data):
    return b'72'


def _speed_read(data):
    return b'40'


def _time_read(data):
    return b'100'


def _wifi_read(data):
    return b'snr'


def _sdk_read(data):
    return b'2.0'


def _sn_read(data):
    return b'tello sn'


def _default_ok(data):
    return b'OK'


def _verify_single_param(data, min, max):
    cmd_values = data.split(" ")
    if len(cmd_values) != 2:
        return b'ERROR'

    if min <= int(cmd_values[1]) <= max:
        return b'OK'
    else:
        return b'ERROR'


def _cw(data):
    return _verify_single_param(data, 1, 360)


def _ccw(data):
    return _verify_single_param(data, 1, 360)


def _up(data):
    return _verify_single_param(data, 20, 500)


def _down(data):
    return _verify_single_param(data, 20, 500)


def _left(data):
    return _verify_single_param(data, 20, 500)


def _right(data):
    return _verify_single_param(data, 20, 500)


def _forward(data):
    return _verify_single_param(data, 20, 500)


def _back(data):
    return _verify_single_param(data, 20, 500)


def _down(data):
    return _verify_single_param(data, 20, 500)


def _speed(data):
    return _verify_single_param(data, 10, 100)


def _go(data):
    """
    go x y z speed
    :param data:
    :type data:
    :return:
    :rtype:
    """
    cmd_values = data.split(" ")
    if len(cmd_values) != 5:
        return b'ERROR'

    if -500 <= int(cmd_values[1]) <= 500 and \
            -500 <= int(cmd_values[2]) <= 500 and \
            -500 <= int(cmd_values[3]) <= 500 and \
            10 <= int(cmd_values[4]) <= 100:
        # there is a note: x,y,z cannot be set between -20-20 simultaneously
        # have no idea why
        if -20 <= int(cmd_values[1]) <= 20 and \
                -20 <= int(cmd_values[2]) <= 20 and \
                -20 <= int(cmd_values[3]) <= 20:
            return b'ERROR'
        else:
            return b'OK'
    else:
        return b'ERROR'

def _curve(data):
    """
    curve x1 y1 z1 x2 y2 z2 speed
    :param data:
    :type data:
    :return:
    :rtype:
    """
    cmd_values = data.split(" ")
    if len(cmd_values) != 8:
        return b'ERROR'

    if -500 <= int(cmd_values[1]) <= 500 and \
            -500 <= int(cmd_values[2]) <= 500 and \
            -500 <= int(cmd_values[3]) <= 500 and \
            -500 <= int(cmd_values[4]) <= 500 and \
            -500 <= int(cmd_values[5]) <= 500 and \
            -500 <= int(cmd_values[6]) <= 500 and \
            10 <= int(cmd_values[7]) <= 60:
        # there is a note: x,y,z cannot be set between -20-20 simultaneously
        # have no idea why
        if -20 <= int(cmd_values[1]) <= 20 and \
                -20 <= int(cmd_values[2]) <= 20 and \
                -20 <= int(cmd_values[3]) <= 20 and \
                -20 <= int(cmd_values[4]) <= 20 and \
                -20 <= int(cmd_values[5]) <= 20 and \
                -20 <= int(cmd_values[6]) <= 20:
            return b'ERROR'
        else:
            return b'OK'
    else:
        return b'ERROR'

def _rc(data):
    """
    rc a b c d
    a = left/right (-100/100)
    b = forward/backward (-100/100)
    c = up/down (-100/100)
    d = yaw (-100/100)

    :param data:
    :type data:
    :return:
    :rtype:
    """
    cmd_values = data.split(" ")
    if len(cmd_values) != 5:
        return b'ERROR'

    if -100 <= int(cmd_values[1]) <= 100 and \
            -100 <= int(cmd_values[2]) <= 100 and \
            -100 <= int(cmd_values[3]) <= 100 and \
            -100 <= int(cmd_values[4]) <= 100:
        return b'OK'
    else:
        return b'ERROR'


def _tello_simulator(data):
    try:
        command_str = data.decode('utf-8')
        command = command_str.replace('?', '_read')
        first_command = command.split(" ")[0]
        if first_command not in _tello_commands:
            return b'ERROR'

        command_function_name = "_" + first_command

        if command_function_name in globals().keys():
            response = globals()[command_function_name](command_str)
        else:
            response = _default_ok(command_str)
    except Exception as exc:
        LOGGER.error(exc)
        response = b'ERROR'

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


def simulate_tello(src, error_rate, no_rsp_rate):
    global proxy_socket
    LOGGER.debug('Starting Tello Simulator...')
    LOGGER.debug('Src: {}'.format(src))

    proxy_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    proxy_socket.bind(ip_to_tuple(src))

    LOGGER.debug('Looping proxy (press Ctrl-Break to stop)...')
    while True:
        cmd_data, client_address = proxy_socket.recvfrom(BUFFER_SIZE)
        LOGGER.info(f"Incoming -> {cmd_data}")

        if no_rsp_rate > 0:
            rand_rsp_rate = randint(1, 100)
            if rand_rsp_rate < no_rsp_rate:
                LOGGER.debug("\tSimulating no response from Tello")
                rsp_data = b'NO RESPONSE'
                if command_response_table:
                    command_response_table.add_row([cmd_data, rsp_data])
                continue

        if error_rate > 0:
            rand_error_rate = randint(1, 100)
            if rand_error_rate <= error_rate:
                rsp_data = b'ERROR'
                proxy_socket.sendto(rsp_data, client_address)
            else:
                rsp_data = _tello_simulator(cmd_data)
                proxy_socket.sendto(rsp_data, client_address)
        else:
            rsp_data = _tello_simulator(cmd_data)
            proxy_socket.sendto(rsp_data, client_address)

        LOGGER.info(f"\tResponse <- {rsp_data}")

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
    parser = argparse.ArgumentParser(description='Tello Simulator/Tello proxy.')

    # SIM Proxy groups
    proto_group = parser.add_mutually_exclusive_group(required=True)
    proto_group.add_argument('--proxy', action='store_true', help='UDP proxy')
    proto_group.add_argument('--sim', action='store_true', help='Simulate Tello')

    parser.add_argument('--sim-no-response-rate', required=False, type=int, default=0,
                        help="Simulated no response from tello rate in percent. Default: 0, Value: 1-100 means the percentage of calls that result in no response. ")
    parser.add_argument('--sim-error-rate', required=False, type=int, default=0,
                        help="Simulated error rate in percent. Default: 0, Value: 1-100 means the percentage of calls that result in an error")

    parser.add_argument('-s', '--src', required=True, help='Source IP and port, i.e.: 127.0.0.1:8000')
    parser.add_argument('-d', '--dst', required=False, help='Destination IP and port, i.e.: 127.0.0.1:8888')

    parser.add_argument('--remember', action='store_true', help='remember the command / response sequence')

    output_group = parser.add_mutually_exclusive_group()
    output_group.add_argument('-q', '--quiet', action='store_true', help='Be quiet')
    output_group.add_argument('-v', '--verbose', action='store_true', help='Be loud')
    output_group.add_argument('-i', '--info', action='store_true', help='Show only important information')

    args = parser.parse_args()

    print(args)

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
        simulate_tello(args.src, args.sim_error_rate, args.sim_no_response_rate)


# end-of-function main


if __name__ == '__main__':
    main()
