#!/bin/bash
echo "root:$ROOT_PASSWORD" | chpasswd
/usr/sbin/sshd -D &
openvpn --config /pro_labs.ovpn &

/opt/sliver-server daemon -p 31337 &

(cd /web && python3 app.py &)

# Keep container running
tail -f /dev/null
