'''Take a generator of water column packets and turn it into a generator for congregated water column packets'''
from collections import defaultdict
def congregate(wcd_generator, allow_incomplete = True):
    ping_number_per_head = defaultdict(int)
    sub_packets_per_head = defaultdict(list)
    for packet in wcd_generator:
        serial_number = packet.header['serial_number']
        ping_number = ping_number_per_head[serial_number]
        sub_packets = sub_packets_per_head[serial_number]
        if packet.header['ping_number'] != ping_number:
            if len(sub_packets) > 0:
                ping = sub_packets[0]
                for sub_packet in sub_packets[1:]:
                    ping.beams += sub_packet.beams
                    ping.header['number of bytes in datagram'] += sub_packet.header['number of bytes in datagram']

                if len(ping.beams) == ping.header['total number of receive beams'] or allow_incomplete:
                    yield ping
                else:
                    print('Incomplete ping with number {} only have {} of {} beams'.format(ping_number, len(ping.beams), ping.header['total number of receive beams']))

            sub_packets_per_head[serial_number] = [packet]
            ping_number_per_head[serial_number] = packet.header['ping_number']

        elif packet.header['ping_number'] == ping_number:
            sub_packets_per_head[serial_number].append(packet)


