"""
Build system module for NuttX.
"""

import os
import subprocess
import logging
from pathlib import Path
from typing import List, Dict, Optional

from enum import Enum

# Get logger for this module
logger = logging.getLogger(__name__)

class BuilderAction(str, Enum):
    def __str__(self):
        return str(self.value)

    def __repr__(self):
        return str(self)

    BUILD = "build"
    CLEAN = "clean"
    DISTCLEAN = "distclean"
    CONFIGURE = "configure"
    INFO = "info"
    MAKE = "make"

class MakeAction(str, Enum):
    def __str__(self):
        return str(self.value)

    def __repr__(self):
        return str(self)

    ALL = "all"
    APPS_CLEAN = "apps_clean"
    BOOTLOADER = "bootloader"
    CLEAN = "clean"
    CLEAN_BOOTLOADER = "clean_bootloader"
    CRYPTO = "crypto/"
    DISTCLEAN = "distclean"
    FLASH = "flash"
    HOST_INFO = "host_info"
    MENUCONFIG = "menuconfig"
    OLDCONFIG = "oldconfig"
    OLDDEFCONFIG = "olddefconfig"
    SCHED_CLEAN = "sched_clean"

class NuttXBuilder:
    """Main builder class for NuttX projects."""
    
    def __init__(self, nuttxspace_path: str = None):
        self.nuttxspace_path = nuttxspace_path
        self.nuttx_path = nuttxspace_path / "nuttx"
        self.apps_path = nuttxspace_path / "nuttx-apps"
        self.rel_apps_path = None
    
    def build(self, parallel: int = None):
        """Build the NuttX project."""
        logger.info(f"Starting build with parallel={parallel}")
        if parallel:
            args = [f"-j{parallel}"]
        else:
            args = []

        return self._run_command([BuilderAction.MAKE] + args)
    
    def distclean(self):
        """Distclean the NuttX project."""
        logger.info("Running distclean")
        self._run_command([BuilderAction.MAKE, MakeAction.DISTCLEAN])
    
    def clean(self):
        """Clean build artifacts."""
        logger.info("Running clean")
        self._run_command([BuilderAction.MAKE, MakeAction.CLEAN])
    
    def validate_nuttx_environment(self) -> tuple[bool, str]:
        """Validate NuttX environment and return (is_valid, error_message)."""
        logger.info(f"Validating NuttX environment: nuttx_dir={self.nuttx_path}, apps_dir={self.apps_path}")
        
        # Check for NuttX environment files
        makefile_path = self.nuttx_path / "Makefile"
        inviolables_path = self.nuttx_path / "INVIOLABLES.md"
        
        if not makefile_path.exists():
            logger.error(f"Makefile not found at: {makefile_path}")
            return False, f"Invalid NuttX directory: {self.nuttx_path}"
        
        if not inviolables_path.exists():
            logger.error(f"INVIOLABLES.md not found at: {inviolables_path}")
            return False, f"Invalid NuttX directory: {self.nuttx_path}"
        
        # Validate apps directory
        if self.nuttx_path.parent == self.apps_path.parent:
            app_dir_name = self.apps_path.stem
            self.rel_apps_path = f"../{app_dir_name}"
        else:
            self.rel_apps_path = self.apps_path

        if not self.apps_path.exists():
            logger.error(f"Apps directory not found: {self.apps_path}")
            return False, f"Apps directory not found: {self.apps_path}"
        
        if not self.apps_path.is_dir():
            logger.error(f"Apps path is not a directory: {self.apps_path}")
            return False, f"Apps path is not a directory: {self.apps_path}"
        
        # Validate apps directory structure
        if not (self.apps_path / "Make.defs").exists():
            logger.error(f"Make.defs not found in apps directory: {self.apps_path}")
            return False, f"Apps directory may not be properly configured (Make.defs missing): {self.apps_path}"
        
        logger.info("NuttX environment validation successful")
        return True, ""
    
    def setup_nuttx(self, board: str, defconfig: str) -> int:
        """Run NuttX setup commands in the NuttX directory."""
        logger.info(f"Setting up NuttX: board={board}, defconfig={defconfig}")
        try:
            # Validate environment first
            is_valid, error_msg = self.validate_nuttx_environment()
            if not is_valid:
                logger.error(f"Validation failed: {error_msg}")
                print(f"❌ Validation failed: {error_msg}")
                return 1

            # Change to NuttX directory
            logger.debug(f"Changing to NuttX directory: {self.nuttx_path}")
            os.chdir(self.nuttx_path)

            # Run configure script
            logger.info(f"Running configure.sh with args: -a {self.rel_apps_path} {board}:{defconfig}")
            config_result = self._run_bash_script("./tools/configure.sh", 
                                                args=[f"-a {self.rel_apps_path}", f"{board}:{defconfig}"], cwd=self.nuttx_path)
            if config_result != 0:
                logger.error(f"Configure script failed with exit code: {config_result}")
                return config_result
            
            logger.info("NuttX setup completed successfully")
            return 0
            
        except Exception as e:
            logger.error(f"Setup failed with error: {e}", exc_info=True)
            print(f"Setup failed with error: {e}")
            return 1
    
    def _run_command(self, cmd: List[str], cwd: Optional[str] = None) -> int:
        """Run a shell command and return exit code."""
        if not cwd:
            cwd = self.nuttx_path
        logger.debug(f"Running command: {cmd} in cwd={cwd}")
        try:
            result = subprocess.run(
                cmd, 
                cwd=cwd, 
                check=True, 
                capture_output=True, 
                text=True,
            )
            logger.debug(f"Command succeeded with return code: {result.returncode}")
            return result
        except subprocess.CalledProcessError as e:
            logger.error(f"Command failed: {' '.join(cmd)}, error: {e}")
            print(f"Command failed: {' '.join(cmd)}")
            print(f"Error: {e}")
            return e.returncode

    def _run_bash_script(self, script_path: str, args: List[str] = None, cwd: Optional[str] = None) -> int:
        """Run a bash script using subprocess.call and return exit code."""
        if not cwd:
            cwd = self.nuttx_path
        try:
            cmd = [script_path]
            if args:
                cmd.extend(args)
            
            cmd = ' '.join(cmd)
            logger.debug(f"Running bash script: {cmd} in cwd={cwd}")
            result = subprocess.call(cmd, cwd=cwd, shell=True)
            logger.debug(f"Bash script result: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Failed to run bash script {script_path}: {e}", exc_info=True)
            print(f"Failed to run bash script {script_path}: {e}")
            return 1
