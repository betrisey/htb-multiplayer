FROM debian:bookworm-slim

### Install production packages
RUN apt-get update --fix-missing \
    && apt-get -y upgrade \
    && apt-get -y install \
    libxml2 libxml2-dev libxslt-dev locate gnupg \
    libreadline6-dev libcurl4-openssl-dev git-core \
    libssl-dev libyaml-dev openssl autoconf libtool \
    ncurses-dev bison curl xsel postgresql \
    postgresql-contrib postgresql-client libpq-dev \
    curl libapr1 libaprutil1 libsvn1 \
    libpcap-dev libsqlite3-dev libgmp3-dev \
    nasm

### Install MSF for stager generation
RUN curl https://raw.githubusercontent.com/rapid7/metasploit-omnibus/master/config/templates/metasploit-framework-wrappers/msfupdate.erb > msfinstall \
    && chmod 755 msfinstall \
    && ./msfinstall \
    && mkdir -p ~/.msf4/ \
    && touch ~/.msf4/initial_setup_complete 

### Add sliver user
RUN mkdir -p ~/.msf4/ && touch ~/.msf4/initial_setup_complete

### Copy compiled binary
USER root
RUN curl -o /opt/sliver-server -L https://github.com/BishopFox/sliver/releases/latest/download/sliver-server_linux && chmod +x /opt/sliver-server

RUN apt-get install -y openvpn ssh iproute2 python3 python3-pip socat lsof
RUN mkdir /run/sshd
RUN sed -i 's/#PermitRootLogin prohibit-password/PermitRootLogin yes/' /etc/ssh/sshd_config

### Unpack Sliver:
RUN /opt/sliver-server unpack --force

COPY ./run.sh /root/
RUN chmod +x /root/run.sh

RUN pip3 install --break-system-packages Flask==3.0.3 sshpubkeys==3.3.1
# RUN COPY ./web /web

WORKDIR /root/
VOLUME [ "/root/.sliver" ]
ENTRYPOINT [ "/root/run.sh" ]