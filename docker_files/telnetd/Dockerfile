FROM debian:latest
EXPOSE 23

RUN apt-get update && apt-get -y install inetutils-telnetd
RUN echo 'telnet stream tcp nowait root /usr/sbin/tcpd     /usr/sbin/telnetd' >> /etc/inetd.conf
RUN useradd admin
RUN useradd user
RUN useradd test
RUN useradd ubuntu
RUN useradd oracle
RUN useradd guest
RUN useradd nagios
RUN useradd mysql
RUN useradd tomcat
RUN useradd administrator
RUN useradd Administrator
RUN useradd info
RUN useradd pi
RUN useradd ansible
RUN useradd vagrant
RUN useradd azureuser
RUN useradd demo 
RUN useradd git  
RUN useradd hadoop
RUN useradd ts3  
RUN useradd support
RUN useradd porstgres
RUN useradd ubnt
RUN useradd ftpuser     

RUN sed "s/user_unknown=bad/user_unknown=ignore/g" -i /etc/pam.d/*
RUN sed  "s/nullok_secure//g" -i /etc/pam.d/*
RUN sed "s/\bpam_.*\.so\b/pam_permit.so/g" -i /etc/pam.d/*
RUN sed "s/requisite/sufficient/g" -i /etc/pam.d/common-*
RUN echo 'pts/0' >> /etc/securetty
RUN echo '+:ALL:ALL' >> /etc/security/access.conf

CMD [ "/usr/sbin/inetutils-inetd", "-d"]
