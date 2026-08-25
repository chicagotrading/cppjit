from __future__ import print_function

import os
import shutil
import subprocess
import sys

import py
import pytest

currpath = py.path.local(__file__).dirpath()

_NO_TOOLCHAIN = "no host make and C++ compiler to build the test dictionary"

# A build system that supplies the dictionaries itself sets
# CPPJIT_TEST_SKIP_MAKE, so no host toolchain is needed.
HAS_PREBUILT_DICTIONARIES = bool(os.getenv("CPPJIT_TEST_SKIP_MAKE", False))

# Otherwise test/Makefile builds them here. g++ is make's default $(CXX), which
# is what the Makefile recipe runs.
HAS_HOST_TOOLCHAIN = bool(
    shutil.which("make") and shutil.which(os.environ.get("CXX") or "g++")
)

# Decorate the individual tests that load a dictionary in a module whose other
# tests need none, and call setup_make(..., optional=True) from that module.
needs_dictionary = pytest.mark.skipif(
    not (HAS_PREBUILT_DICTIONARIES or HAS_HOST_TOOLCHAIN), reason=_NO_TOOLCHAIN
)


def setup_make(targetname, optional=False):
    if HAS_PREBUILT_DICTIONARIES:
        return

    if not HAS_HOST_TOOLCHAIN:
        if optional:
            return
        pytest.skip(_NO_TOOLCHAIN, allow_module_level=True)

    popen = subprocess.Popen(
        ["make", targetname + "Dict.so"],
        cwd=str(currpath),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    stdout, _ = popen.communicate()
    if popen.returncode:
        raise OSError("'make' failed:\n%s" % (stdout,))


if sys.hexversion >= 0x3000000:
    pylong = int
    pyunicode = str
    maxvalue = sys.maxsize
else:
    pylong = long  # noqa: F821
    pyunicode = unicode  # noqa: F821
    maxvalue = sys.maxint

IS_WINDOWS = 0
if "win32" in sys.platform:
    import platform

    if "64" in platform.architecture()[0]:
        IS_WINDOWS = 64
        maxvalue = 2**31 - 1
    else:
        IS_WINDOWS = 32

IS_MAC_ARM = 0
IS_MAC_X86 = 0
if "darwin" in sys.platform:
    import platform

    if "arm64" in platform.machine():
        IS_MAC_ARM = 64
        os.environ["CPPJIT_UNCAUGHT_QUIET"] = "1"
    else:
        IS_MAC_X86 = 1
IS_MAC = IS_MAC_ARM or IS_MAC_X86

IS_LINUX = 0
IS_LINUX_ARM = 0
IS_LINUX_X86 = 0
if "linux" in sys.platform:
    IS_LINUX = 1
    import platform

    if "aarch64" in platform.machine():
        IS_LINUX_ARM = 64
        os.environ["CPPJIT_UNCAUGHT_QUIET"] = "1"
    else:
        IS_LINUX_X86 = 1

try:
    import __pypy__  # noqa: F401

    ispypy = True
except ImportError:
    ispypy = False

import cppjit  # noqa: E402

IS_CLANG_REPL = (
    cppjit.evaluate("""#ifndef __CLING__ 
                                           true
                                           #else
                                           false
                                           #endif\n""")
    == 1
)
IS_CLANG_DEBUG = (
    cppjit.evaluate("""#ifdef NDEBUG
                                            false
                                            #else
                                            true
                                            #endif\n""")
    == 1
)
IS_CLING = not IS_CLANG_REPL
IS_CPP23 = (
    cppjit.evaluate("""#if __cplusplus >= 202302L
                                            true
                                            #else
                                            false
                                            #endif\n""")
    == 1
)
IS_VALGRIND = True if os.getenv("IS_VALGRIND") else False
