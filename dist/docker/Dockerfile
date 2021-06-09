FROM centos:7
LABEL maintainer="Apex Liu <apex.liu@qq.com>"

ENV TP_VER=3.5.6-rc6


ADD res/teleport-server-linux-x64-$TP_VER.tar.gz /root
ADD res/bootstrap.sh /root

RUN mkdir /usr/local/teleport; \
    mkdir /usr/local/teleport/data; \
    cp -R /root/teleport-server-linux-x64-$TP_VER/data/bin /usr/local/teleport/bin; \
    cp -R /root/teleport-server-linux-x64-$TP_VER/data/www /usr/local/teleport/www; \
    chmod +x /root/bootstrap.sh; \
    rm -rf /etc/localtime; \
    ln -sf /usr/share/zoneinfo/Asia/Shanghai /etc/localtime


CMD ["/bin/bash"]

EXPOSE 7190
EXPOSE 52089
EXPOSE 52189
EXPOSE 52389

ENTRYPOINT ["/root/bootstrap.sh"]
