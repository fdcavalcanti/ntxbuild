.. ntxbuild documentation master file, created by
   sphinx-quickstart on Mon Dec  8 17:37:16 2025.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

ntxbuild Documentation
======================

**NuttX Build System Assistant** - A Python tool for managing and building NuttX RTOS projects with ease.

ntxbuild is simply a wrapper around the many tools available in the NuttX repository. It wraps around tools
such as make, kconfig-tweak, menuconfig and most used bash scripts (such as configure.sh).

This tool provides a command line interface that supports NuttX configuration and building,
while also providing a Python API that allows you to script your builds.

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   quick_start
   api_examples
   examples
   features
   how_it_works
