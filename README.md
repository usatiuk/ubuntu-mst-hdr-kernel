# Ubuntu Intel MST-HDR kernel

This repository prepares a complete Ubuntu 26.04 `generic` kernel containing
the experimental Intel HDR-over-DisplayPort-MST v3 patch series. It builds a
parallel ABI (`999`) so the normal Ubuntu HWE kernel remains installed.

The tested machine is an Ubuntu 26.04 NUC with:

- Ubuntu kernel `7.0.0-28-generic`
- Intel `8086:7d51`, bound to `i915`
- Dell U2725QE on the logical MST connector `DP-5`
- GNOME 50 on Wayland

The upstream series was still unmerged and had unresolved Intel CI failures
when this backport was prepared. Treat the result as an experimental test
kernel, not a security-supported replacement for Ubuntu's kernel.

## Design

The kernel keeps Ubuntu's `linux` source package and `generic` flavour. Only
the ABI and Debian version change. For Ubuntu source `7.0.0-28.28` and
packaging revision 1, the important outputs are:

```text
linux-image-unsigned-7.0.0-999-generic
linux-modules-7.0.0-999-generic
linux-headers-7.0.0-999
linux-headers-7.0.0-999-generic
linux-mst-hdr
```

`linux-mst-hdr` is a small meta-package. It lets a PPA move clients to a new
base kernel release later without inventing a custom Ubuntu kernel flavour.

`999` is an ABI number, not the patch revision. Changing only the ABI reuses
Ubuntu's existing `generic` configuration, annotations, build rules, and
package templates. A kernel release ending in `-mst-hdr` would require adding
and maintaining a new Ubuntu flavour through all of those packaging layers,
without improving isolation. The stable meta-package already carries the
human-readable `mst-hdr` name.

All source downloads and builds run in an Ubuntu 26.04 Docker container.
Host APT source repositories are not modified. Rootless Docker is detected:
container root is used because it maps to the invoking host user. With a
rootful daemon, normal build steps run as the invoking UID/GID and root-owned
source downloads are handed back to that UID/GID.

## Safety

- Secure Boot must be disabled before installing the unsigned kernel.
- `linux-generic-hwe-26.04` and a stock kernel in `/boot` are mandatory.
- The installer does not remove or overwrite stock packages.
- The installer and package triggers do not customize GRUB settings.
- Nothing reboots automatically.
- Removal is refused while the custom kernel is running.
- The custom ABI omits Ubuntu's separately signed ZFS companion package.
  Installation is refused when ZFS is active; the tested machine uses ext4.

Run the preflight report first:

```bash
./mst-hdr-kernel doctor
./mst-hdr-kernel self-test
```

## Prepare and build

The first command builds a reusable container image with Ubuntu's kernel
build dependencies:

```bash
./mst-hdr-kernel image
```

Prepare the Ubuntu source corresponding to the running kernel:

```bash
export DEBFULLNAME="Your Name"
export DEBEMAIL="address-used-by-your-launchpad-key@example.com"

./mst-hdr-kernel prepare --running
```

Alternative targets are:

```bash
./mst-hdr-kernel prepare --latest
./mst-hdr-kernel prepare --source-version 7.0.0-28.28
./mst-hdr-kernel prepare --running --revision 2
./mst-hdr-kernel prepare --running --refresh-source
```

Preparation verifies the pinned patch checksum, downloads the exact Ubuntu
source, applies the backport with fuzz disabled, creates the `999` changelog
entry, removes the unsatisfiable dependency on Canonical's separately signed
ZFS modules, and generates the meta-package. Downloaded Ubuntu source-package
archives are cached by exact version under `.work/source-cache/`; subsequent
preparations verify and reuse them. On a cache miss, the disposable container
refreshes its APT indexes at runtime. Repository indexes are not baked into
the image. `--refresh-source` discards only that version's cache and downloads
it again. The extracted and patched source tree is always recreated from
scratch.

Build local binary packages:

```bash
./mst-hdr-kernel build-local
```

This runs Canonical's full packaging route. With rootless Docker it invokes
the rules as container root, which maps to the invoking host user. With
rootful Docker it invokes the same rules through `fakeroot` as the host
UID/GID:

```text
debian/rules clean
debian/rules binary
```

The build is intentionally large. Allow at least 30 GiB of free space.
Packages and checksums are collected under `dist/<version>/local/`.

## Install and verify

After disabling Secure Boot in firmware:

```bash
./mst-hdr-kernel install
sudo reboot
```

After booting the custom kernel:

```bash
./mst-hdr-kernel verify
```

The automated checks confirm the custom ABI, active `i915` driver, connected
Dell U2725QE, and obvious i915/DRM failures. Install `drm-info` for connector
property inspection:

```bash
sudo apt install drm-info
```

Hardware acceptance still requires:

1. Enable HDR for the Dell in GNOME Settings.
2. Toggle HDR off and on to exercise the MST fastset path.
3. Confirm both displays retain their native modes.
4. Test dock hotplug and suspend/resume.

To remove the custom kernel, boot a stock Ubuntu kernel first and run:

```bash
./mst-hdr-kernel remove
```

## PPA-ready source packages

Launchpad accepts signed source uploads, not locally built `.deb` files.
Generate kernel and meta-package uploads with:

```bash
./mst-hdr-kernel build-source --sign-key YOUR_GPG_KEY_ID
```

Signing happens on the host; the private key is never mounted into the
builder container. The source packages are also unpacked again in a clean
directory before being collected under `dist/<version>/source/`. The kernel
upload references Ubuntu's existing `linux_7.0.0.orig.tar.gz` in the primary
archive, so that 255 MB file is not uploaded to the PPA.

Upload both `_source.changes` files explicitly:

```bash
dput ppa:YOUR_LAUNCHPAD_NAME/mst-hdr \
  dist/<version>/source/linux_<version>_source.changes

dput ppa:YOUR_LAUNCHPAD_NAME/mst-hdr \
  dist/<version>/source/linux-mst-hdr-meta_<version>_source.changes
```

Launchpad will initially hold the meta-package in dependency-wait state until
the kernel binaries are published. It then builds automatically.

No Launchpad account, PPA, upload destination, or GitHub automation is
created by this repository.

## Updating

Ubuntu's current Resolute generic package at the time of the tested build is
`7.0.0-28.28`. The corresponding patched package version is
`7.0.0-999.28+msthdr1`:

- `7.0.0` is the kernel base version.
- `999` is the reserved custom ABI.
- `.28` tracks the Ubuntu upload revision.
- `+msthdr1` identifies revision 1 of this backport and packaging.

For a later Ubuntu update, refresh the host's package metadata, prepare the
new source, and build/upload both source packages:

```bash
sudo apt update
./mst-hdr-kernel prepare --latest
./mst-hdr-kernel build-source --sign-key YOUR_GPG_KEY_ID

dput ppa:YOUR_LAUNCHPAD_NAME/mst-hdr \
  dist/<version>/source/linux_<version>_source.changes
dput ppa:YOUR_LAUNCHPAD_NAME/mst-hdr \
  dist/<version>/source/linux-mst-hdr-meta_<version>_source.changes
```

`prepare` always applies and checksum-verifies the MST-HDR patch. A cache miss
refreshes APT metadata and downloads the new exact Ubuntu source inside a
disposable container; the reusable builder image is not rebuilt. Once
Launchpad publishes both builds, machines with the PPA and `linux-mst-hdr`
installed receive the new custom kernel through the normal `apt upgrade`
path. The stock `linux-generic-hwe-26.04` meta-package continues updating
independently.

For local testing before uploading, run `build-local` after `prepare`.
Use `--revision 2` (then 3, and so on) when changing the backport or packaging
without changing Ubuntu's source version. If the patch no longer applies,
preparation stops without fuzzing it into place. A reverse-applying patch is
reported separately because it may mean Ubuntu already contains the feature.

Refresh the container after Ubuntu changes kernel build dependencies:

```bash
./mst-hdr-kernel image --refresh
```

## Patch provenance

See [patches/README.md](patches/README.md) for upstream Message-IDs, archives,
the exact checksum, and the Ubuntu 7.0 context adaptations.
