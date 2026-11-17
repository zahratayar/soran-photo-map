
import os
import html
from pathlib import Path
from urllib.parse import quote

import folium
import exifread
from folium.plugins import MarkerCluster


# ==================================================
# FOLDERS
# ==================================================

BASE = Path(__file__).resolve().parent

ORIGINAL = BASE / "images"
COMPRESSED = BASE / "web_images"

OUTPUT = BASE / "index.html"


# ==================================================
# CHECK FOLDERS
# ==================================================

if not ORIGINAL.exists() or not COMPRESSED.exists():
    raise SystemExit("ERROR: Images folder not found!")


# ==================================================
# GPS FUNCTIONS
# ==================================================

def decimal_gps(value, ref):

    try:
        d = float(value.values[0].num) / float(value.values[0].den)
        m = float(value.values[1].num) / float(value.values[1].den)
        s = float(value.values[2].num) / float(value.values[2].den)

        result = d + m / 60 + s / 3600

        if str(ref).strip().upper() in ("S", "W"):
            result = -result

        return result

    except Exception:
        return None


def get_gps(path):

    try:
        with open(path, "rb") as f:
            tags = exifread.process_file(f, details=False)

        lat = tags.get("GPS GPSLatitude")
        lat_ref = tags.get("GPS GPSLatitudeRef")
        lon = tags.get("GPS GPSLongitude")
        lon_ref = tags.get("GPS GPSLongitudeRef")

        if not all([lat, lat_ref, lon, lon_ref]):
            return None

        latitude = decimal_gps(lat, lat_ref)
        longitude = decimal_gps(lon, lon_ref)

        if latitude is None or longitude is None:
            return None

        if not (-90 <= latitude <= 90):
            return None

        if not (-180 <= longitude <= 180):
            return None

        return latitude, longitude

    except Exception:
        return None


# ==================================================
# CREATE MAP
# ==================================================

m = folium.Map(
    location=[36.65, 44.54],
    zoom_start=13,
    tiles=None,
    control_scale=True
)


folium.TileLayer(
    tiles="https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png",
    attr="© OpenStreetMap contributors © CARTO",
    name="Light Map",
    max_zoom=20
).add_to(m)


folium.TileLayer(
    tiles=(
        "https://server.arcgisonline.com/ArcGIS/rest/services/"
        "World_Imagery/MapServer/tile/{z}/{y}/{x}"
    ),
    attr="Tiles © Esri",
    name="Satellite",
    max_zoom=19
).add_to(m)


# ==================================================
# MARKER CLUSTER
# ==================================================

cluster = MarkerCluster(
    name="Soran Survey Photos",
    options={
        "maxClusterRadius": 45,
        "disableClusteringAtZoom": 17,
        "spiderfyOnMaxZoom": True,
        "showCoverageOnHover": False,
        "chunkedLoading": True
    }
).add_to(m)


# ==================================================
# FIND ORIGINAL PHOTOS
# ==================================================

extensions = {".jpg", ".jpeg"}

original_files = sorted(
    p for p in ORIGINAL.rglob("*")
    if p.is_file() and p.suffix.lower() in extensions
)

print("Original JPG/JPEG files:", len(original_files))


# ==================================================
# PROCESS PHOTOS
# ==================================================

gps_count = 0
no_gps_count = 0
no_compressed_count = 0

locations = []

for index, original_path in enumerate(original_files, start=1):

    relative_path = original_path.relative_to(ORIGINAL)

    # Compression script saves every copy as .jpg
    compressed_path = (
        COMPRESSED / relative_path
    ).with_suffix(".jpg")

    if not compressed_path.exists():
        no_compressed_count += 1
        continue

    gps = get_gps(original_path)

    if gps is None:
        no_gps_count += 1
        continue

    latitude, longitude = gps

    gps_count += 1
    locations.append([latitude, longitude])

    # Relative path from index.html
    image_relative = compressed_path.relative_to(BASE).as_posix()
    image_url = quote(image_relative, safe="/")

    filename = html.escape(original_path.name)

    # Popup photo loads when marker popup is opened
    popup_html = f"""
    <div style="width:270px; font-family:Arial;">

        <h4>Pavement Survey Photo</h4>

        <img
            src="{image_url}"
            style="
                width:250px;
                max-height:200px;
                object-fit:contain;
            "
        >

        <p>
            <b>Image:</b> {filename}<br>
            <b>Latitude:</b> {latitude:.6f}<br>
            <b>Longitude:</b> {longitude:.6f}
        </p>

    </div>
    """

    folium.Marker(
        location=[latitude, longitude],
        popup=folium.Popup(popup_html, max_width=290),
        tooltip=filename
    ).add_to(cluster)

    if index % 100 == 0:
        print(f"Processed {index}/{len(original_files)}")


# ==================================================
# AUTOMATIC ZOOM
# ==================================================

if locations:
    m.fit_bounds(locations, padding=(30, 30))


# ==================================================
# MAP CONTROL
# ==================================================

folium.LayerControl(
    collapsed=False
).add_to(m)


# ==================================================
# SAVE WEBSITE
# ==================================================

m.save(str(OUTPUT))


# ==================================================
# FINAL REPORT
# ==================================================

print("\n======================================")
print("SORAN PHOTO MAP READY")
print("======================================")

print("Original JPG/JPEG files:", len(original_files))
print("Photos with GPS:", gps_count)
print("Photos without GPS:", no_gps_count)
print("Missing compressed copies:", no_compressed_count)

print("\nWebsite file:")
print(OUTPUT)

print("======================================")

input("Press Enter to close...")
