#!/usr/bin/env python3
import os

from PIL import Image


def generate_favicons():
    # Use black for the foreground color
    foreground_color = (0, 0, 0)  # Black color for foreground

    # Load the PNG image
    png_path = os.path.join("static", "img", "brandmark-design.png")
    original_img = Image.open(png_path).convert("RGBA")

    # Create a solid black image with the same dimensions and alpha channel
    width, height = original_img.size
    black_img = Image.new("RGBA", (width, height), (0, 0, 0, 0))

    # Copy the alpha channel from original to the black image
    for x in range(width):
        for y in range(height):
            r, g, b, a = original_img.getpixel((x, y))
            if a > 0:  # If not completely transparent
                black_img.putpixel((x, y), (foreground_color[0], foreground_color[1], foreground_color[2], a))

    # Ensure the static/img/favicon directory exists
    favicon_dir = os.path.join("static", "img", "favicon")
    os.makedirs(favicon_dir, exist_ok=True)

    # Define sizes for various devices and platforms (reduced max size)
    ico_sizes = [16, 32, 48]
    png_sizes = [16, 32, 48, 64, 96, 128]

    # Generate ICO file with multiple sizes
    favicon_images = []

    for size in ico_sizes:
        # Create a new transparent image
        new_img = Image.new("RGBA", (size, size), (0, 0, 0, 0))

        # Resize the black image
        resized = black_img.resize((size, size), Image.Resampling.LANCZOS)

        # Paste it onto the transparent background
        new_img.paste(resized, (0, 0), resized)

        if size <= 32:  # Small sizes need special handling for ICO format
            new_img = new_img.convert("RGB")

        favicon_images.append(new_img)

    # Save ICO file
    ico_path = os.path.join("static", "img", "favicon.ico")
    favicon_images[0].save(ico_path, format="ICO", sizes=[(s, s) for s in ico_sizes], append_images=favicon_images[1:])
    print(f"ICO favicon generated at {ico_path}")

    # Generate PNG files at various sizes
    for size in png_sizes:
        # Create a new transparent image
        new_img = Image.new("RGBA", (size, size), (0, 0, 0, 0))

        # Resize the black image
        resized = black_img.resize((size, size), Image.Resampling.LANCZOS)

        # Paste it onto the transparent background
        new_img.paste(resized, (0, 0), resized)

        # Save PNG file
        png_path = os.path.join(favicon_dir, f"favicon-{size}x{size}.png")
        new_img.save(png_path, format="PNG")
        print(f"Generated {png_path}")

    # Create Apple touch icons (iOS needs non-transparent background)
    apple_sizes = [57, 60, 76, 120]
    for size in apple_sizes:
        # Create a white background
        new_img = Image.new("RGB", (size, size), (255, 255, 255))

        # Resize the black image
        resized = black_img.resize((size, size), Image.Resampling.LANCZOS)

        # Paste it onto the white background (using alpha channel as mask)
        new_img.paste(resized, (0, 0), resized)

        # Save PNG file
        apple_path = os.path.join(favicon_dir, f"apple-touch-icon-{size}x{size}.png")
        new_img.save(apple_path, format="PNG")
        print(f"Generated {apple_path}")

    print("High-resolution favicons generated successfully")


if __name__ == "__main__":
    generate_favicons()
