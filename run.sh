#!/bin/bash
openvpn --config /pro_labs.ovpn &

/opt/sliver-server daemon -p 31337
