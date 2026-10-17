# Ubuntu Intel MST HDR kernel

Experimental Ubuntu 26.04 **amd64** kernel adding Intel HDR and VRR over
DisplayPort MST, including 10-bit color where hardware and bandwidth allow.
Installs alongside the stock Ubuntu kernel.

**Before installing:** disable Secure Boot, keep a stock kernel for rollback,
and do not use this kernel if you need ZFS. It is unsigned and provides no ZFS
modules.

## Install

Packages are available from the [Launchpad PPA](https://launchpad.net/~usatiuk/+archive/ubuntu/linux-mst-hdr).

```bash
sudo add-apt-repository ppa:usatiuk/linux-mst-hdr
sudo apt update
sudo apt install linux-mst-hdr
sudo reboot
```

The meta-package keeps the custom kernel updated through APT.

## Remove

Boot a stock kernel, then run this from a clone of this repository:

```bash
./mst-hdr-kernel remove
sudo add-apt-repository --remove ppa:usatiuk/linux-mst-hdr
```

[Build and upload instructions](docs/building.md) · [Patch details](patches/README.md)
