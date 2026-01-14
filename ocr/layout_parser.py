import cv2
import numpy as np
import pytesseract


class LayoutParser:
    
    
    def parse_layout(self, ocr_data):
    
        blocks = []
        
        try:
            n_boxes = len(ocr_data.get('text', []))
            if n_boxes == 0:
                return blocks
            
            current_block = {
                'lines': [],
                'top': 0,
                'left': 0,
                'width': 0
            }
            last_block_num = -1
            current_line = {'text': '', 'left': 0, 'top': 0, 'line_num': -1}
            
            for i in range(n_boxes):
                try:
                    # Safely get values
                    text = str(ocr_data.get('text', [''])[i]).strip() if i < len(ocr_data.get('text', [])) else ''
                    
                    conf_list = ocr_data.get('conf', [])
                    conf = int(conf_list[i]) if i < len(conf_list) and str(conf_list[i]).replace('-','').isdigit() else 0
                    
                    block_num = ocr_data.get('block_num', [])[i] if i < len(ocr_data.get('block_num', [])) else 0
                    line_num = ocr_data.get('line_num', [])[i] if i < len(ocr_data.get('line_num', [])) else 0
                    
                    # Skip low confidence and empty text
                    if conf < 30 or not text:
                        continue
                    
                    # Get position
                    top = ocr_data.get('top', [])[i] if i < len(ocr_data.get('top', [])) else 0
                    left = ocr_data.get('left', [])[i] if i < len(ocr_data.get('left', [])) else 0
                    width = ocr_data.get('width', [])[i] if i < len(ocr_data.get('width', [])) else 0
                    
                    # New block detected
                    if block_num != last_block_num:
                        # Save previous line and block
                        if current_line['text']:
                            current_block['lines'].append(current_line)
                        if current_block['lines']:
                            blocks.append(current_block)
                        
                        # Start new block
                        current_block = {
                            'lines': [],
                            'top': top,
                            'left': left,
                            'width': width
                        }
                        current_line = {'text': '', 'left': left, 'top': top, 'line_num': line_num}
                        last_block_num = block_num
                    
                    # New line within same block
                    if line_num != current_line['line_num'] and current_line['text']:
                        current_block['lines'].append(current_line)
                        current_line = {'text': '', 'left': left, 'top': top, 'line_num': line_num}
                    
                    # Add word to current line
                    if current_line['text']:
                        current_line['text'] += ' ' + text
                    else:
                        current_line['text'] = text
                        current_line['left'] = left
                        current_line['top'] = top
                        current_line['line_num'] = line_num
                    
                except Exception as e:
                    print(f"Error parsing item at index {i}: {e}")
                    continue
            
            # Save last line and block
            if current_line['text']:
                current_block['lines'].append(current_line)
            if current_block['lines']:
                blocks.append(current_block)
                
        except Exception as e:
            print(f"Error in parse_layout: {e}")
        
        return blocks
    
    def detect_tables(self, image):

        tables = []
        
        try:
            # Convert to grayscale
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            else:
                gray = image.copy()
            
            # Threshold
            _, thresh = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY_INV)
            
            # Detect horizontal and vertical lines
            horizontal_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (40, 1))
            vertical_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 40))
            
            horizontal_lines = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, horizontal_kernel)
            vertical_lines = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, vertical_kernel)
            
            # Combine lines
            table_mask = cv2.add(horizontal_lines, vertical_lines)
            
            # Find contours
            contours, _ = cv2.findContours(table_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            # Filter contours by size
            min_area = 5000
            for contour in contours:
                area = cv2.contourArea(contour)
                if area > min_area:
                    x, y, w, h = cv2.boundingRect(contour)
                    
                    # Extract table region
                    table_region = image[y:y+h, x:x+w]
                    
                    # Try to extract table data
                    table_data = self._extract_table_data(table_region)
                    
                    if table_data:
                        tables.append({
                            'x': x, 'y': y, 'w': w, 'h': h,
                            'rows': table_data
                        })
        
        except Exception as e:
            print(f"Table detection error: {e}")
        
        return tables
    
    def _extract_table_data(self, table_image):
        
        try:
            # Use Tesseract to get detailed data
            data = pytesseract.image_to_data(
                table_image, 
                lang='eng', 
                config='--psm 6',
                output_type=pytesseract.Output.DICT
            )
            
            # Group text by rows (similar y-coordinates)
            rows = {}
            n_boxes = len(data['text'])
            
            for i in range(n_boxes):
                if i >= len(data['text']):
                    continue
                    
                text = str(data['text'][i]).strip()
                
                # Check if conf exists and is valid
                if i >= len(data.get('conf', [])):
                    continue
                    
                try:
                    conf = int(data['conf'][i])
                except (ValueError, TypeError):
                    conf = 0
                
                if conf < 30 or not text:
                    continue
                
                # Safely get top and left values
                if i >= len(data.get('top', [])) or i >= len(data.get('left', [])):
                    continue
                    
                top = data['top'][i]
                left = data['left'][i]
                
                # Find or create row
                row_key = top // 20  # Group by 20px vertical bins
                if row_key not in rows:
                    rows[row_key] = []
                
                rows[row_key].append((left, text))
            
            # Sort rows and cells
            sorted_rows = []
            for row_key in sorted(rows.keys()):
                cells = rows[row_key]
                cells.sort(key=lambda x: x[0])  # Sort by x position
                sorted_rows.append([cell[1] for cell in cells])
            
            return sorted_rows if len(sorted_rows) > 1 else []
        
        except Exception as e:
            print(f"Table extraction error: {e}")
            return []