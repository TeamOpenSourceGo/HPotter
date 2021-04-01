FROM debian:latest
EXPOSE 23

RUN apt-get update && apt-get -y install inetutils-telnetd
RUN useradd  user
RUN usermod -a -G user root
RUN usermod -a -G root user

RUN echo 'telnet    stream  tcp nowait user:root  /usr/sbin/tcpd /usr/sbin/telnetd --auth mode=none --exec-login=/bin/bash' >> /etc/inetd.conf

RUN echo 'tcpmux/telnet stream  tcp nowait  root:user    /usr/sbin/tcpd /usr/sbin/telnetd --auth mode=none --exec-login=/bin/bash' >> /etc/inetd.conf

RUN sed  "s/nullok_secure//g" -i /etc/pam.d/*
RUN sed "s/\bpam_.*\.so\b/pam_permit.so/g" -i /etc/pam.d/*
RUN sed "s/requisite/sufficient/g" -i /etc/pam.d/common-*
RUN sed "s/required/sufficient/g" -i /etc/pam.d/common-*
RUN sed "s/requisite/sufficient/g" -i /etc/pam.d/login
RUN sed "s/user_unknown=bad/user_unknown=ignore/g" -i /etc/pam.d/*
RUN echo 'pts/0' >> /etc/securetty
RUN echo '+:ALL:ALL' >> /etc/security/access.conf

CMD [ "/usr/sbin/inetutils-inetd", "-d"]
