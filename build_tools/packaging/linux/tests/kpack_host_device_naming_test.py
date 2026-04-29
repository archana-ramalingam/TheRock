#!/usr/bin/env python3
# Copyright Advanced Micro Devices, Inc.
# SPDX-License-Identifier: MIT

"""Unit tests for kpack host-device-meta-v2 naming (packaging_utils)."""

import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, os.fspath(Path(__file__).parent.parent))

import packaging_utils as pu


def _base_config(**kwargs):
    defaults = dict(
        artifacts_dir=Path("/tmp/artifacts"),
        dest_dir=Path("/tmp/out"),
        pkg_type="deb",
        rocm_version="7.13.0",
        version_suffix="",
        install_prefix="/opt/rocm/core-7.13",
        gfx_arch=pu.GFX_GENERIC,
        enable_rpath=False,
        versioned_pkg=True,
        enable_kpack=True,
        gfxarch_list=("gfx94x", "gfx110x"),
        kpack_naming=pu.KPACK_NAMING_LEGACY,
    )
    defaults.update(kwargs)
    return pu.PackageConfig(**defaults)


class UsesHostDeviceKpackNamingTest(unittest.TestCase):
    def test_disabled_without_kpack(self):
        cfg = _base_config(enable_kpack=False, kpack_naming=pu.KPACK_NAMING_HOST_DEVICE_META_V2)
        info = {"Package": "amdrocm-blas", "Gfxarch": "True"}
        self.assertFalse(pu.uses_host_device_kpack_naming(info, cfg))

    def test_disabled_for_metapackage(self):
        cfg = _base_config(kpack_naming=pu.KPACK_NAMING_HOST_DEVICE_META_V2)
        info = {"Package": "amdrocm-core", "Gfxarch": "True", "Metapackage": "True"}
        self.assertFalse(pu.uses_host_device_kpack_naming(info, cfg))

    def test_global_v2_flag(self):
        cfg = _base_config(kpack_naming=pu.KPACK_NAMING_HOST_DEVICE_META_V2)
        info = {"Package": "amdrocm-blas", "Gfxarch": "True"}
        self.assertTrue(pu.uses_host_device_kpack_naming(info, cfg))

    def test_json_legacy_overrides_global_v2(self):
        cfg = _base_config(kpack_naming=pu.KPACK_NAMING_HOST_DEVICE_META_V2)
        info = {"Package": "amdrocm-blas", "Gfxarch": "True", "KpackLayout": "legacy"}
        self.assertFalse(pu.uses_host_device_kpack_naming(info, cfg))

    def test_json_v2_overrides_global_legacy(self):
        cfg = _base_config(kpack_naming=pu.KPACK_NAMING_LEGACY)
        info = {"Package": "amdrocm-blas", "Gfxarch": "True", "KpackLayout": "host-device-meta-v2"}
        self.assertTrue(pu.uses_host_device_kpack_naming(info, cfg))


class UpdatePackageNameKpackV2Test(unittest.TestCase):
    def test_legacy_kpack_generic_no_host_suffix(self):
        cfg = _base_config(
            kpack_naming=pu.KPACK_NAMING_LEGACY,
            gfx_arch=pu.GFX_GENERIC,
            pkg_type="deb",
        )
        self.assertEqual(pu.update_package_name("amdrocm-blas", cfg), "amdrocm-blas7.13")

    def test_v2_kpack_generic_deb_host_suffix(self):
        cfg = _base_config(
            kpack_naming=pu.KPACK_NAMING_HOST_DEVICE_META_V2,
            gfx_arch=pu.GFX_GENERIC,
            pkg_type="deb",
        )
        self.assertEqual(pu.update_package_name("amdrocm-blas", cfg), "amdrocm-blas-host7.13")

    def test_v2_kpack_arch_device_name_unchanged_pattern(self):
        cfg = _base_config(
            kpack_naming=pu.KPACK_NAMING_HOST_DEVICE_META_V2,
            gfx_arch="gfx94X-dcgpu",
            pkg_type="deb",
        )
        self.assertEqual(pu.update_package_name("amdrocm-blas", cfg), "amdrocm-blas7.13-gfx94x")

    def test_non_kpack_unchanged(self):
        cfg = _base_config(
            enable_kpack=False,
            gfx_arch="gfx94X-dcgpu",
            kpack_naming=pu.KPACK_NAMING_HOST_DEVICE_META_V2,
            pkg_type="deb",
        )
        self.assertEqual(pu.update_package_name("amdrocm-blas", cfg), "amdrocm-blas7.13-gfx94x")


@patch.object(pu, "get_package_list")
class ResolveNonversionedUmbrellaTest(unittest.TestCase):
    def test_v2_gfx_umbrella_lists_host_and_devices(self, mock_list):
        mock_list.return_value = (["amdrocm-blas"], [])
        cfg = _base_config(
            kpack_naming=pu.KPACK_NAMING_HOST_DEVICE_META_V2,
            gfx_arch=pu.GFX_GENERIC,
            versioned_pkg=False,
        )
        pkg_info = {"Package": "amdrocm-blas", "Gfxarch": "True"}
        out = pu.resolve_nonversioned_install_dependencies(pkg_info, cfg, is_meta=False)
        self.assertIn("amdrocm-blas-host7.13", out)
        self.assertIn("amdrocm-blas7.13-gfx94x", out)
        self.assertIn("amdrocm-blas7.13-gfx110x", out)

    def test_legacy_single_dep(self, mock_list):
        mock_list.return_value = (["amdrocm-blas"], [])
        cfg = _base_config(
            kpack_naming=pu.KPACK_NAMING_LEGACY,
            gfx_arch=pu.GFX_GENERIC,
            versioned_pkg=False,
        )
        pkg_info = {"Package": "amdrocm-blas", "Gfxarch": "True"}
        out = pu.resolve_nonversioned_install_dependencies(pkg_info, cfg, is_meta=False)
        self.assertEqual(out, "amdrocm-blas7.13")


if __name__ == "__main__":
    unittest.main()
