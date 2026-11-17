
from pathlib import Path
from PIL import Image, ImageOps
import os

# Original photographs
source_folder = Path("images")

# New compressed copies
output_folder = Path("web_images")

output_folder.mkdir(exist_ok=True)

extensions = {".jpg", ".jpeg"}

files = [
    p for p in source_folder.rglob("*")
    if p.is_file() and p.suffix.lower() in extensions
]

print("Total photographs:", len(files))

success = 0
failed = 0

for index, photo in enumerate(files, start=1):

    try:
        with Image.open(photo) as img:

            # Correct photo orientation
            img = ImageOps.exif_transpose(img)

            # Resize for online display
            img.thumbnail((1200, 1200), Image.Resampling.LANCZOS)

            # Preserve folder structure
            relative_path = photo.relative_to(source_folder)
            destination = output_folder / relative_path

            destination.parent.mkdir(
                parents=True,
                exist_ok=True
            )

            # Save compressed JPEG copy
            if img.mode not in ("RGB", "L"):
                img = img.convert("RGB")

            img.save(
                destination.with_suffix(".jpg"),
                "JPEG",
                quality=82,
                optimize=True
            )

            success += 1

    except Exception as error:
        print("Failed:", photo.name, error)
        failed += 1

    if index % 100 == 0:
        print(f"Processed {index}/{len(files)}")

print("\nCOMPRESSION FINISHED")
print("Successful:", success)
print("Failed:", failed)
print("Original photographs were not modified.")
print("Compressed copies:", output_folder.resolve())

input("Press Enter to close...")
