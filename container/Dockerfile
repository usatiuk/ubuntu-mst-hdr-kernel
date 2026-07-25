FROM ubuntu:26.04

ARG DEBIAN_FRONTEND=noninteractive

RUN sed -i 's/^Types: deb$/Types: deb deb-src/' \
        /etc/apt/sources.list.d/ubuntu.sources \
    && apt-get update \
    && apt-get build-dep -y linux \
    && apt-get install -y --no-install-recommends \
        bc \
        bison \
        build-essential \
        ca-certificates \
        cpio \
        debhelper \
        devscripts \
        dpkg-dev \
        dwarves \
        fakeroot \
        flex \
        git \
        kmod \
        libncurses-dev \
        lintian \
        llvm \
        rsync \
        xz-utils \
        zstd \
    && rm -rf /var/lib/apt/lists/*

RUN mkdir -p /work /tmp/mst-hdr-home \
    && chmod 1777 /work /tmp/mst-hdr-home

ENV DEBIAN_FRONTEND=noninteractive
ENV HOME=/tmp/mst-hdr-home
WORKDIR /work
