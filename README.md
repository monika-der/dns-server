# DNS Server

This project implements a simple DNS server in Python. The server listens for DNS queries on port 53 and responds with the appropriate DNS records based on the zone files provided.

## Prerequisites

- Python 3.x
- `sudo` privileges to run the server on port 53

## Setup

1. Ensure you have Python 3 installed on your system.
2. Place your DNS zone files in a directory named `zones`. Each zone file should be in JSON format and contain the necessary DNS records.

## Running the Server

To start the DNS server, open a terminal and run the following command:

```sh
sudo python3 dns_server.py
```

## Testing the Server
To test the DNS server, open another terminal and use the dig command to query the server. For example:

```sh
dig howcode.org @127.0.0.1
```
This command queries the DNS server running on 127.0.0.1 for the domain howcode.org
