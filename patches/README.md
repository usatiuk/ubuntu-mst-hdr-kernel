# Intel MST VRR/HDR v6 backport

`intel-mst-vrr-hdr-v6-ubuntu-7.0.patch` replaces the previous HDR-only v3
backport. Its baseline is Ubuntu Resolute `linux` source `7.0.0-38.38`, the
latest stable Ubuntu 26.04 source checked on October 17, 2026 using fresh
container APT indexes. It enables HDR metadata, VSC SDPs, 10-bpc-capable MST
streams, HDR fastsets, and VRR capability/signalling.

## Upstream sources

The main implementation is Xiao Lu's v6, the newest revision returned by
Patchwork for this series when checked on October 17:

- Series: <https://patchwork.freedesktop.org/series/173155/>
- Message-ID: `20260902051206.264215-1-xiaolu.xie@intel.com`
- Archive: <https://www.mail-archive.com/intel-gfx@lists.freedesktop.org/msg383958.html>
- Original mbox: [upstream/xiao-v6.mbox](upstream/xiao-v6.mbox)
- Download: <https://patchwork.freedesktop.org/api/1.0/series/173155/revisions/6/mbox/>

Gil Dekel's v3 **patch 1/2 only** supplies per-connector colorimetry support:

- Message-ID: `20260626214513.179943-2-gildekel@google.com`
- Archive: <https://www.mail-archive.com/intel-gfx@lists.freedesktop.org/msg381527.html>
- Original first-message extract: [upstream/gil-v3-colorimetry.mbox](upstream/gil-v3-colorimetry.mbox)
- Series mbox: <https://patchwork.freedesktop.org/api/1.0/series/169209/revisions/3/mbox/>

Gil's overlapping HDR implementation (patch 2/2) is not applied. The separate
HDR-to-SDR null-infoframe series is not included. These submissions remain
experimental; passing basic upstream CI does not establish that the rebased
kernel works on this machine.

## Ubuntu 7.0 adaptations

- Resolve the older function signatures, helper names and stream-enable loop
  context explicitly. No fuzzy patch application is allowed.
- Ubuntu 7.0 has no `intel_dp_needs_as_sdp()` helper. Keep its existing AS-SDP
  computation, which already gates transmission on actual `vrr.enable`, and
  invoke it for MST as v6 requires. The newer helper's branch-device exclusion
  is absent here, so its relaxation needs no equivalent change.
- Ubuntu 7.0 uses `crtc_state->pipe_bpp` instead of the newer `max_pipe_bpp`.
  Bound the MST maximum by both that already computed platform/user limit and
  the EDID depth (`min(pipe_bpp, sink_bpc * 3)`, unknown depth defaults to 8).
  This removes the unconditional 24-bpp cap while preserving the connector's
  max-bpc request. Ubuntu's existing `max_link_bpp_x16` retry path still handles
  aggregate link bandwidth and DSC. No forced `hdr_enabled ? 30 : 24` is used.
- Retain Gil's per-sink colorimetry check at Ubuntu 7.0's VSC computation site;
  its later relocation to `intel_dp_needs_vsc_colorimetry()` is not present in
  this Ubuntu source.
- Require an exact one-byte read before modifying `DP_DOWNSPREAD_CTRL`; v6's
  negative-only error check could otherwise use an uninitialized byte on a
  short read. The rest of v6's remote DPCD read/write mechanism is retained.

10 bpc is enabled as a capability, not forced. Actual operation at 4K 120 Hz
HDR alongside the second MST display still requires hardware verification of
DSC, link allocation, hotplug, HDR toggles and suspend/resume. VRR likewise
requires a capable downstream sink and valid EDID refresh ranges.

## Checksums

SHA-256:

```text
8a8b9b40462337acfba9c4903b52c098757eb71a5e99fdaaa9afd9cf574056db  intel-mst-vrr-hdr-v6-ubuntu-7.0.patch
e8d3cac4b1c38c97c80f2deb8d0e76d2b16ff824f623cc8a1ca57dc8c76e033c  upstream/xiao-v6.mbox
4c7d5b74ebaf4cc8e71e2d675614f32b2356bf4ebd4c299eb02d7aa2818a0559  upstream/gil-v3-colorimetry.mbox
```

The builder verifies the rebased patch checksum and the complete allowlist of
seven modified DRM files before applying it.

## Validation on October 17, 2026

- Full Ubuntu `debian/rules binary` build passed inside Docker, producing
  `7.0.0-999.38+msthdr2` image, modules, headers and companion packages, plus
  the `7.0.0.999.38+msthdr2` meta-package.
- Kernel and meta source packages built inside Docker and unpacked again.
  All seven patched files matched the reviewed rebase, and the embedded
  meta-package manifest matched the release manifest.
- Static tests and `checkpatch.pl --no-tree --no-signoff` passed. Forward and
  reverse patch checks passed with fuzz disabled.
- Both packaged Intel modules report `7.0.0-999-generic` vermagic. The kernel
  package contains an x86 bzImage with that release. Package dependencies and
  all release checksums were verified.

Artifacts are under `dist/7.0.0-999.38+msthdr2/{local,source}/`. The source
uploads are unsigned. No packages were installed or uploaded, and the kernel
was not booted for hardware validation.
