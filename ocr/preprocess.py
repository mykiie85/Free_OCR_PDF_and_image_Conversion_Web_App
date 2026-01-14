import cv2
import numpy as np


class ImagePreprocessor:
    
    
    def preprocess(self, image, method='advanced'):
        
        # Convert to grayscale
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image.copy()
        
        # Use advanced preprocessing by default for better quality
        if method == 'advanced':
            return self._advanced_preprocess(gray)
        
        # Denoise
        denoised = cv2.fastNlMeansDenoising(gray, None, 10, 7, 21)
        
        # Apply thresholding based on method
        if method == 'adaptive':
            processed = cv2.adaptiveThreshold(
                denoised,
                255,
                cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                cv2.THRESH_BINARY,
                11,
                2
            )
        elif method == 'otsu':
            _, processed = cv2.threshold(
                denoised,
                0,
                255,
                cv2.THRESH_BINARY + cv2.THRESH_OTSU
            )
        else:
            _, processed = cv2.threshold(denoised, 127, 255, cv2.THRESH_BINARY)
        
        # Deskew if needed
        processed = self._deskew(processed)
        
        return processed
    
    def _advanced_preprocess(self, gray):
        
        # Step 1: Increase contrast using CLAHE
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(gray)
        
        # Step 2: Denoise more aggressively
        denoised = cv2.fastNlMeansDenoising(enhanced, None, h=10, templateWindowSize=7, searchWindowSize=21)
        
        # Step 3: Increase sharpness
        sharpened = self._sharpen_image(denoised)
        
        # Step 4: Adaptive thresholding with better parameters
        binary = cv2.adaptiveThreshold(
            sharpened,
            255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY,
            blockSize=15,  # Larger block size for better local adaptation
            C=8  # Adjusted constant
        )
        
        # Step 5: Morphological operations to clean up
        kernel = np.ones((2, 2), np.uint8)
        cleaned = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel, iterations=1)
        
        # Step 6: Deskew
        deskewed = self._deskew(cleaned)
        
        # Step 7: Final noise removal
        final = cv2.medianBlur(deskewed, 3)
        
        return final
    
    def _sharpen_image(self, image):
        
        # Create sharpening kernel
        kernel = np.array([[-1, -1, -1],
                          [-1,  9, -1],
                          [-1, -1, -1]])
        sharpened = cv2.filter2D(image, -1, kernel)
        return sharpened
    
    def _deskew(self, image):
        
        try:
            # Detect edges
            edges = cv2.Canny(image, 50, 150, apertureSize=3)
            
            # Detect lines
            lines = cv2.HoughLinesP(edges, 1, np.pi / 180, threshold=100, 
                                   minLineLength=100, maxLineGap=10)
            
            if lines is not None and len(lines) > 5:
                # Calculate angles
                angles = []
                for line in lines:
                    x1, y1, x2, y2 = line[0]
                    angle = np.degrees(np.arctan2(y2 - y1, x2 - x1))
                    # Normalize angle
                    if angle < -45:
                        angle = 90 + angle
                    elif angle > 45:
                        angle = angle - 90
                    angles.append(angle)
                
                # Get median angle
                median_angle = np.median(angles)
                
                # Only rotate if angle is significant
                if abs(median_angle) > 0.3:
                    # Rotate image
                    h, w = image.shape
                    center = (w // 2, h // 2)
                    M = cv2.getRotationMatrix2D(center, median_angle, 1.0)
                    rotated = cv2.warpAffine(
                        image, 
                        M, 
                        (w, h), 
                        flags=cv2.INTER_CUBIC, 
                        borderMode=cv2.BORDER_REPLICATE
                    )
                    return rotated
        except Exception as e:
            print(f"Deskew warning: {e}")
        
        return image
    
    def enhance_contrast(self, image):
        
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(image)
        return enhanced
    
    def remove_noise(self, image):
        
        kernel = np.ones((2, 2), np.uint8)
        opening = cv2.morphologyEx(image, cv2.MORPH_OPEN, kernel)
        return opening
    
    def resize_for_ocr(self, image, target_dpi=300):
    
        h, w = image.shape[:2]
        
        # If image is too small, upscale it
        if h < 1000 or w < 1000:
            scale_factor = 2.0
            new_w = int(w * scale_factor)
            new_h = int(h * scale_factor)
            resized = cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_CUBIC)
            return resized
        
        # If image is too large, optimize it
        elif h > 4000 or w > 4000:
            scale_factor = 0.75
            new_w = int(w * scale_factor)
            new_h = int(h * scale_factor)
            resized = cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_AREA)
            return resized
        
        return image