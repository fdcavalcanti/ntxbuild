"""
Build system module for NuttX.
"""

import os
import subprocess
from pathlib import Path
from typing import List, Dict, Optional

class NuttXBuilder:
    """Main builder class for NuttX projects."""
    
    def __init__(self, config_path: str = None):
        self.config_path = config_path
        self.config = {}
    
    def load_config(self, config_path: str = None):
        """Load build configuration."""
        if config_path:
            self.config_path = config_path
        # TODO: Implement configuration loading
        pass
    
    def build(self, parallel: int = None):
        """Build the NuttX project."""
        if parallel:
            args = [f"-j{parallel}"]
        else:
            args = []

        self._run_command(["make"] + args)
        return 0
    
    def distclean(self):
        """Distclean the NuttX project."""
        self._run_command(["make", "distclean"])
    
    def clean(self):
        """Clean build artifacts."""
        self._run_command(["make", "clean"])
    
    def validate_nuttx_environment(self, nuttx_dir: Path, apps_dir: Path) -> tuple[bool, str]:
        """Validate NuttX environment and return (is_valid, error_message)."""
        # Check for NuttX environment files
        makefile_path = nuttx_dir / "Makefile"
        inviolables_path = nuttx_dir / "INVIOLABLES.md"
        
        if not makefile_path.exists():
            return False, f"Invalid NuttX directory: {nuttx_dir}"
        
        if not inviolables_path.exists():
            return False, f"Invalid NuttX directory: {nuttx_dir}"
        
        # Validate apps directory
        if not apps_dir.exists():
            return False, f"Apps directory not found: {apps_dir}"
        
        if not apps_dir.is_dir():
            return False, f"Apps path is not a directory: {apps_dir}"
        
        # Validate apps directory structure
        if not (apps_dir / "Make.defs").exists():
            return False, f"Apps directory may not be properly configured (Make.defs missing): {apps_dir}"
        
        return True, ""
    
    def setup_nuttx(self, nuttx_dir: Path, apps_dir: Path, board: str, defconfig: str) -> int:
        """Run NuttX setup commands in the NuttX directory."""
        try:
            # Validate environment first
            is_valid, error_msg = self.validate_nuttx_environment(nuttx_dir, apps_dir)
            if not is_valid:
                print(f"❌ Validation failed: {error_msg}")
                return 1
            
            # Change to NuttX directory
            os.chdir(nuttx_dir)
            
            # Run configure script
            rel_apps_dir = apps_dir.relative_to(nuttx_dir)
            config_result = self._run_bash_script("./tools/configure.sh", 
                                                args=[f"-a {rel_apps_dir}", f"{board}:{defconfig}"], cwd=nuttx_dir)
            if config_result != 0:
                return config_result
            
            return 0
            
        except Exception as e:
            print(f"Setup failed with error: {e}")
            return 1
    
    def kconfig_read(self, config: str):
        """Read Kconfig file"""
        ans = self._run_command(["kconfig-tweak", "-s", config])
        print(f"{config}={ans.stdout.strip()}")
        return 0
    
    def _run_command(self, cmd: List[str], cwd: Optional[str] = None) -> int:
        """Run a shell command and return exit code."""
        try:
            result = subprocess.run(
                cmd, 
                cwd=cwd, 
                check=True, 
                capture_output=True, 
                text=True,
            )
            return result
        except subprocess.CalledProcessError as e:
            print(f"Command failed: {' '.join(cmd)}")
            print(f"Error: {e}")
            return e.returncode

    def _run_bash_script(self, script_path: str, args: List[str] = None, cwd: Optional[str] = None) -> int:
        """Run a bash script using subprocess.call and return exit code."""
        try:
            cmd = [script_path]
            if args:
                cmd.extend(args)
            
            cmd = ' '.join(cmd)
            result = subprocess.call(cmd, cwd=cwd, shell=True)
            print(f"Command result: {result}")
            return result
            
        except Exception as e:
            print(f"Failed to run bash script {script_path}: {e}")
            return 1
