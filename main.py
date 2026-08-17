# ==========================================================
# PAPERSTORE OMR FIXED
# ==========================================================
#
# FEATURES
# --------
# ✔ Text file storage
# ✔ Stable OMR grid
# ✔ Fixed traversal
# ✔ No sync searching
# ✔ Reserved timing cells
# ✔ Alignment guide dots
# ✔ Shared master grid
# ✔ CRC verification
# ✔ Adjustable paper size
# ✔ Adjustable cell size
# ✔ Interactive CMD
# ✔ PNG-safe output
#
# IMPORTANT
# ---------
# USE:
# - PNG ONLY
# - CELL SIZE 16-20
#
# INSTALL
# -------
# pip install pillow numpy opencv-python
#
# ==========================================================

import os
import cv2
import json
import zlib
import numpy as np

from PIL import Image
from PIL import ImageDraw

# ==========================================================
# CONFIG
# ==========================================================

PAPER_SIZES = {
    "A4": (2480, 3508),    
    "A5": (1748, 2480),
    "LETTER": (2550, 3300)
}

DEFAULT_MARGIN = 160

ALIGN_EVERY = 20

# ==========================================================
# UTIL
# ==========================================================

def clear():
    os.system("cls" if os.name == "nt" else "clear")

def bytes_to_bits(data):

    return ''.join(
        f'{b:08b}'
        for b in data
    )

def bits_to_bytes(bits):

    out = bytearray()

    for i in range(0, len(bits), 8):

        chunk = bits[i:i+8]

        if len(chunk) == 8:

            out.append(
                int(chunk, 2)
            )

    return bytes(out)

# ==========================================================
# HEADER                                          
# ==========================================================

def build_packet(text):

    raw = text.encode("utf-8")

    crc = zlib.crc32(raw)

    meta = {
        "size": len(raw),
        "crc": crc
    }

    header = json.dumps(meta).encode()

    packet = (
        len(header).to_bytes(4, "big") +
        header +
        raw
    )

    return packet

def parse_packet(data):

    header_size = int.from_bytes(
        data[:4],
        "big"
    )

    header_raw = data[
        4:4+header_size
    ]

    meta = json.loads(
        header_raw.decode()
    )

    payload = data[
        4+header_size:
    ]

    payload = payload[
        :meta["size"]
    ]

    crc = zlib.crc32(payload)

    if crc != meta["crc"]:
        raise Exception("CRC FAILED")

    return payload.decode("utf-8")

# ==========================================================
# MASTER GRID
# ==========================================================

def build_centers(
    margin,
    grid_w,
    grid_h,
    cell
):

    xs = []
    ys = []

    for x in range(grid_w):

        xs.append(
            margin +
            x * cell +
            cell // 2
        )

    for y in range(grid_h):

        ys.append(
            margin +
            y * cell +
            cell // 2
        )

    return xs, ys

# ==========================================================
# RESERVED CELLS
# ==========================================================

def is_reserved(x, y):

    # timing row
    if y == 0:
        return True

    # timing column
    if x == 0:
        return True

    # alignment
    if (
        x % ALIGN_EVERY == 0
        and
        y % ALIGN_EVERY == 0
    ):
        return True

    return False

# ==========================================================
# FINDERS
# ==========================================================

def draw_finders(draw, w, h):

    s = 60

    draw.rectangle(
        [20,20,20+s,20+s],
        fill="black"
    )

    draw.rectangle(
        [w-20-s,20,w-20,20+s],
        fill="black"
    )

    draw.rectangle(
        [20,h-20-s,20+s,h-20],
        fill="black"
    )

    draw.ellipse(
        [w-100,h-100,w-20,h-20],
        fill="black"
    )

# ==========================================================
# GRID
# ==========================================================

def draw_grid(
    draw,
    margin,
    grid_w,
    grid_h,
    cell
):

    for x in range(grid_w + 1):

        px = margin + x * cell

        draw.line(
            [
                (px, margin),
                (px, margin + grid_h * cell)
            ],
            fill=(220,220,220),
            width=1
        )

    for y in range(grid_h + 1):

        py = margin + y * cell

        draw.line(
            [
                (margin, py),
                (margin + grid_w * cell, py)
            ],
            fill=(220,220,220),
            width=1
        )

# ==========================================================
# TIMING
# ==========================================================

def draw_timing(
    draw,
    xs,
    ys,
    margin,
    cell
):

    # top timing

    for i, cx in enumerate(xs):

        if i % 2 == 0:

            draw.rectangle(
                [
                    cx - cell//2,
                    margin - 50,
                    cx + cell//2,
                    margin - 30
                ],
                fill="black"
            )

    # left timing

    for i, cy in enumerate(ys):

        if i % 2 == 0:

            draw.rectangle(
                [
                    margin - 50,
                    cy - cell//2,
                    margin - 30,
                    cy + cell//2
                ],
                fill="black"
            )

# ==========================================================
# ALIGNMENT
# ==========================================================

def draw_alignment(
    draw,
    xs,
    ys,
    cell
):

    r = max(2, cell // 4)

    for y in range(
        0,
        len(ys),
        ALIGN_EVERY
    ):

        for x in range(
            0,
            len(xs),
            ALIGN_EVERY
        ):

            cx = xs[x]
            cy = ys[y]

            draw.ellipse(
                [
                    cx-r,
                    cy-r,
                    cx+r,
                    cy+r
                ],
                fill="black"
            )

# ==========================================================
# ENCODE
# ==========================================================

def encode():

    clear()

    print("=" * 60)
    print(" PAPERSTORE OMR ")
    print("=" * 60)

    path = input(
        "\nEnter text file path: "
    ).strip()

    if not os.path.exists(path):

        print("\n[-] File not found")
        input("\nPress Enter...")
        return

    with open(
        path,
        "r",
        encoding="utf-8"
    ) as f:

        text = f.read()

    print("""
1. A4
2. A5
3. LETTER
""")

    p = input(
        "Paper size: "
    ).strip()

    if p == "1":
        paper = "A4"

    elif p == "2":
        paper = "A5"

    else:
        paper = "LETTER"

    page_w, page_h = PAPER_SIZES[paper]

    cell = int(input(
        "\nCell size (16 recommended): "
    ))

    margin = DEFAULT_MARGIN

    grid_w = (
        page_w - margin * 2
    ) // cell

    grid_h = (
        page_h - margin * 2
    ) // cell

    xs, ys = build_centers(
        margin,
        grid_w,
        grid_h,
        cell
    )

    packet = build_packet(text)

    bits = bytes_to_bits(packet)

    img = Image.new(
        "RGB",
        (page_w, page_h),
        "white"
    )

    draw = ImageDraw.Draw(img)

    draw_finders(draw, page_w, page_h)

    draw_grid(
        draw,
        margin,
        grid_w,
        grid_h,
        cell
    )

    draw_timing(
        draw,
        xs,
        ys,
        margin,
        cell
    )

    draw_alignment(
        draw,
        xs,
        ys,
        cell
    )

    # ======================================================
    # DATA
    # ======================================================

    bit_index = 0

    for y in range(grid_h):

        for x in range(grid_w):

            if is_reserved(x, y):
                continue

            if bit_index >= len(bits):
                break

            bit = bits[bit_index]

            bit_index += 1

            if bit == "1":

                cx = xs[x]
                cy = ys[y]

                half = cell // 2 - 2

                draw.rectangle(
                    [
                        cx-half,
                        cy-half,
                        cx+half,
                        cy+half
                    ],
                    fill="black"
                )

    os.makedirs(
        "output",
        exist_ok=True
    )

    out = "output/paperstore.png"

    img.save(out)

    print("\n[+] ENCODE COMPLETE")
    print("[+] Saved:", out)

    input("\nPress Enter...")

# ==========================================================
# READ GRID
# ==========================================================

def read_grid(
    thresh,
    xs,
    ys,
    cell
):

    bits = []

    for y, cy in enumerate(ys):

        for x, cx in enumerate(xs):

            if is_reserved(x, y):
                continue

            s = int(cell * 0.30)

            x1 = cx - s
            y1 = cy - s

            x2 = cx + s
            y2 = cy + s

            sample = thresh[
                y1:y2,
                x1:x2
            ]

            black = np.sum(
                sample > 0
            )

            ratio = black / sample.size

            if ratio > 0.60:
                bits.append("1")
            else:
                bits.append("0")

    return ''.join(bits)

# ==========================================================
# DECODE
# ==========================================================

def decode():

    clear()

    print("=" * 60)
    print(" PAPERSTORE OMR ")
    print("=" * 60)

    path = input(
        "\nEnter image path: "
    ).strip()

    if not os.path.exists(path):

        print("\n[-] File not found")
        input("\nPress Enter...")
        return

    img = cv2.imread(path)

    gray = cv2.cvtColor(
        img,
        cv2.COLOR_BGR2GRAY
    )

    thresh = cv2.adaptiveThreshold(
        gray,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY_INV,
        31,
        5
    )

    cell = int(input(
        "\nEnter cell size used: "
    ))

    margin = DEFAULT_MARGIN

    h, w = thresh.shape

    grid_w = (
        w - margin * 2
    ) // cell

    grid_h = (
        h - margin * 2
    ) // cell

    xs, ys = build_centers(
        margin,
        grid_w,
        grid_h,
        cell
    )

    bits = read_grid(
        thresh,
        xs,
        ys,
        cell
    )

    raw = bits_to_bytes(bits)

    try:

        text = parse_packet(raw)

        os.makedirs(
            "output",
            exist_ok=True
        )

        out = "output/recovered.txt"

        with open(
            out,
            "w",
            encoding="utf-8"
        ) as f:

            f.write(text)

        print("\n[+] DECODE COMPLETE")
        print("[+] File:", out)

    except Exception as e:

        print("\n[-] Decode failed")
        print(e)

    input("\nPress Enter...")

# ==========================================================
# MENU
# ==========================================================

while True:

    clear()

    print("=" * 60)
    print(" PAPERSTORE OMR ")
    print("=" * 60)

    print("""
1. Encode Text File
2. Decode Image
3. Exit
""")

    choice = input(
        "Select Option: "
    ).strip()

    if choice == "1":
        encode()

    elif choice == "2":
        decode()

    elif choice == "3":
        break

    else:

        print("\n[-] Invalid option")

        input("\nPress Enter...")