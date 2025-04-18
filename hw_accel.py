import os
import re
import json
import logging
import subprocess
from typing import List, Dict, Optional, Tuple, Any, Union

logger = logging.getLogger(__name__)

class HardwareAcceleration:
    """Class to handle hardware acceleration detection and configuration."""
    
    def __init__(self, db_manager=None):
        """Initialize the hardware acceleration manager.
        
        Args:
            db_manager: Database manager instance
        """
        self.db_manager = db_manager
        self.ffmpeg_path = "ffmpeg"  # Default ffmpeg path
        self.detected_devices = []
    
    def set_ffmpeg_path(self, path: str):
        """Set the path to the ffmpeg executable.
        
        Args:
            path: Path to ffmpeg executable
        """
        self.ffmpeg_path = path
    
    def detect_hardware_devices(self) -> List[Dict[str, Any]]:
        """Detect available hardware acceleration devices.
        
        Returns:
            List of dictionaries with device information
        """
        devices = []
        
        # Check for NVIDIA GPUs (NVENC)
        if self._check_nvidia_support():
            nvidia_devices = self._get_nvidia_devices()
            devices.extend(nvidia_devices)
        
        # Check for Intel QuickSync
        if self._check_intel_qsv_support():
            intel_devices = self._get_intel_devices()
            devices.extend(intel_devices)
        
        # Check for AMD AMF
        if self._check_amd_support():
            amd_devices = self._get_amd_devices()
            devices.extend(amd_devices)
        
        # Store the detected devices
        self.detected_devices = devices
        
        # If we have a database manager, save the devices
        if self.db_manager and devices:
            self._save_devices_to_db(devices)
        
        return devices
    
    def _check_nvidia_support(self) -> bool:
        """Check if NVIDIA GPU acceleration is supported.
        
        Returns:
            True if supported, False otherwise
        """
        try:
            # Check if ffmpeg supports NVENC
            result = subprocess.run(
                [self.ffmpeg_path, "-hide_banner", "-encoders"],
                capture_output=True, text=True, check=False
            )
            return "h264_nvenc" in result.stdout
        except Exception as e:
            logger.warning(f"Error checking NVIDIA support: {e}")
            return False
    
    def _get_nvidia_devices(self) -> List[Dict[str, Any]]:
        """Get NVIDIA GPU devices.
        
        Returns:
            List of dictionaries with NVIDIA device information
        """
        devices = []
        
        try:
            # Try to use nvidia-smi to get device information
            result = subprocess.run(
                ["nvidia-smi", "--query-gpu=name,memory.total,driver_version", "--format=csv,noheader"],
                capture_output=True, text=True, check=False
            )
            
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                for i, line in enumerate(lines):
                    parts = line.split(', ')
                    if len(parts) >= 3:
                        name = parts[0]
                        memory = parts[1]
                        driver = parts[2]
                        
                        devices.append({
                            'device_name': name,
                            'device_type': 'nvidia',
                            'encoder': 'h264_nvenc',
                            'details': {
                                'memory': memory,
                                'driver': driver,
                                'device_index': i
                            },
                            'ffmpeg_options': {
                                'c:v': 'h264_nvenc',
                                'preset': 'p4',
                                'tune': 'hq',
                                'rc': 'vbr',
                                'cq': 23
                            }
                        })
            else:
                # If nvidia-smi fails, add a generic NVIDIA device
                devices.append({
                    'device_name': 'NVIDIA GPU',
                    'device_type': 'nvidia',
                    'encoder': 'h264_nvenc',
                    'details': {},
                    'ffmpeg_options': {
                        'c:v': 'h264_nvenc',
                        'preset': 'p4',
                        'tune': 'hq',
                        'rc': 'vbr',
                        'cq': 23
                    }
                })
        except Exception as e:
            logger.warning(f"Error getting NVIDIA devices: {e}")
            # Add a generic NVIDIA device if detection fails
            devices.append({
                'device_name': 'NVIDIA GPU',
                'device_type': 'nvidia',
                'encoder': 'h264_nvenc',
                'details': {},
                'ffmpeg_options': {
                    'c:v': 'h264_nvenc',
                    'preset': 'p4',
                    'tune': 'hq',
                    'rc': 'vbr',
                    'cq': 23
                }
            })
        
        return devices
    
    def _check_intel_qsv_support(self) -> bool:
        """Check if Intel QuickSync acceleration is supported.
        
        Returns:
            True if supported, False otherwise
        """
        try:
            # Check if ffmpeg supports QSV
            result = subprocess.run(
                [self.ffmpeg_path, "-hide_banner", "-encoders"],
                capture_output=True, text=True, check=False
            )
            return "h264_qsv" in result.stdout
        except Exception as e:
            logger.warning(f"Error checking Intel QSV support: {e}")
            return False
    
    def _get_intel_devices(self) -> List[Dict[str, Any]]:
        """Get Intel GPU devices.
        
        Returns:
            List of dictionaries with Intel device information
        """
        devices = []
        
        try:
            # Try to get Intel GPU information
            # This is platform dependent, and may need to be adjusted
            # For Linux, we could parse lspci
            # For Windows, we could use dxdiag or wmic
            
            # For now, add a generic Intel device
            devices.append({
                'device_name': 'Intel QuickSync',
                'device_type': 'intel',
                'encoder': 'h264_qsv',
                'details': {},
                'ffmpeg_options': {
                    'c:v': 'h264_qsv',
                    'preset': 'veryfast',
                    'look_ahead': 0
                }
            })
            
            # Check specifically for Intel Arc
            if self._check_intel_arc():
                devices.append({
                    'device_name': 'Intel Arc',
                    'device_type': 'intel',
                    'encoder': 'h264_qsv',
                    'details': {'arc': True},
                    'ffmpeg_options': {
                        'c:v': 'h264_qsv',
                        'preset': 'veryfast',
                        'look_ahead': 1
                    }
                })
            
        except Exception as e:
            logger.warning(f"Error getting Intel devices: {e}")
            # Add a generic Intel device if detection fails
            devices.append({
                'device_name': 'Intel GPU',
                'device_type': 'intel',
                'encoder': 'h264_qsv',
                'details': {},
                'ffmpeg_options': {
                    'c:v': 'h264_qsv',
                    'preset': 'veryfast'
                }
            })
        
        return devices
    
    def _check_intel_arc(self) -> bool:
        """Check if Intel Arc GPU is present.
        
        Returns:
            True if an Intel Arc GPU is detected, False otherwise
        """
        try:
            # This is platform dependent and may need adjustment
            
            # For Linux
            if os.name == 'posix':
                result = subprocess.run(
                    ["lspci", "-nn"],
                    capture_output=True, text=True, check=False
                )
                return any("Intel Arc" in line for line in result.stdout.splitlines())
            
            # For Windows
            elif os.name == 'nt':
                result = subprocess.run(
                    ["wmic", "path", "win32_VideoController", "get", "name"],
                    capture_output=True, text=True, check=False
                )
                return any("Intel Arc" in line for line in result.stdout.splitlines())
            
            return False
        except Exception as e:
            logger.warning(f"Error checking for Intel Arc: {e}")
            return False
    
    def _check_amd_support(self) -> bool:
        """Check if AMD GPU acceleration is supported.
        
        Returns:
            True if supported, False otherwise
        """
        try:
            # Check if ffmpeg supports AMF
            result = subprocess.run(
                [self.ffmpeg_path, "-hide_banner", "-encoders"],
                capture_output=True, text=True, check=False
            )
            return "h264_amf" in result.stdout
        except Exception as e:
            logger.warning(f"Error checking AMD support: {e}")
            return False
    
    def _get_amd_devices(self) -> List[Dict[str, Any]]:
        """Get AMD GPU devices.
        
        Returns:
            List of dictionaries with AMD device information
        """
        devices = []
        
        try:
            # Try to get AMD GPU information
            # This is platform dependent, similar to Intel detection
            
            # For now, add a generic AMD device
            devices.append({
                'device_name': 'AMD GPU',
                'device_type': 'amd',
                'encoder': 'h264_amf',
                'details': {},
                'ffmpeg_options': {
                    'c:v': 'h264_amf',
                    'quality': 'speed',
                    'usage': 'ultralowlatency'
                }
            })
            
        except Exception as e:
            logger.warning(f"Error getting AMD devices: {e}")
            # Add a generic AMD device if detection fails
            devices.append({
                'device_name': 'AMD GPU',
                'device_type': 'amd',
                'encoder': 'h264_amf',
                'details': {},
                'ffmpeg_options': {
                    'c:v': 'h264_amf',
                    'quality': 'speed'
                }
            })
        
        return devices
    
    def _save_devices_to_db(self, devices: List[Dict[str, Any]]):
        """Save detected devices to the database.
        
        Args:
            devices: List of device dictionaries
        """
        try:
            # Save each device to the database
            for i, device in enumerate(devices):
                # Set the first device as preferred if there are no preferred devices
                existing_preferred = self.db_manager.get_preferred_hw_accel_device()
                preferred = (i == 0 and not existing_preferred)
                
                self.db_manager.add_hw_accel_device(
                    device_name=device['device_name'],
                    device_type=device['device_type'],
                    encoder=device['encoder'],
                    transcode_enabled=True,  # Enable transcoding by default
                    preferred=preferred,
                    ffmpeg_options=device['ffmpeg_options']
                )
        except Exception as e:
            logger.error(f"Error saving devices to database: {e}")
    
    def get_preferred_device(self) -> Optional[Dict[str, Any]]:
        """Get the preferred hardware acceleration device.
        
        Returns:
            Device dictionary if found, None otherwise
        """
        if self.db_manager:
            return self.db_manager.get_preferred_hw_accel_device()
        
        # If no database manager, return the first detected device
        return self.detected_devices[0] if self.detected_devices else None
    
    def generate_ffmpeg_hw_accel_args(self, preferred_device: Optional[Dict[str, Any]] = None) -> List[str]:
        """Generate ffmpeg hardware acceleration arguments.
        
        Args:
            preferred_device: Preferred hardware acceleration device
            
        Returns:
            List of ffmpeg arguments
        """
        if preferred_device is None:
            preferred_device = self.get_preferred_device()
        
        if not preferred_device:
            # No hardware acceleration available
            return []
        
        # Extract ffmpeg options from the device
        ffmpeg_options = preferred_device.get('ffmpeg_options', {})
        
        # Convert the options dictionary to ffmpeg command-line arguments
        args = []
        for key, value in ffmpeg_options.items():
            args.extend([f"-{key}", str(value)])
        
        return args

    def create_ffmpeg_command(self, 
                             input_file: str, 
                             output_options: List[str],
                             transcode: bool = False,
                             hw_device: Optional[Dict[str, Any]] = None) -> List[str]:
        """Create a ffmpeg command with hardware acceleration.
        
        Args:
            input_file: Input file path
            output_options: Additional output options
            transcode: Whether to transcode the video
            hw_device: Hardware acceleration device to use
            
        Returns:
            List of ffmpeg command arguments
        """
        if hw_device is None:
            hw_device = self.get_preferred_device()
        
        cmd = [self.ffmpeg_path, "-i", input_file]
        
        if hw_device and transcode:
            # Add hardware acceleration arguments for transcoding
            hw_args = self.generate_ffmpeg_hw_accel_args(hw_device)
            cmd.extend(hw_args)
        else:
            # Copy the video stream without transcoding
            cmd.extend(["-c:v", "copy"])
        
        # Add any additional output options
        cmd.extend(output_options)
        
        return cmd


# Function to detect and initialize hardware acceleration
def init_hw_accel(db_manager=None, ffmpeg_path="ffmpeg"):
    """Detect and initialize hardware acceleration.
    
    Args:
        db_manager: Database manager instance
        ffmpeg_path: Path to ffmpeg executable
        
    Returns:
        HardwareAcceleration instance
    """
    hw_accel = HardwareAcceleration(db_manager)
    hw_accel.set_ffmpeg_path(ffmpeg_path)
    hw_accel.detect_hardware_devices()
    return hw_accel
