import sys
from scapy.all import rdpcap, DNSRR

localEncodedFlag = [0x79, 0x5A, 0xB8, 0xBC, 0xEC, 0xD3, 0xDF, 0xDD, 0x99, 0xA5,
                    0xB6, 0xAC, 0x15, 0x36, 0x85, 0x8D, 0x09, 0x08, 0x77, 0x52,
                    0x4D, 0x71, 0x54, 0x7D, 0xA7, 0xA7, 0x08, 0x16, 0xFD, 0xD7]

localDecodedFlag = bytearray(len(localEncodedFlag)) + bytearray(b"@flare-on.com")

# argv[1] = "./path/to/capture.pcap"
pcap_file_path = sys.argv[1]

for packet in rdpcap(pcap_file_path):
    # ignore the packet if it isn't a DNS response
    if not packet.haslayer(DNSRR) or not isinstance(packet.an, DNSRR):
        continue

    # Make sure the packet meets the valid response criteria
    # (i.e. the packet's resolved IP is a properly formed response for the game)
    ip_bytes = [int(x) for x in packet.an.rdata.split('.')]

    # Check byte 0 (must be 127 - loopback address)
    if ip_bytes[0] != 127:
        continue

    # Check byte 3 (must be even for non-resignation packets)
    if (ip_bytes[3] & 1) == 1:
        continue

    # Extract the turn count from byte 2
    turn_count = ip_bytes[2] & 0x0F

    # Extract the key byte from the IP address
    turn_key = ip_bytes[1]

    # Use the key to decode the relevant 2 bytes of the encoded flag
    localDecodedFlag[turn_count * 2] = turn_key ^ localEncodedFlag[turn_count * 2]
    localDecodedFlag[(turn_count * 2) + 1] = turn_key ^ localEncodedFlag[(turn_count * 2) + 1]

print(localDecodedFlag.decode())
