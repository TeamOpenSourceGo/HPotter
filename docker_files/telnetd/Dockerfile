FROM debian:latest
EXPOSE 23

RUN apt-get update && apt-get -y install inetutils-telnetd
RUN echo 'telnet stream tcp nowait root /usr/sbin/tcpd     /usr/sbin/telnetd -a none' >> /etc/inetd.conf
RUN sed "s/\bpam_.*\.so\b/pam_permit.so/g" -i /etc/pam.d/*
RUN sed "s/requisite/sufficient/g" -i /etc/pam.d/common-*
RUN echo 'pts/0' >> /etc/securetty
RUN echo '+:ALL:ALL' >> /etc/security/access.conf

CMD [ "/usr/sbin/inetutils-inetd", "-d"]

