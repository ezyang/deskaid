#!/usr/bin/env python3

import logging
import subprocess
from typing import Dict, List, Optional


def run_command(
    cmd: List[str],
    cwd: Optional[str] = None,
    env: Optional[Dict[str, str]] = None,
    check: bool = True,
    capture_output: bool = True,
    text: bool = True,
    timeout: Optional[float] = None,
    shell: bool = False,
) -> subprocess.CompletedProcess:
    """
    Run a subprocess command with consistent logging.

    Args:
        cmd: Command to run as a list of strings
        cwd: Current working directory for the command
        env: Environment variables to set for the command
        check: If True, raise CalledProcessError if the command returns non-zero exit code
        capture_output: If True, capture stdout and stderr
        text: If True, decode stdout and stderr as text
        timeout: Timeout in seconds
        shell: If True, run command in a shell

    Returns:
        CompletedProcess instance with attributes args, returncode, stdout, stderr

    Raises:
        subprocess.CalledProcessError: If check=True and process returns non-zero exit code
        subprocess.TimeoutExpired: If the process times out
    """
    # Log the command being run at INFO level
    log_cmd = " ".join(str(c) for c in cmd)
    logging.info(f"Running command: {log_cmd}")

    # Run the subprocess
    result = subprocess.run(
        cmd,
        cwd=cwd,
        env=env,
        check=False,  # We'll handle the check ourselves
        capture_output=capture_output,
        text=text,
        timeout=timeout,
        shell=shell,
    )

    # Log stdout/stderr at DEBUG level
    if text:
        stdout = result.stdout if hasattr(result, "stdout") else ""
        stderr = result.stderr if hasattr(result, "stderr") else ""

        if stdout:
            logging.debug(f"Command stdout: {stdout}")
        if stderr:
            logging.debug(f"Command stderr: {stderr}")
    else:
        # Log binary output length
        stdout_len = (
            len(result.stdout) if hasattr(result, "stdout") and result.stdout else 0
        )
        stderr_len = (
            len(result.stderr) if hasattr(result, "stderr") and result.stderr else 0
        )

        if stdout_len:
            logging.debug(f"Command stdout: {stdout_len} bytes")
        if stderr_len:
            logging.debug(f"Command stderr: {stderr_len} bytes")

    # Log the return code
    logging.debug(f"Command return code: {result.returncode}")

    # Re-raise CalledProcessError if check is True and command failed
    if check and result.returncode != 0:
        raise subprocess.CalledProcessError(
            result.returncode, cmd, output=result.stdout, stderr=result.stderr
        )

    return result
