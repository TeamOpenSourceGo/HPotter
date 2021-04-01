FROM debian:latest
EXPOSE 22

RUN apt update && apt -y install openssh-server && mkdir /var/run/sshd
RUN apt install sudo

RUN service ssh restart
RUN echo 'PermitRootLogin yes' >> /etc/ssh/sshd_config
RUN echo 'PermitEmptyPasswords yes' >> /etc/ssh/sshd_config
RUN echo 'PasswordAuthentication yes' >> /etc/ssh/sshd_config
RUN service ssh restart

RUN echo 'root:toor' | chpasswd

RUN echo '#!/bin/bash' > /setpasswd
RUN echo 'passwd $1 < pass.txt' >> /setpasswd
RUN chmod 764 /setpasswd

CMD ["/usr/sbin/sshd","-D"]