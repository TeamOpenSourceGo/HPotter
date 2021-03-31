FROM debian:latest
EXPOSE 22
RUN apt update && apt -y install openssh-server && mkdir /var/run/sshd

RUN echo 'PermitRootLogin yes' >> /etc/ssh/sshd_config
RUN service ssh restart
RUN echo 'root:toor' | chpasswd

CMD ["/usr/sbin/sshd","-D"]