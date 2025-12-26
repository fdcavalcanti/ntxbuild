API Reference
================

This page contains the complete API reference for all modules in the ntxbuild package.

Build Module
---------------------

Use the Build Module to manage the `nuttxspace`: create a configuration, build,
clean and use general `make` commands.

.. automodule:: ntxbuild.build
   :members:
   :show-inheritance:
   :undoc-members:

Configuration Module
----------------------

Apply Kconfig changes and manage NuttX configurations using the Configuration Module.

.. automodule:: ntxbuild.config
   :members:
   :show-inheritance:
   :undoc-members:

Environment Data Module
-------------------------

This module helps in setting up and retrieving necessary environment variables for building NuttX projects.

.. automodule:: ntxbuild.env_data
   :members:
   :show-inheritance:
   :undoc-members:

CLI Module
-------------------
Use the CLI Module to parse command line arguments and execute commands.
This generally should not be used but the API is available anyway.

.. automodule:: ntxbuild.cli
   :members:
   :show-inheritance:
   :undoc-members:

Setup Module
---------------------

This contains helper funtions to setup the ntxbuild environment, such as
downloading the NuttX source code.

.. automodule:: ntxbuild.setup
   :members:
   :show-inheritance:
   :undoc-members:

Utilities Module
---------------------

.. automodule:: ntxbuild.utils
   :members:
   :show-inheritance:
   :undoc-members:

Module contents
---------------

.. automodule:: ntxbuild
   :members:
   :show-inheritance:
   :undoc-members:
