### produce oci-image and generate rootfs tar archive
```
podman build --tag=example -- examples/nginx/docker
podman image save --format=oci-archive -- example | p5-libvirt_lxc_helper make-rootfs --destination=rootfs.tar
```
- For producing oci-image you can use `docker`, `podman`, `buildah`, etc ...
- For more options check: `p5-libvirt_lxc_helper --help`

### helper script
  `Dockerfile` instructions do not always lead to the desired result.  
  For example, it is not so easy to replace the contents of `/etc/hosts`.  
  But you can use a special script (`yaml` or `json` config file) - in this example it named as [`.p5.libvirt_lxc_helper.script.yml`](docker/files/.p5.libvirt_lxc_helper.script.yml).  
  It should be marked as `p5.libvirt_lxc_helper.script` `LABEL` in `Dockerfile` like this:
  ```
  LABEL p5.libvirt_lxc_helper.script=.p5.libvirt_lxc_helper.script.yml
  ```
  In this case `.p5.libvirt_lxc_helper.script.yml` is path (relative to container root) to script.  
  Path will be normalized automatically - don't worry about `/`, `./`, etc...  
  For example, there you can do something like this:
  ```
    - command: /bin/sh -xe
      input: |
        rm --force /etc/hostname && echo nginx > /etc/hostname
        rm --force /etc/resolv.conf && ln --symbolic /run/systemd/resolve/stub-resolv.conf /etc/resolv.conf
    
        rm --force /etc/hosts && cat > /etc/hosts << EOF
        127.0.0.1       localhost
    
        # The following lines are desirable for IPv6 capable hosts
        ::1             localhost ip6-localhost ip6-loopback
        ff02::1         ip6-allnodes
        ff02::2         ip6-allrouters
    
        ::1             nginx
        127.0.0.1       nginx
        EOF
  ```
