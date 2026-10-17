#!/usr/bin/env python3
"""Exercise package workflows with fake APT, dpkg and build commands."""

from pathlib import Path
import subprocess
import tempfile
import unittest


TOOL = Path(__file__).resolve().parents[1] / "mst-hdr-kernel"


class Workflows(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="mst-hdr-test-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.library = self.root / "mst-hdr-kernel"
        self.library.write_text(TOOL.read_text().removesuffix('main "$@"\n'))

    def run_shell(self, script):
        return subprocess.run(
            ["bash", "-c", 'source "$1"\n' + script, "test", str(self.library)],
            text=True, capture_output=True,
        )

    def remove(self, packages, apt_exit=0):
        (self.root / "packages").write_text(packages)
        return self.run_shell('''
            dpkg-query() { cat "$ROOT_DIR/packages"; }
            sudo() {
                printf '%s\\n' "$@" >"$ROOT_DIR/apt-args"
                return ''' + str(apt_exit) + '''
            }
            remove_packages
        ''')

    def test_remove_after_partial_purge_without_manifest(self):
        packages = """linux-image-unsigned-7.0.0-999-generic\t7.0.0-999.38+msthdr2\tinstalled
linux-modules-7.0.0-999-generic\t7.0.0-999.38+msthdr2\thalf-installed
linux-headers-6.19.0-999\t6.19.0-999.28+msthdr1\tconfig-files
linux-image-unsigned-7.0.0-38-generic\t7.0.0-38.38\tinstalled
linux-image-unsigned-7.0.0-999-generic\t7.0.0-999.38+other1\tinstalled
linux-tools-common\t7.0.0-999.38+msthdr2\tinstalled
"""
        result = self.remove(packages)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual((self.root / "apt-args").read_text().splitlines(), [
            "apt-get", "purge", "--",
            "linux-image-unsigned-7.0.0-999-generic",
            "linux-modules-7.0.0-999-generic", "linux-headers-6.19.0-999",
        ])

    def test_remove_meta_and_headers(self):
        packages = """linux-mst-hdr\t7.0.0.999.38+msthdr2\tinstalled
linux-headers-7.0.0-999-generic\t7.0.0-999.38+msthdr2\tunpacked
"""
        result = self.remove(packages, apt_exit=42)
        self.assertEqual(result.returncode, 42)
        self.assertEqual((self.root / "apt-args").read_text().splitlines()[3:], [
            "linux-mst-hdr", "linux-headers-7.0.0-999-generic",
        ])

    def test_remove_nothing_is_a_noop(self):
        result = self.remove("")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse((self.root / "apt-args").exists())

    def test_dpkg_failure_stops_removal(self):
        result = self.run_shell('''
            dpkg-query() { return 17; }
            sudo() { touch "$ROOT_DIR/apt-args"; }
            remove_packages
        ''')
        self.assertEqual(result.returncode, 17)
        self.assertFalse((self.root / "apt-args").exists())

    def prepare_install(self):
        current = self.root / ".work/current"
        current.mkdir(parents=True, exist_ok=True)
        (current / "manifest.env").write_text(
            "CUSTOM_VERSION=7.0.0-999.38+msthdr2\nKERNEL_RELEASE=7.0.0-999-generic\n"
        )
        directory = self.root / "dist/7.0.0-999.38+msthdr2/local"
        directory.mkdir(parents=True, exist_ok=True)
        for package in ["linux-headers-7.0.0-999", "linux-headers-7.0.0-999-generic",
                        "linux-image-unsigned-7.0.0-999-generic",
                        "linux-modules-7.0.0-999-generic", "linux-mst-hdr"]:
            (directory / f"{package}_test.deb").touch()
        return directory

    def install(self, overrides=""):
        return self.run_shell('''
            mokutil() { printf 'SecureBoot disabled\\n'; }
            findmnt() { return 1; }
            lsmod() { :; }
            sudo() { printf '%s\\n' "$@" >"$ROOT_DIR/apt-args"; }
        ''' + overrides + "\ninstall_packages\n")

    def test_install_without_stock_meta_requirement(self):
        self.prepare_install()
        result = self.install('dpkg-query() { return 17; }')
        self.assertEqual(result.returncode, 0, result.stderr)
        args = (self.root / "apt-args").read_text().splitlines()
        self.assertEqual(args[:3], ["apt-get", "install", "--"])
        self.assertEqual(len(args[3:]), 5)

    def test_missing_package_stops_before_apt(self):
        directory = self.prepare_install()
        next(directory.glob("linux-headers-7.0.0-999_test.deb")).unlink()
        result = self.install()
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse((self.root / "apt-args").exists())

    def test_secure_boot_and_zfs_still_block_installation(self):
        self.prepare_install()
        for override in [
            "mokutil() { printf 'SecureBoot enabled\\n'; }",
            "findmnt() { printf '/tank zfs\\n'; }",
            "lsmod() { printf 'zfs 123 1\\n'; }",
            "lsmod() { printf 'zfs 123 1\\n'; printf 'other 1 1\\n%.0s' {1..20000}; }",
        ]:
            with self.subTest(override=override):
                result = self.install(override)
                self.assertNotEqual(result.returncode, 0)
                self.assertFalse((self.root / "apt-args").exists())

    def test_build_failures_stop_before_meta_and_collection(self):
        self.prepare_install()
        current = self.root / ".work/current"
        (current / "source/debian").mkdir(parents=True)
        (current / "meta").mkdir()
        mock_bin = self.root / "bin"
        mock_bin.mkdir()
        rules = current / "source/debian/rules"
        rules.write_text('''#!/bin/sh
if [ "$1" = "$FAIL_STEP" ]; then
    printf 'step failed\\n' >&2
    exit 17
fi
''')
        dpkg = mock_bin / "dpkg-buildpackage"
        dpkg.write_text('''#!/bin/sh
case "$PWD" in
    */source) printf 'step failed\\n' >&2; exit 17;;
esac
touch "$TEST_ROOT/meta-built"
''')
        for command in [rules, dpkg]:
            command.chmod(0o755)
        for workflow, step in [("build_local", "clean"), ("build_local", "binary"),
                               ("build_source", "source")]:
            with self.subTest(workflow=workflow, step=step):
                result = self.run_shell('''
                    export PATH="$ROOT_DIR/bin:$PATH"
                    export TEST_ROOT="$ROOT_DIR"
                    export FAIL_STEP=''' + step + '''
                    require_image() { :; }
                    docker_is_rootless() { return 0; }
                    docker_run() {
                        local -a args=("$@")
                        args[-1]="${args[-1]//\\/workspace/$ROOT_DIR}"
                        "${args[@]}"
                    }
                    collect_local_artifacts() { touch "$ROOT_DIR/collected"; }
                    collect_source_artifacts() { touch "$ROOT_DIR/collected"; }
                    verify_source_roundtrip() { touch "$ROOT_DIR/roundtrip-ran"; }
                ''' + workflow)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("step failed", result.stderr)
                self.assertFalse((self.root / "collected").exists())
                self.assertFalse((self.root / "roundtrip-ran").exists())
                self.assertFalse((self.root / "meta-built").exists())


if __name__ == "__main__":
    unittest.main()
