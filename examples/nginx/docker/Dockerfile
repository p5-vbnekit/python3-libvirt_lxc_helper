ARG base_image=debian:bullseye

FROM ${base_image}

ENV LC_ALL C
ENV DEBIAN_FRONTEND noninteractive

# watch .p5.libvirt_lxc_helper.script.yml
ENV EXAMPLE_A should be inherited
ENV EXAMPLE_B should be inherited
ENV EXAMPLE_C should be removed
ENV EXAMPLE_D should be replaced

RUN rm --force /etc/apt/sources.list
COPY files/etc/apt/sources.list.d/debian.sources /etc/apt/sources.list.d/debian.sources
RUN apt-mark showmanual | xargs --no-run-if-empty -- apt-mark auto --
RUN apt update --assume-yes && apt install --assume-yes apt-utils
RUN apt update --assume-yes && apt full-upgrade --assume-yes

RUN apt purge --assume-yes ifupdown iproute2
RUN rm --force --recursive /etc/network

RUN apt update --assume-yes && apt install --assume-yes systemd systemd-sysv
RUN apt update --assume-yes && apt install --assume-yes nginx

RUN systemctl enable systemd-networkd.service systemd-resolved.service

RUN rm --force /etc/*-

RUN apt update --assume-yes && apt --assume-yes full-upgrade && apt autoremove --assume-yes && apt purge --assume-yes '~c'
RUN apt clean --assume-yes && for _path in /tmp /var/tmp /var/lib/apt/lists; do \
      find "${_path}" -mindepth 1 -maxdepth 1 -exec rm --recursive --force {} \;; \
    done

COPY files/.p5.libvirt_lxc_helper.script.yml .p5.libvirt_lxc_helper.script.yml
LABEL p5.libvirt_lxc_helper.script=.p5.libvirt_lxc_helper.script.yml

ENTRYPOINT ["/sbin/init"]
