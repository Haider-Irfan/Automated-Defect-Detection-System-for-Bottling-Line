import os
from PIL import Image, ImageDraw
import numpy as np
import matplotlib.pyplot as plt

def is_red(pixel, threshold=100):
    
    r, g, b = pixel
    return r > threshold and g < threshold and b < threshold

def is_white(pixel, threshold=200):
    
    r, g, b = pixel
    return r > threshold and g > threshold and b > threshold

def is_black(pixel, threshold=50):
    
    r, g, b = pixel
    return r < threshold and g < threshold and b < threshold

def is_dark(pixel, threshold=100):
    
    r, g, b = pixel
    return r < threshold and g < threshold and b < threshold

def check_cap_presence(image, cap_positions, threshold=500):

    pixels = np.array(image)
    cap_status = []
    
    for x, y, w, h in cap_positions:
        cap_region = pixels[y:y+h, x:x+w]
        red_pixels = sum(is_red(pixel) for row in cap_region for pixel in row)

        if red_pixels > threshold:
            status = "Cap Present "
            color = "green"
        else:
            status = "Cap Missing "
            color = "red"
        
        cap_status.append((red_pixels, status, (x, y, w, h, color)))
    
    return cap_status

def analyze_label_region(image, cap_positions):
    
    pixels = np.array(image)
    label_status = []
    
    for x, y, w, h in cap_positions:
        cap_region = pixels[y:y+h, x:x+w]
        total_pixels = w * h
        
        red_pixels = sum(is_red(pixel) for row in cap_region for pixel in row)
        white_pixels = sum(is_white(pixel) for row in cap_region for pixel in row)
        black_pixels = sum(is_black(pixel) for row in cap_region for pixel in row)
        
        red_ratio = red_pixels / total_pixels
        white_ratio = white_pixels / total_pixels
        black_ratio = black_pixels / total_pixels

        if white_ratio > 0.4 or black_ratio > 0.4 or red_ratio < 0.01:
            status = "Label Missing "
            color = "red"
        elif black_ratio > 0.2 or white_ratio > 0.1:
            status = "Possible Printing Defect "
            color = "orange"
        else:
            status = "Label is OK "
            color = "blue"
        
        label_status.append((red_ratio, white_ratio, black_ratio, status, (x, y, w, h, color)))
    
    return label_status

def check_fill_level(image, liquid_positions):
    
    pixels = np.array(image)
    fill_levels = []
    
    for x, y, w, h in liquid_positions:
        liquid_region = pixels[y:y+h, x:x+w]
        total_pixels = w * h
        dark_pixels = sum(is_dark(pixel) for row in liquid_region for pixel in row)
        
        fill_ratio = dark_pixels / total_pixels
        
        # manually test the number ofopixel and put the values here 
        if fill_ratio > 0.47:
            status = "Overfilled "
            color = "red"
        elif 0.42 < fill_ratio <= 0.47:
            status = "Properly Filled "
            color = "green"
        elif 0.001 < fill_ratio <= 0.41:
            status = "Underfilled "
            color = "orange"
        else:
            status = "Empty "
            color = "blue"
        
        fill_levels.append((fill_ratio, status, (x, y, w, h, color)))
    
    return fill_levels

def detect_label_alignment(image, label_position1, label_position2):
    
    x1, y1, w1, h1 = label_position1
    x2, y2, w2, h2 = label_position2

    pixels = np.array(image)

    def count_colors(img):
        red_pixels = np.sum((img[:, :, 0] > 150) & (img[:, :, 1] < 100) & (img[:, :, 2] < 100))
        black_pixels = np.sum((img[:, :, 0] < 50) & (img[:, :, 1] < 50) & (img[:, :, 2] < 50))
        white_pixels = np.sum((img[:, :, 0] > 200) & (img[:, :, 1] > 200) & (img[:, :, 2] > 200))
        return red_pixels, black_pixels, white_pixels

    red, black, white = count_colors(pixels)

    def is_aligned(red, black, white):
        total = red + black + white
        if total == 0:
            return False
        red_ratio = red / total
        black_ratio = black / total
        white_ratio = white / total

        return 0.03 < red_ratio < 0.85 and 0.03 < black_ratio < 0.27 and 0.017 < white_ratio < 0.3

    is_properly_aligned = is_aligned(red, black, white)
    status = "Properly Aligned" if is_properly_aligned else "Misaligned"
    color = "green" if is_properly_aligned else "red"

    return [(None, status, (x1, y1, w1, h1, color)), 
            (None, status, (x2, y2, w2, h2, color))]


def process_images_in_folder(folder_path):
    
    image_files = [f for f in os.listdir(folder_path) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]

    if not image_files:
        print("No images found in the given folder!!!")
        return

    for image_file in image_files:
        image_path = os.path.join(folder_path, image_file)

        image = Image.open(image_path)
        width, height = image.size

        cap_width = width // 5
        cap_height = (height // 8) + 5
        label_width = (width // 3) + 5
        label_height = height // 2
        liquid_width = width // 6
        liquid_height = (height // 3) - 8
        label_position1 = (image.width // 2.9, image.height // 1.04, 110, 10)
        label_position2 = (image.width // 2.9, image.height // 1.62, 110, 10)

        cap_positions = [(width // 2 - cap_width // 2, height // 30, cap_width, cap_height)]
        label_positions = [(width // 2 - label_width // 2, height // 2, label_width, label_height)]
        liquid_positions = [(width // 2 - liquid_width // 2, height // 3, liquid_width, liquid_height)]

        cap_results = check_cap_presence(image, cap_positions)
        label_results = analyze_label_region(image, label_positions)
        fill_results = check_fill_level(image, liquid_positions)
        alignment_results = detect_label_alignment(image, label_position1, label_position2)

        draw = ImageDraw.Draw(image)
        
        #Also making frames on the image the where the detecting window is placed
        
        for x, y, w, h, color in [data[2] for data in cap_results]:
         draw.rectangle([x, y, x + w, y + h], outline=color, width=3)

        for x, y, w, h, color in [data[4] for data in label_results]:
         draw.rectangle([x, y, x + w, y + h], outline=color, width=3)

        for x, y, w, h, color in [data[2] for data in fill_results]:
         draw.rectangle([x, y, x + w, y + h], outline=color, width=3)

        for x, y, w, h, color in [data[2] for data in alignment_results]:
         draw.rectangle([x, y, x + w, y + h], outline=color, width=3)


        cap_status = cap_results[0][1]
        label_status = label_results[0][3]
        fill_status = fill_results[0][1]
        alignment_status = alignment_results[0][1]

        issue_messages = []

        # Only add messages if there is a problem
        if "Missing" in cap_status:
            issue_messages.append(cap_status)
        if "Defect" in label_status or "Label Missing" in label_status:
            issue_messages.append(label_status)
        if "Underfilled" in fill_status or "Overfilled" in fill_status or "Empty" in fill_status:
            issue_messages.append(fill_status)  # 🔹 Now checks for "Empty" too
        if "Misaligned" in alignment_status:
            issue_messages.append(alignment_status)

        # If no issues found, set "No Issue"
        if not issue_messages:
            issue_messages = ["No Issue"]

        plt.figure(figsize=(8, 6))
        plt.imshow(np.array(image))
        plt.axis("off")
        plt.title(" | ".join(issue_messages))
        plt.show()

        print("\nProcessing Image: " + image_file)
        for msg in issue_messages:
            print(msg)
        print("\n")


folder_path = r"C:/Users/IAT/Desktop/5th Semester/Image processing/Project Dataset"

process_images_in_folder(folder_path)