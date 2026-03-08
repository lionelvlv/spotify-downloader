"""
Audio converter using FFmpeg to create Opus files.
"""
import logging
import subprocess
from pathlib import Path
from typing import Optional


class ConversionError(Exception):
    """Custom exception for conversion failures."""
    pass


class Converter:
    """Convert audio files to Opus format using FFmpeg."""
    
    def __init__(
        self,
        bitrate: str = "128k",
        sample_rate: int = 48000,
        compression_level: int = 10
    ):
        """
        Initialize converter.
        
        Args:
            bitrate: Target bitrate (e.g., "96k", "128k", "160k")
            sample_rate: Sample rate in Hz (Opus standard is 48000)
            compression_level: Compression level 0-10 (10 is slowest but best)
        """
        self.logger = logging.getLogger(__name__)
        self.bitrate = bitrate
        self.sample_rate = sample_rate
        self.compression_level = compression_level
        
        # Verify FFmpeg is available
        if not self._check_ffmpeg():
            raise RuntimeError("FFmpeg is not installed or not in PATH")
    
    def _check_ffmpeg(self) -> bool:
        """
        Check if FFmpeg is available.
        
        Returns:
            True if FFmpeg is available, False otherwise
        """
        try:
            result = subprocess.run(
                ['ffmpeg', '-version'],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.returncode == 0
        except Exception:
            return False
    
    def to_opus(self, input_path: Path, output_path: Path) -> Path:
        """
        Convert audio file to Opus format.
        
        Args:
            input_path: Path to input audio file
            output_path: Path to output Opus file
            
        Returns:
            Path to output file
            
        Raises:
            ConversionError: If conversion fails
        """
        if not input_path.exists():
            raise ConversionError(f"Input file not found: {input_path}")
        
        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Build FFmpeg command
        cmd = [
            'ffmpeg',
            '-i', str(input_path),          # Input file
            '-c:a', 'libopus',               # Use Opus codec
            '-b:a', self.bitrate,            # Bitrate
            '-vbr', 'on',                    # Variable bitrate
            '-compression_level', str(self.compression_level),
            '-ar', str(self.sample_rate),   # Sample rate
            '-ac', '2',                      # Stereo
            '-map_metadata', '0',            # Copy metadata
            '-y',                            # Overwrite output file
            str(output_path)
        ]
        
        try:
            self.logger.debug(f"Converting {input_path.name} to Opus...")
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,  # 5 minute timeout
                check=True
            )
            
            # Verify output file was created and has content
            if not output_path.exists():
                raise ConversionError("Output file was not created")
            
            if output_path.stat().st_size == 0:
                output_path.unlink()
                raise ConversionError("Output file is empty")
            
            self.logger.debug(f"Successfully converted to: {output_path}")
            return output_path
            
        except subprocess.CalledProcessError as e:
            # Clean up failed output
            if output_path.exists():
                output_path.unlink()
            
            error_msg = e.stderr if e.stderr else str(e)
            raise ConversionError(f"FFmpeg conversion failed: {error_msg}")
            
        except subprocess.TimeoutExpired:
            # Clean up on timeout
            if output_path.exists():
                output_path.unlink()
            raise ConversionError("Conversion timed out")
            
        except Exception as e:
            # Clean up on any other error
            if output_path.exists():
                output_path.unlink()
            raise ConversionError(f"Unexpected error during conversion: {e}")
    
    def get_audio_info(self, file_path: Path) -> Optional[dict]:
        """
        Get audio file information using ffprobe.
        
        Args:
            file_path: Path to audio file
            
        Returns:
            Dictionary with audio info or None on error
        """
        cmd = [
            'ffprobe',
            '-v', 'error',
            '-show_entries', 'format=duration,bit_rate:stream=codec_name,sample_rate,channels',
            '-of', 'json',
            str(file_path)
        ]
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=10,
                check=True
            )
            
            import json
            return json.loads(result.stdout)
            
        except Exception as e:
            self.logger.warning(f"Failed to get audio info: {e}")
            return None
