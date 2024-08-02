import json
import socket
import glob

# Create a UDP socket
port = 53
ip = "127.0.0.1"

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((ip, port))


def load_zones():
    json_zone = {}
    zone_files = glob.glob('zones/*zone')

    for zone in zone_files:
        with open(zone) as z:
            data = json.load(z)
            zone_name = data["$origin"]
            json_zone[zone_name] = data
    return json_zone


zone_data = load_zones()


def get_flags(flags):
    byte1 = flags[0]
    QR = '1'
    opcode = ''.join([str((byte1 >> bit) & 1) for bit in range(1, 5)])
    AA = '1'
    TC = '0'
    RD = '0'
    RA = '0'
    Z = '000'
    RCODE = '0000'
    return int(QR + opcode + AA + TC + RD, 2).to_bytes(1, byteorder='big') + int(RA + Z + RCODE, 2).to_bytes(1, byteorder='big')


def get_question_domain(data):
    state = 0
    expectedlength = 0
    domainstring = ''
    domainparts = []
    x = 0
    y = 0
    for byte in data:
        if state == 1:
            if byte != 0:
                domainstring += chr(byte)
            x += 1
            if x == expectedlength:
                domainparts.append(domainstring)
                domainstring = ''
                state = 0
                x = 0
            if byte == 0:
                domainparts.append(domainstring)
                break
        else:
            state = 1
            expectedlength = byte
        y += 1

    questiontype = data[y:y+2]
    return domainparts, questiontype


def get_zone(domain):
    zone_name = '.'.join(domain)
    return zone_data[zone_name]


def get_recs(data):
    domain, question_type = get_question_domain(data)
    qtype = 'a' if question_type == b'\x00\x01' else ''
    zone = get_zone(domain)
    return zone[qtype], qtype, domain


def build_question(domain_name, rectype):
    qbytes = b''.join([bytes([len(part)]) + part.encode() for part in domain_name])
    if rectype == 'a':
        qbytes += (1).to_bytes(2, byteorder='big')
    qbytes += (1).to_bytes(2, byteorder='big')
    return qbytes


def rec_to_bytes(domain_name, rec_type, ttl, value):
    rbytes = b'\xc0\x0c'
    if rec_type == 'a':
        rbytes += (1).to_bytes(2, byteorder='big')
    rbytes += (1).to_bytes(2, byteorder='big')
    rbytes += int(ttl).to_bytes(4, byteorder='big')
    if rec_type == 'a':
        rbytes += (4).to_bytes(2, byteorder='big')
        rbytes += b''.join([int(part).to_bytes(1, byteorder='big') for part in value.split('.')])
    return rbytes


def build_response(data):
    transaction_id = data[:2]
    flags = get_flags(data[2:4])
    QDCOUNT = b'\x00\x01'
    ANCOUNTS = len(get_recs(data[12:])).to_bytes(2, byteorder='big')
    NSCOUNT = (0).to_bytes(2, byteorder='big')
    ARCOUNT = (0).to_bytes(2, byteorder='big')

    dns_header = transaction_id + flags + QDCOUNT + ANCOUNTS + NSCOUNT + ARCOUNT

    dns_body = b''
    records, rec_type, domain_name = get_recs(data[12:])
    dns_question = build_question(domain_name, rec_type)
    for record in records:
        dns_body += rec_to_bytes(domain_name, rec_type, record["ttl"], record["value"])
    return dns_header + dns_question + dns_body


while True:
    data, addr = sock.recvfrom(512)
    r = build_response(data)
    sock.sendto(r, addr)