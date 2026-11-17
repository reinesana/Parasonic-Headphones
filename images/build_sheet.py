#!/usr/bin/env python3
"""Draws the printable one-page build sheet (build_sheet.pdf / .png).
Run with a Python that has matplotlib:  /opt/anaconda3/bin/python3 images/build_sheet.py
"""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, FancyBboxPatch, Polygon, Rectangle, Wedge, Arc

INK = "#222222"
GREY = "#8a8a8a"
LIGHT = "#e9e9e9"
SCREEN = "#c9b6ff"
BATT = "#f3d9a4"
TAPE = "#9ad1f5"
VHB = "#f5a3a3"
GLASS = "#5c4b8a"

fig = plt.figure(figsize=(8.5, 11))
fig.patch.set_facecolor("white")
fig.text(0.5, 0.965, "MUSIC DISPLAY HEADPHONES  -  build sheet", ha="center", va="center",
         fontsize=17, fontweight="bold", color=INK)
fig.text(0.5, 0.943, "one screen + one battery per ear  -  no soldering  -  audio wiring untouched",
         ha="center", va="center", fontsize=9.5, color=GREY)


def panel(idx, title, caption):
    col, row = idx % 2, idx // 2
    ax = fig.add_axes([0.06 + col * 0.47, 0.675 - row * 0.3, 0.41, 0.245])
    ax.set_xlim(0, 100); ax.set_ylim(0, 100); ax.set_aspect("equal"); ax.axis("off")
    ax.add_patch(FancyBboxPatch((0, 0), 100, 100, boxstyle="round,pad=0,rounding_size=4",
                                fc="white", ec=INK, lw=1.4))
    ax.add_patch(Circle((9, 91), 6.5, fc=INK, ec=INK))
    ax.text(9, 91, str(idx + 1), ha="center", va="center", color="white", fontsize=11, fontweight="bold")
    ax.text(19, 91, title, ha="left", va="center", fontsize=11, fontweight="bold", color=INK)
    ax.text(50, 7, caption, ha="center", va="center", fontsize=6.2, color=INK, linespacing=1.4)
    return ax


def board(ax, cx, cy, r=18, back=False):
    """Round Waveshare board. back=True shows components; else shows screen."""
    ax.add_patch(Circle((cx, cy), r, fc=LIGHT, ec=INK, lw=1.3))
    ax.add_patch(Rectangle((cx - 4, cy - r - 4), 8, 5, fc="white", ec=INK, lw=1))  # USB-C
    ax.text(cx, cy - r - 8, "USB-C", ha="center", va="center", fontsize=6, color=GREY)
    if back:
        ax.add_patch(Rectangle((cx - 9, cy - 2), 18, 12, fc="#bbbbbb", ec=INK, lw=0.8))
        ax.text(cx, cy + 4, "ESP32-S3", ha="center", va="center", fontsize=5.5)
        ax.add_patch(Rectangle((cx - 12, cy - 11), 7, 4, fc="white", ec=INK, lw=0.8))
        ax.text(cx - 8.5, cy - 14.5, "BAT", ha="center", va="center", fontsize=5)
        ax.text(cx - 14.5, cy - 9, "+", ha="center", va="center", fontsize=7, fontweight="bold")
        ax.add_patch(Rectangle((cx + 3, cy - 11), 9, 3, fc="white", ec=INK, lw=0.8))
    else:
        ax.add_patch(Circle((cx, cy), r - 3, fc=SCREEN, ec=GLASS, lw=1))
        ax.add_patch(Wedge((cx, cy), r - 3, 200, 330, fc="#8b6fe0", ec="none"))
        ax.text(cx, cy, "video", ha="center", va="center", fontsize=7, color="white", fontweight="bold")


def battery(ax, x, y, w=24, h=14, lead_to=None):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0,rounding_size=2",
                                fc=BATT, ec=INK, lw=1.2))
    ax.text(x + w / 2, y + h / 2, "LiPo\n300mAh", ha="center", va="center", fontsize=6)
    if lead_to:
        ax.plot([x + w, lead_to[0]], [y + h * 0.6, lead_to[1]], color="#d33", lw=1.3)
        ax.plot([x + w, lead_to[0]], [y + h * 0.35, lead_to[1] - 2.5], color=INK, lw=1.3)


def earcup(ax, cx, cy, r=20):
    ax.add_patch(Circle((cx, cy), r, fc="#f7f7f7", ec=INK, lw=1.3))
    ax.add_patch(Circle((cx, cy), r - 5, fc="#dddddd", ec=GREY, lw=0.8))
    ax.add_patch(Arc((cx + r * 0.55, cy + r * 0.9), r * 1.5, r * 1.4, theta1=10, theta2=200,
                     color=INK, lw=2.2))
    ax.plot([cx + 2, cx + 2], [cy - r, cy - r - 14], color=INK, lw=1.2)
    ax.text(cx + 5, cy - r - 10, "audio\ncable", ha="left", va="center", fontsize=6, color=GREY)


# 1 - parts
ax = panel(0, "Parts (per ear)", "Waveshare ESP32-S3 1.28\" round display board,\n"
           "protected 3.7 V LiPo with MX1.25 plug, one earcup.")
board(ax, 24, 52)
battery(ax, 44, 46)
earcup(ax, 82, 55, 15)
ax.text(24, 76, "board", ha="center", fontsize=7)
ax.text(56, 66, "battery", ha="center", fontsize=7)
ax.text(82, 82, "earcup", ha="center", fontsize=7)

# 2 - upload
ax = panel(1, "Upload the clip", "convert_video.py for left / right, set TOUCH_VERSION,\n"
           "START_VIDEO, ROTATION in the sketch, Upload, press RST.")
ax.add_patch(FancyBboxPatch((8, 40), 36, 26, boxstyle="round,pad=0,rounding_size=2", fc="white", ec=INK, lw=1.2))
ax.add_patch(Rectangle((11, 44), 30, 19, fc=LIGHT, ec="none"))
ax.text(26, 56, "convert_video.py", ha="center", fontsize=5.5, family="monospace")
ax.text(26, 50, "left / right", ha="center", fontsize=5.5, family="monospace")
ax.add_patch(Rectangle((4, 36), 44, 4, fc="#cccccc", ec=INK, lw=0.8))
ax.text(26, 30, "laptop", ha="center", fontsize=7, color=GREY)
ax.plot([48, 60], [52, 52], color=INK, lw=1.4)
ax.plot([50, 50, 60], [55, 52, 52], color=INK, lw=1.4)
ax.annotate("", xy=(62, 52), xytext=(55, 52), arrowprops=dict(arrowstyle="->", lw=1.4, color=INK))
ax.text(55, 59, "USB-C\ndata cable", ha="center", fontsize=6, color=GREY)
board(ax, 80, 54, 15)

# 3 - insulate
ax = panel(2, "Insulate the back", "Electrical tape over the ESP32 module, header pins\n"
           "and exposed metal. Leave the battery socket reachable.")
board(ax, 30, 52, 18, back=True)
ax.text(30, 76, "back of board", ha="center", fontsize=7)
board(ax, 72, 52, 18, back=True)
ax.add_patch(Rectangle((57, 45), 30, 22, fc=TAPE, ec=INK, lw=1))
ax.add_patch(Rectangle((57, 45), 30, 22, fc="none", ec="none"))
ax.text(72, 56, "electrical\ntape", ha="center", va="center", fontsize=6,
        bbox=dict(boxstyle="round,pad=0.25", fc=TAPE, ec="none"))
ax.text(72, 76, "taped, socket free", ha="center", fontsize=7)
ax.annotate("", xy=(52, 52), xytext=(49, 52), arrowprops=dict(arrowstyle="->", lw=1.6, color=INK))

# 4 - battery
ax = panel(3, "Plug in the battery", "RED wire to the + mark by the socket (not standardised!).\n"
           "Wrap the cell in tape, leave slack in the lead, VHB it on.")
board(ax, 68, 50, 18, back=True)
battery(ax, 12, 40, 28, 15, lead_to=(56, 42))
ax.text(26, 60, "wrapped in\nelectrical tape", ha="center", fontsize=6, color=GREY)
ax.text(44, 50, "red = +", ha="center", fontsize=6.5, color="#d33", fontweight="bold")
ax.add_patch(Circle((53.5, 41), 5, fc="none", ec="#d33", lw=1.4, ls="--"))

# 5 - stack
ax = panel(4, "Layer stack", "Cross-section, ear outward. Adds ~13 mm and ~17 g per ear.\n"
           "Dry-fit with masking tape first - VHB can't be moved.")
layers = [
    ("foam earpad", "#d9d9d9", 7), ("driver + back shell", "#bfbfbf", 8), ("VHB tape", VHB, 4),
    ("LiPo (taped)", BATT, 7), ("VHB (small pieces)", VHB, 3), ("board back (taped)", TAPE, 4),
    ("PCB", "#9bc49b", 4), ("round LCD glass", SCREEN, 5),
]
y = 20
for name, color, h in layers:
    ax.add_patch(Rectangle((16, y), 40, h, fc=color, ec=INK, lw=0.9))
    ax.text(59, y + h / 2, name, ha="left", va="center", fontsize=6.3)
    y += h
ax.annotate("", xy=(10, 60), xytext=(10, 20), arrowprops=dict(arrowstyle="->", lw=1.2, color=GREY))
ax.text(10, 16, "ear", ha="center", fontsize=6.5, color=GREY)
ax.text(10, 64, "outside", ha="center", fontsize=6.5, color=GREY)

# 6 - mounted
ax = panel(5, "Mount & rotate", "VHB disc on the earcup back, USB-C pointing down.\n"
           "Video upside down? Change ROTATION and re-upload.")
earcup(ax, 46, 50, 22)
board(ax, 46, 50, 17)
ax.add_patch(Arc((46, 50), 50, 50, theta1=300, theta2=20, color=GREY, lw=1.2, ls="--"))
ax.annotate("", xy=(70, 58), xytext=(71, 50), arrowprops=dict(arrowstyle="->", lw=1.2, color=GREY))
ax.text(84, 46, "ROTATION\n0-3", ha="center", va="center", fontsize=6.5, color=GREY)
ax.text(18, 30, "clip hanger\nover the ear", ha="center", fontsize=6, color=GREY)

fig.text(0.5, 0.058, "Per-board settings at the top of HeadphoneScreen.ino", ha="center",
         fontsize=8, color=INK, fontweight="bold")
fig.text(0.5, 0.040, "TOUCH_VERSION 1/0    START_VIDEO 0 = left clip, 1 = right clip    "
         "ROTATION 0-3    BRIGHTNESS 0-255",
         ha="center", fontsize=7.5, color=INK, family="monospace")
fig.text(0.5, 0.020, "github.com/reinesana/Parasonic-Headphones", ha="center", fontsize=7.5, color=GREY)

out = Path(__file__).resolve().parent
fig.savefig(out / "build_sheet.pdf")
fig.savefig(out / "build_sheet.png", dpi=200)
print("wrote", out / "build_sheet.pdf", "and build_sheet.png")
