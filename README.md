MUSIC DISPLAY HEADPHONES
========================
Clip-on headphones with a small round screen on each ear that loops a
short video clip of your choice. Each ear is an independent unit
(board + battery); the headphone audio wiring is never touched.

Two pieces of software, two different places:

  convert_video.py   runs on your COMPUTER (Python + ffmpeg).
                         Turns any mp4 into a short 240x240 clip and
                         writes it out as a C header the sketch includes.

  HeadphoneScreen_v3/    runs on the BOARD (Arduino). Loops the clip,
                         tap the screen to switch between the two clips.


FOLDER LAYOUT
-------------
  README.txt                         this guide
  convert_video.py               mp4 -> video_left.h / video_right.h
  videos/                            put your source mp4s here
  firmware/HeadphoneScreen/
      HeadphoneScreen.ino            the Arduino sketch (open this)
      partitions.csv                 flash layout (leave as is)
      video_left.h, video_right.h    generated clips - do not edit
  HeadphoneScreen_Adela/, _Hootie/, _v2/   old LittleFS versions, ignore


PARTS
-----
- 2x Waveshare ESP32-S3-Touch-LCD-1.28 (or ESP32-S3-LCD-1.28, non-touch)
  240x240 round IPS, GC9A01, 16MB flash, 2MB PSRAM, USB-C, MX1.25
  battery socket with onboard charger.
- 1x pair of clip-on headphones with a flat earcup back, ~38 mm across
  (built on Panasonic RP-HZ47; anything similar works)
- 2x 3.7V LiPo ~300mAh, protected, MX1.25 2-pin plug
- 3M VHB foam tape, electrical tape
- USB-C DATA cable
- Computer: Arduino IDE 2, Python 3, ffmpeg


SOFTWARE SETUP (once)
---------------------
1. Arduino IDE 2: https://www.arduino.cc/en/software
2. File > Preferences > Additional boards manager URLs:
     https://espressif.github.io/arduino-esp32/package_esp32_index.json
   Boards Manager > install "esp32" by Espressif (3.x).
3. Library Manager > install
     "GFX Library for Arduino"  (Moon On Our Nation)
     "JPEGDEC"                  (Larry Bank)
4. ffmpeg:  macOS  brew install ffmpeg
            Windows winget install ffmpeg
            Linux   sudo apt install ffmpeg


STEP 1 - MAKE YOUR CLIPS
------------------------
Copy your videos into videos/, then from the HeadphoneScreens folder:

  python3 convert_video.py videos/song.mp4  left  --seconds 10
  python3 convert_video.py videos/other.mp4 right --seconds 10

Options
  --start N     begin N seconds into the video (e.g. the chorus)
  --seconds N   clip length (10-15 s per ear is a good target)
  --fps 20      frame rate (default 20)
  --quality 6   2 = best / largest ... 10 = smallest (default 6)

What it does: centre-crops to a square, scales to 240x240, encodes
baseline MJPEG, and writes firmware/HeadphoneScreen/
video_left.h or video_right.h. It prints the length and size.

Limits: a frame over 60 KB is rejected -> rerun with --quality 8 or 10.
Both clips together must fit in ~14 MB (about 0.5 MB per second total).
The same clip can go on both ears; just run it twice with left and right.


STEP 2 - ARDUINO IDE SETTINGS (Tools menu)
------------------------------------------
  Board:             ESP32S3 Dev Module
  Flash Size:        16MB (128Mb)
  Partition Scheme:  Custom            <- uses partitions.csv in the folder
  PSRAM:             QSPI PSRAM
  USB CDC On Boot:   Enabled
  Upload Speed:      921600
  Port:              the one that appears when you plug the board in
                     (macOS /dev/cu.usbmodem*, Windows COMx)


STEP 3 - PER-BOARD SETTINGS (top of HeadphoneScreen.ino)
--------------------------------------------------------
  TOUCH_VERSION  1 = touch board, 0 = non-touch board
  START_VIDEO    0 = start on the left clip, 1 = start on the right clip
  ROTATION       0-3 in 90-degree steps so the video is upright once
                 mounted with USB-C facing down (usually 0 on one ear and
                 2 on the other, because the boards are mirrored)
  BRIGHTNESS     255 default; ~150 if it blows out on camera / for battery
  SPI_SPEED      80000000; drop to 40000000 if you see stripes

Touch vs non-touch - what actually differs:
  Signal        Touch-LCD-1.28   LCD-1.28 (non-touch)
  SCK/MOSI/CS/DC   10/11/9/8        same
  LCD_MISO         12               none
  LCD_RST          14               12
  Backlight        2                40
  Touch I2C        SDA 6, SCL 7, INT 5, RST 13   (no touch chip)
The touch board has a second thin ribbon from the glass to the PCB.
Wrong TOUCH_VERSION = black screen.


STEP 4 - UPLOAD
---------------
Open firmware/HeadphoneScreen/HeadphoneScreen.ino, plug in the
board, click Upload. Compile takes 1-2 min (the clips are big), upload
about 1 min. Press RST - the clip loops. Tap the screen (or press BOOT)
to switch between the two clips.
If upload won't start: hold BOOT, tap RST, release BOOT, Upload again.
Repeat for the second board with its own START_VIDEO / ROTATION.


STEP 5 - BATTERY
----------------
  !! Check polarity before plugging in. The MX1.25 socket is NOT
  !! standardised. Find the + / - marks beside the socket on the board
  !! and make sure the RED wire lands on +. If reversed, lift the tiny
  !! metal tab inside the plug with a pin, pull the wires out, swap them.

With USB unplugged, connect the battery: the screen should come on.
Plug USB-C back in: the onboard charger charges the LiPo.
Runtime at full brightness is roughly 1.5-2 h per 300 mAh cell; lower
BRIGHTNESS to stretch it. There is no power switch: unplug the battery
or let it drain.


STEP 6 - ASSEMBLY
-----------------
Dry-fit everything with masking tape first (set ROTATION, check lead
lengths). VHB cannot be repositioned once pressed down.

Side view of one ear, seen from outside:

                     clip hanger (stock, rotating)
                            +----------+
                            |          |   <- hooks over the ear
                    +-------+----------+-------+
                 +--|      .------------.      |--+
                /   |   .--| LiPo 300   |--.   |   \
               |    |  /   | mAh        |   \  |    |
               |    | |    '-----+------'    | |    |  <- round screen
               |    | |   .------+------.    | |    |     (video here)
               |    | |   | Waveshare   |    | |    |
               |    | |   | ESP32-S3    |    | |    |
                \   |  \  | 1.28" board |   /  |   /
                 +--|   '-+------+------+-'    |--+
                    +------------+-------------+
                                 |
                          USB-C port facing DOWN
                                 |
                    headphone audio cable (untouched)

Layer stack, from the ear outward:

  YOUR EAR
   |
   v
  [ foam earpad ]                 1. stock
  [ driver + plastic back shell ] 2. stock
  [===== VHB foam tape =========] 3. full disc, cut to the shell
  [ LiPo, taped in elec. tape   ] 4. flat side down, leads toward USB edge
  [===== VHB (small pieces) ====] 5. leave the MX1.25 socket area clear
  [ back of board, elec. tape   ] 6. cover ESP32 module, header, socket
  [ PCB                         ] 7.
  [ round LCD glass             ] 8. faces outward - do NOT tape over it
   OUTSIDE

Added per ear: ~13 mm thickness, ~17 g (board ~10 g + battery ~7 g).
The ~36 mm board sits on a ~38 mm earpad, so the cup looks like it IS
the screen.

Order of work per ear:
  a. Insulate the back of the board with electrical tape (all exposed
     metal), leaving the MX1.25 socket reachable.
  b. Wrap the battery in electrical tape. Plug it in with a small slack
     loop in the lead - never stretched, never pinched between layers.
  c. Stick battery to board back with small VHB pieces.
  d. Cut a VHB disc for the earcup back shell, stick the battery side of
     the stack onto it, USB-C pointing down toward the cable.
  e. Put them on, check the video is upright; if not, change ROTATION
     and re-upload (USB-C is still reachable).

Wiring - there is almost none:
  LiPo  --(MX1.25, red to +)--> board battery socket
  USB-C -------------------->  board (upload + charging)
  Audio cable --------------->  driver (stock, separate circuit)


KNOWN TRADE-OFF
---------------
Light clip-ons are built for ~11 g per side; this adds ~17 g cantilevered
outward, so expect a slight tilt. Fixes if needed: move the battery to
the inside of the clip hanger (weight closer to the head), or a dab of
hot glue at the hanger pivot to stiffen it.


TROUBLESHOOTING
---------------
- Black screen: TOUCH_VERSION wrong, then check backlight pin.
- Video sideways/upside down: change ROTATION, re-upload.
- Stripes / glitches: SPI_SPEED 40000000.
- Tap does nothing: press BOOT instead; on non-touch boards only BOOT works.
- Upload won't start: hold BOOT, tap RST, release BOOT, retry.
- "largest frame is N bytes" from the script: --quality 8 (or 10).
- Firmware too big: shorten clips with --seconds or raise --quality.
- "ffmpeg: command not found": install ffmpeg (Software Setup, step 4).
- Board won't power from battery: polarity (Step 5) or empty cell -
  charge over USB first.
