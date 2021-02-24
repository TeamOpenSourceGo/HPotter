FROM debian:latest
EXPOSE 23

RUN apt update && apt -y install inetutils-telnetd
RUN echo 'telnet stream tcp nowait root /usr/sbin/tcpd /usr/sbin/telnetd' >> /etc/inetd.conf
RUN echo 'pts/0' >> /etc/securetty
RUN echo 'pts/1' >> /etc/securetty
RUN echo 'pts/2' >> /etc/securetty
RUN echo 'pts/3' >> /etc/securetty
RUN echo 'pts/4' >> /etc/securetty
RUN echo 'pts/5' >> /etc/securetty
RUN echo 'pts/6' >> /etc/securetty
RUN echo 'pts/7' >> /etc/securetty
RUN echo 'pts/8' >> /etc/securetty
RUN echo 'pts/9' >> /etc/securetty
RUN echo '+:root:ALL' >> /etc/security/access.conf
RUN echo '+:ALL:ALL' >> /etc/security/access.conf
RUN echo 'NO_PASSWORD_CONSOLE' >> /etc/login.defs
RUN sed "s/pam_unix.so/pam_permit.so/g" -i /etc/pam.d/*
RUN sed "s/pam_limits.so/pam_permit.so/g" -i /etc/pam.d/*
RUN sed "s/pam_time.so/pam_permit.so/g" -i /etc/pam.d/*
RUN sed "s/pam_deny.so/pam_permit.so/g" -i /etc/pam.d/*
RUN sed "s/pam_loginuid.so/pam_permit.so/g" -i /etc/pam.d/*
RUN sed "s/pam_nologin.so/pam_permit.so/g" -i /etc/pam.d/*
RUN sed "s/pam_rootok.so/pam_permit.so/g" -i /etc/pam.d/*
RUN sed "s/pam_keyinit.so/pam_permit.so/g" -i /etc/pam.d/*
RUN sed "s/pam_lastlog.so/pam_permit.so/g" -i /etc/pam.d/*
RUN sed "s/pam_shells.so/pam_permit.so/g" -i /etc/pam.d/*
RUN sed "s/pam_env.so/pam_permit.so/g" -i /etc/pam.d/*
RUN sed "s/pam_selinux.so/pam_permit.so/g" -i /etc/pam.d/*
RUN sed "s/pam_systemd.so/pam_permit.so/g" -i /etc/pam.d/*
RUN sed "s/pam_group.so/pam_permit.so/g" -i /etc/pam.d/*
RUN sed "s/pam_securetty.so/pam_permit.so/g" -i /etc/pam.d/*

CMD [ "/usr/sbin/inetutils-inetd","-d"]
