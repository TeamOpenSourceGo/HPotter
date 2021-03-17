FROM debian:latest
EXPOSE 22
RUN apt-get update && apt-get -y install openssh-server && mkdir /var/run/sshd
RUN service ssh restart
RUN echo 'PermitRootLogin yes' >> /etc/ssh/sshd_config
RUN echo 'PermitEmptyPasswords yes' >> /etc/ssh/sshd_config
RUN echo 'PasswordAuthentication yes' >> /etc/ssh/sshd_config
RUN echo 'PubkeyAuthentication  no' >> /etc/ssh/sshd_config
RUN service ssh restart

RUN sed "s/\bpam_.*\.so\b/pam_permit.so/g" -i /etc/pam.d/*
RUN sed  "s/\\[success=1 default=ignore\]\/\[success=2 default=ignore\]//g" -i  /etc/pam.d/common-auth
RUN sed "17 a auth      \[success=1 default=ignore\]        pam_succeed_if.so user = admin" -i /etc/pam.d/common-auth
RUN sed "s/required/sufficient/g" -i /etc/pam.d/*
RUN sed "s/requisite/sufficient/g" -i /etc/pam.d/*
RUN sed  "s/nullok_secure//g" -i /etc/pam.d/*

CMD ["/usr/sbin/sshd","-D"]
