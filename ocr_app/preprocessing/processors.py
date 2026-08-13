"""
Image processing classes for OCR preprocessing.
Implements various enhancement techniques for historical documents.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Optional, Union

import numpy as np
from PIL import Image


@dataclass
class ProcessorConfig:
    """Configuration for image processors."""
    enabled: bool = True
    parameters: dict = None
    
    def __post_init__(self):
        if self.parameters is None:
            self.parameters = {}


class ImageProcessor(ABC):
    """Abstract base class for image processors."""
    
    def __init__(self, config: Optional[ProcessorConfig] = None):
        """
        Initialize the processor.
        
        Args:
            config: Processor configuration.
        """
        self.config = config or ProcessorConfig()
        self.name = self.__class__.__name__
    
    @abstractmethod
    def process(self, image: Image.Image) -> Image.Image:
        """
        Process an image.
        
        Args:
            image: Input PIL Image.
            
        Returns:
            Processed PIL Image.
        """
        pass
    
    def apply(self, image: Image.Image) -> Image.Image:
        """
        Apply processing if enabled.
        
        Args:
            image: Input PIL Image.
            
        Returns:
            Processed or original PIL Image.
        """
        if self.config.enabled:
            return self.process(image)
        return image


class DenoiseProcessor(ImageProcessor):
    """Denoise processor using non-local means or bilateral filtering."""
    
    def __init__(self, config: Optional[ProcessorConfig] = None):
        """Initialize denoise processor."""
        default_params = {
            "method": "bilateral",  # 'bilateral' or 'nlmeans'
            "strength": 10,
            "template_size": 7,
            "search_window": 21,
        }
        if config is None:
            config = ProcessorConfig(parameters=default_params)
        elif config.parameters is None:
            config.parameters = default_params
        else:
            config.parameters = {**default_params, **config.parameters}
        
        super().__init__(config)
    
    def process(self, image: Image.Image) -> Image.Image:
        """
        Apply denoising to the image.
        
        Args:
            image: Input PIL Image.
            
        Returns:
            Denoised PIL Image.
        """
        try:
            import cv2
            
            # Convert to numpy array
            img_array = np.array(image)
            
            # Convert to BGR for OpenCV if RGB
            if len(img_array.shape) == 3 and img_array.shape[2] == 3:
                img_array = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
            
            method = self.config.parameters.get("method", "bilateral")
            strength = self.config.parameters.get("strength", 10)
            
            if method == "bilateral":
                # Bilateral filter - preserves edges
                d = self.config.parameters.get("template_size", 7)
                sigma_color = strength
                sigma_space = strength
                
                if len(img_array.shape) == 3:
                    processed = cv2.bilateralFilter(img_array, d, sigma_color, sigma_space)
                else:
                    processed = cv2.bilateralFilter(img_array, d, sigma_color, sigma_space)
            
            elif method == "nlmeans":
                # Non-local means denoising
                h = strength
                template_size = self.config.parameters.get("template_size", 7)
                search_window = self.config.parameters.get("search_window", 21)
                
                if len(img_array.shape) == 3:
                    processed = cv2.fastNlMeansDenoisingColored(
                        img_array, None, h, h, template_size, search_window
                    )
                else:
                    processed = cv2.fastNlMeansDenoising(
                        img_array, None, h, template_size, search_window
                    )
            else:
                processed = img_array
            
            # Convert back to RGB if needed
            if len(processed.shape) == 3 and processed.shape[2] == 3:
                processed = cv2.cvtColor(processed, cv2.COLOR_BGR2RGB)
            
            return Image.fromarray(processed)
            
        except ImportError:
            # OpenCV not available, return original
            return image
        except Exception:
            # Any error, return original
            return image


class BinarizationProcessor(ImageProcessor):
    """Binarization processor using Otsu or adaptive thresholding."""
    
    def __init__(self, config: Optional[ProcessorConfig] = None):
        """Initialize binarization processor."""
        default_params = {
            "method": "otsu",  # 'otsu', 'adaptive', or 'simple'
            "threshold": 127,
            "block_size": 11,
            "c_value": 2,
        }
        if config is None:
            config = ProcessorConfig(parameters=default_params)
        elif config.parameters is None:
            config.parameters = default_params
        else:
            config.parameters = {**default_params, **config.parameters}
        
        super().__init__(config)
    
    def process(self, image: Image.Image) -> Image.Image:
        """
        Apply binarization to the image.
        
        Args:
            image: Input PIL Image.
            
        Returns:
            Binarized PIL Image.
        """
        try:
            import cv2
            
            # Convert to grayscale
            img_array = np.array(image.convert('L'))
            
            method = self.config.parameters.get("method", "otsu")
            
            if method == "otsu":
                # Otsu's thresholding
                _, processed = cv2.threshold(
                    img_array, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU
                )
            
            elif method == "adaptive":
                # Adaptive thresholding
                block_size = self.config.parameters.get("block_size", 11)
                c_value = self.config.parameters.get("c_value", 2)
                
                # Block size must be odd
                if block_size % 2 == 0:
                    block_size += 1
                
                processed = cv2.adaptiveThreshold(
                    img_array, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                    cv2.THRESH_BINARY, block_size, c_value
                )
            
            elif method == "simple":
                # Simple thresholding
                threshold = self.config.parameters.get("threshold", 127)
                _, processed = cv2.threshold(
                    img_array, threshold, 255, cv2.THRESH_BINARY
                )
            else:
                processed = img_array
            
            return Image.fromarray(processed)
            
        except ImportError:
            return image
        except Exception:
            return image


class CLAHEProcessor(ImageProcessor):
    """Contrast Limited Adaptive Histogram Equalization processor."""
    
    def __init__(self, config: Optional[ProcessorConfig] = None):
        """Initialize CLAHE processor."""
        default_params = {
            "clip_limit": 2.0,
            "tile_grid_size": (8, 8),
        }
        if config is None:
            config = ProcessorConfig(parameters=default_params)
        elif config.parameters is None:
            config.parameters = default_params
        else:
            config.parameters = {**default_params, **config.parameters}
        
        super().__init__(config)
    
    def process(self, image: Image.Image) -> Image.Image:
        """
        Apply CLAHE to the image.
        
        Args:
            image: Input PIL Image.
            
        Returns:
            Enhanced PIL Image.
        """
        try:
            import cv2
            
            # Convert to grayscale
            img_array = np.array(image.convert('L'))
            
            clip_limit = self.config.parameters.get("clip_limit", 2.0)
            tile_grid_size = self.config.parameters.get("tile_grid_size", (8, 8))
            
            clahe = cv2.createCLAHE(clipLimit=clip_limit, tileGridSize=tile_grid_size)
            processed = clahe.apply(img_array)
            
            return Image.fromarray(processed)
            
        except ImportError:
            return image
        except Exception:
            return image


class DeskewProcessor(ImageProcessor):
    """Deskew processor to correct image rotation."""
    
    def __init__(self, config: Optional[ProcessorConfig] = None):
        """Initialize deskew processor."""
        default_params = {
            "delta": 1.0,
            "limit": 5.0,  # Maximum rotation angle in degrees
        }
        if config is None:
            config = ProcessorConfig(parameters=default_params)
        elif config.parameters is None:
            config.parameters = default_params
        else:
            config.parameters = {**default_params, **config.parameters}
        
        super().__init__(config)
    
    def process(self, image: Image.Image) -> Image.Image:
        """
        Deskew the image by detecting and correcting rotation.
        
        Args:
            image: Input PIL Image.
            
        Returns:
            Deskewed PIL Image.
        """
        try:
            import cv2
            
            # Convert to grayscale
            img_array = np.array(image.convert('L'))
            
            limit = self.config.parameters.get("limit", 5.0)
            
            # Calculate skew angle using moments
            coords = np.column_stack(np.where(img_array > 0))
            
            if len(coords) == 0:
                return image
            
            angle = cv2.minAreaRect(coords)[-1]
            
            # Adjust angle based on quadrant
            if angle < -45:
                angle = -(90 + angle)
            else:
                angle = -angle
            
            # Limit the rotation angle
            if abs(angle) > limit:
                angle = limit if angle > 0 else -limit
            
            # Skip if angle is too small
            if abs(angle) < 0.1:
                return image
            
            # Rotate image
            (h, w) = img_array.shape[:2]
            center = (w // 2, h // 2)
            matrix = cv2.getRotationMatrix2D(center, angle, 1.0)
            
            processed = cv2.warpAffine(
                img_array, matrix, (w, h),
                flags=cv2.INTER_CUBIC,
                borderMode=cv2.BORDER_REPLICATE
            )
            
            return Image.fromarray(processed)
            
        except ImportError:
            return image
        except Exception:
            return image


class ContrastProcessor(ImageProcessor):
    """Simple contrast enhancement processor."""
    
    def __init__(self, config: Optional[ProcessorConfig] = None):
        """Initialize contrast processor."""
        default_params = {
            "factor": 1.2,  # Contrast factor (>1 increases contrast)
            "brightness": 0,  # Brightness adjustment
        }
        if config is None:
            config = ProcessorConfig(parameters=default_params)
        elif config.parameters is None:
            config.parameters = default_params
        else:
            config.parameters = {**default_params, **config.parameters}
        
        super().__init__(config)
    
    def process(self, image: Image.Image) -> Image.Image:
        """
        Enhance contrast of the image.
        
        Args:
            image: Input PIL Image.
            
        Returns:
            Enhanced PIL Image.
        """
        from PIL import ImageEnhance
        
        factor = self.config.parameters.get("factor", 1.2)
        brightness = self.config.parameters.get("brightness", 0)
        
        # Apply contrast enhancement
        enhancer = ImageEnhance.Contrast(image)
        enhanced = enhancer.enhance(factor)
        
        # Apply brightness enhancement
        if brightness != 0:
            enhancer = ImageEnhance.Brightness(enhanced)
            enhanced = enhancer.enhance(1.0 + brightness / 100.0)
        
        return enhanced
