FROM ubuntu/squid:latest

RUN mkdir -p /var/log/squid && chown -R proxy:proxy /var/log/squid

COPY squid.conf /etc/squid/squid.conf
COPY domains.txt /etc/squid/domains.txt