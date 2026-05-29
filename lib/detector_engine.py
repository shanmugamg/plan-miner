import cv2
import numpy as np
import os

class ColorDetectorEngine:
    @staticmethod
    def extract_template_from_click(img_bgr, cx, cy, patch_size=60):
        """
        Crops a patch around (cx, cy) from img_bgr and extracts its HSV color profile.
        Assumes the clicked object has a colored foreground on a neutral background.
        """
        h_img, w_img = img_bgr.shape[:2]
        
        # Calculate bounding coordinates for the crop patch
        x1 = max(0, cx - patch_size // 2)
        y1 = max(0, cy - patch_size // 2)
        x2 = min(w_img, cx + patch_size // 2)
        y2 = min(h_img, cy + patch_size // 2)
        
        patch_bgr = img_bgr[y1:y2, x1:x2].copy()
        if patch_bgr.size == 0:
            raise ValueError("Clicked region is outside the image boundaries.")
            
        patch_hsv = cv2.cvtColor(patch_bgr, cv2.COLOR_BGR2HSV)
        pixels = patch_hsv.reshape(-1, 3)
        
        # Filter out background pixels:
        # Avoid neutral white (V > 230, S < 25), black (V < 40), or light gray
        fg_mask = (pixels[:, 1] > 25) & (pixels[:, 2] > 40) & (pixels[:, 2] < 250)
        fg_pixels = pixels[fg_mask]
        
        if len(fg_pixels) < 10:
            # Fallback if there are very few colored pixels: take everything except bright white
            fg_mask_fallback = (pixels[:, 1] > 10) & (pixels[:, 2] > 20)
            fg_pixels = pixels[fg_mask_fallback]
            
        if len(fg_pixels) == 0:
            raise ValueError("No distinct colored pixels detected in the clicked region. Please click on a colored symbol.")
            
        # Get HSV limits using percentiles to discard outliers
        h_vals = fg_pixels[:, 0]
        s_vals = fg_pixels[:, 1]
        v_vals = fg_pixels[:, 2]
        
        # Hue wraps around 180 in OpenCV. We find the circular shift S that minimizes
        # the linear range of shifted hue values to correctly handle wrapping (e.g., for red).
        best_range = 180
        best_min = 0
        best_max = 180
        best_shift = 0
        for shift in range(180):
            shifted = (h_vals + shift) % 180
            h_min_s = np.percentile(shifted, 2)
            h_max_s = np.percentile(shifted, 98)
            r = h_max_s - h_min_s
            if r < best_range:
                best_range = r
                best_min = h_min_s
                best_max = h_max_s
                best_shift = shift

        h_min = int(best_min - best_shift) % 180
        h_max = int(best_max - best_shift) % 180
        s_min, s_max = int(np.percentile(s_vals, 2)), int(np.percentile(s_vals, 98))
        v_min, v_max = int(np.percentile(v_vals, 2)), int(np.percentile(v_vals, 98))
        
        # Expand bounds slightly to be more inclusive initially
        if h_min <= h_max:
            h_min = max(0, h_min - 8)
            h_max = min(180, h_max + 8)
        else:
            h_min = (h_min - 8) % 180
            h_max = (h_max + 8) % 180
            
        s_min = max(30, s_min - 20)
        s_max = min(255, s_max + 20)
        v_min = max(30, v_min - 25)
        v_max = min(255, v_max + 25)
        
        # Re-mask patch to calculate size metrics of the foreground
        lower_bound = np.array([h_min, s_min, v_min])
        upper_bound = np.array([h_max, s_max, v_max])
        if h_min <= h_max:
            mask = cv2.inRange(patch_hsv, lower_bound, upper_bound)
        else:
            lower_1 = np.array([h_min, s_min, v_min])
            upper_1 = np.array([180, s_max, v_max])
            mask1 = cv2.inRange(patch_hsv, lower_1, upper_1)
            
            lower_2 = np.array([0, s_min, v_min])
            upper_2 = np.array([h_max, s_max, v_max])
            mask2 = cv2.inRange(patch_hsv, lower_2, upper_2)
            
            mask = cv2.bitwise_or(mask1, mask2)
        
        # Calculate bounding box of the foreground object inside the patch
        coords = np.argwhere(mask > 0)
        if len(coords) > 0:
            y_indices, x_indices = coords[:, 0], coords[:, 1]
            t_w = int(x_indices.max() - x_indices.min() + 1)
            t_h = int(y_indices.max() - y_indices.min() + 1)
            t_area = int(np.sum(mask > 0))
        else:
            # Fallback to patch dimensions
            t_w = patch_bgr.shape[1]
            t_h = patch_bgr.shape[0]
            t_area = int(t_w * t_h)
            
        template_info = {
            "lower_bound": lower_bound.tolist(),
            "upper_bound": upper_bound.tolist(),
            "width": t_w,
            "height": t_h,
            "area": t_area,
            "patch_bgr": patch_bgr,
            "patch_mask": mask
        }
        
        return template_info
    @classmethod
    def detect_objects(cls, img_bgr, template_info, tolerance=0.5, proximity=100.0, min_area_scale=0.1, max_area_scale=5.0):
        """
        Detects colored objects in target img_bgr matching the template properties.
        """
        h_img, w_img = img_bgr.shape[:2]
        
        lower_bound = np.array(template_info["lower_bound"])
        upper_bound = np.array(template_info["upper_bound"])
        
        # Dynamically scale bounds based on tolerance slider (0.0 to 1.0)
        # Tolerance modifies range expansion
        h_tol = int(tolerance * 15)
        s_tol = int(tolerance * 40)
        v_tol = int(tolerance * 50)
        
        if lower_bound[0] <= upper_bound[0]:
            lower_bound[0] = max(0, lower_bound[0] - h_tol)
            upper_bound[0] = min(180, upper_bound[0] + h_tol)
        else:
            lower_bound[0] = (lower_bound[0] - h_tol) % 180
            upper_bound[0] = (upper_bound[0] + h_tol) % 180
            
        lower_bound[1] = max(10, lower_bound[1] - s_tol)
        upper_bound[1] = min(255, upper_bound[1] + s_tol)
        lower_bound[2] = max(10, lower_bound[2] - v_tol)
        upper_bound[2] = min(255, upper_bound[2] + v_tol)
        
        hsv = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2HSV)
        
        if lower_bound[0] <= upper_bound[0]:
            mask = cv2.inRange(hsv, lower_bound, upper_bound)
        else:
            lower_1 = np.array([lower_bound[0], lower_bound[1], lower_bound[2]])
            upper_1 = np.array([180, upper_bound[1], upper_bound[2]])
            mask1 = cv2.inRange(hsv, lower_1, upper_1)
            
            lower_2 = np.array([0, lower_bound[1], lower_bound[2]])
            upper_2 = np.array([upper_bound[0], upper_bound[1], upper_bound[2]])
            mask2 = cv2.inRange(hsv, lower_2, upper_2)
            
            mask = cv2.bitwise_or(mask1, mask2)
        
        num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(mask)
        
        # Calculate allowed area based on template area
        t_area = template_info["area"]
        min_allowed_area = max(10, int(t_area * min_area_scale))
        max_allowed_area = int(t_area * max_area_scale)
        
        candidate_indices = []
        for i in range(1, num_labels):
            area = stats[i][4]
            if min_allowed_area <= area <= max_allowed_area:
                candidate_indices.append(i)
                
        # Group candidates based on spatial proximity using grid buckets
        # This was reverted to the Python BFS approach to maintain 100% detection accuracy.
        # Morphological closing aggressively distorted the area and aspect ratio of components,
        # leading to false positive fragment detections.
        cell_size = max(1.0, float(proximity))
        grid = {}
        for idx in candidate_indices:
            cx, cy = centroids[idx]
            gx = int(cx // cell_size)
            gy = int(cy // cell_size)
            grid.setdefault((gx, gy), []).append(idx)

        adj = {i: [] for i in candidate_indices}
        for idx_i in candidate_indices:
            cx_i, cy_i = centroids[idx_i]
            gx = int(cx_i // cell_size)
            gy = int(cy_i // cell_size)
            for dx in (-1, 0, 1):
                for dy in (-1, 0, 1):
                    neighbors = grid.get((gx + dx, gy + dy), [])
                    for idx_j in neighbors:
                        if idx_j <= idx_i:
                            continue
                        cx_j, cy_j = centroids[idx_j]
                        dist = np.sqrt((cx_i - cx_j)**2 + (cy_i - cy_j)**2)
                        if dist < proximity:
                            adj[idx_i].append(idx_j)
                            adj[idx_j].append(idx_i)
                    
        visited = set()
        clusters = []
        for node in candidate_indices:
            if node not in visited:
                cluster = []
                queue = [node]
                visited.add(node)
                while queue:
                    curr = queue.pop(0)
                    cluster.append(curr)
                    for neighbor in adj[curr]:
                        if neighbor not in visited:
                            visited.add(neighbor)
                            queue.append(neighbor)
                clusters.append(cluster)
                
        detections = []
        detection_id = 1
        
        # Sort clusters top-to-bottom, then left-to-right
        def get_cluster_pos(cluster):
            lefts = [stats[c][0] for c in cluster]
            tops = [stats[c][1] for c in cluster]
            return (min(tops), min(lefts))
            
        clusters.sort(key=get_cluster_pos)
        
        for cluster in clusters:
            lefts = [stats[c][0] for c in cluster]
            tops = [stats[c][1] for c in cluster]
            rights = [stats[c][0] + stats[c][2] for c in cluster]
            bottoms = [stats[c][1] + stats[c][3] for c in cluster]
            
            c_left = min(lefts)
            c_top = min(tops)
            c_right = max(rights)
            c_bottom = max(bottoms)
            c_w = c_right - c_left
            c_h = c_bottom - c_top
            c_area = sum([stats[c][4] for c in cluster])
            
            cx = int(c_left + c_w / 2)
            cy = int(c_top + c_h / 2)
            
            # Simple shape filter: reject extremely skinny blobs if template is mostly square-ish
            t_aspect = max(0.1, float(template_info["width"]) / float(template_info["height"]))
            c_aspect = float(c_w) / max(1, float(c_h))
            aspect_ratio_diff = abs(c_aspect - t_aspect)
            
            # Check aspect ratio discrepancy
            if aspect_ratio_diff > 4.0:
                continue
                
            detections.append({
                "id": detection_id,
                "bbox": (c_left, c_top, c_w, c_h),
                "centroid": (cx, cy),
                "area": c_area
            })
            detection_id += 1
            
        return detections, mask
