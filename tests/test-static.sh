#!/usr/bin/env bash
set -Eeuo pipefail

root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"

bash -n "${root}/mst-hdr-kernel"
"${root}/mst-hdr-kernel" self-test

test -x "${root}/mst-hdr-kernel"
test -x "${root}/meta/debian/rules"
test -f "${root}/container/Dockerfile"
test -f "${root}/patches/intel-mst-vrr-hdr-v6-ubuntu-7.0.patch"

if command -v shellcheck >/dev/null 2>&1; then
    shellcheck "${root}/mst-hdr-kernel" "${root}/tests/test-static.sh"
else
    printf '%s\n' 'shellcheck not installed; skipped'
fi

printf '%s\n' 'static tests passed'

