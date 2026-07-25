# Intel HDR over DP MST backport

`intel-mst-hdr-v3-ubuntu-7.0.patch` backports Gil Dekel's two-patch v3
series, `[PATCH v3 0/2] drm/i915/display: Enable HDR over DP MST`, to the
Ubuntu 26.04 `7.0.0-28.28` kernel source.

Upstream references:

- Cover Message-ID: `20260626214513.179943-1-gildekel@google.com`
- Patchwork series: <https://patchwork.freedesktop.org/series/169609/>
- v3 archive:
  <https://www.mail-archive.com/dri-devel@lists.freedesktop.org/msg615953.html>
- v3 patch 1:
  <https://www.mail-archive.com/dri-devel@lists.freedesktop.org/msg615954.html>
- v3 patch 2:
  <https://www.mail-archive.com/dri-devel@lists.freedesktop.org/msg615955.html>

The v3 code is identical to v2. V3 removes Gerrit `Change-Id` trailers and
adds `Assisted-by` trailers.

Ubuntu 7.0 adaptations are context-only:

- Ubuntu's `intel_dp_compute_config()` declaration has the older signature.
- The nearby `intel_dp_dsc_reset_config()` declaration is absent.
- The function following the colorimetry getter has a different return type.

No functional prerequisite was added. The patch must apply with fuzz disabled.
Its expected SHA-256 is:

```text
f4f5215b2019f5e0714472af05d403f4f9046e7f2938795636e6cb63ce76f019
```
