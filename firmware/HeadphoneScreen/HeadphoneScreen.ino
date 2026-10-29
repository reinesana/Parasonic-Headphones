// HeadphoneScreen: loops a video on a Waveshare ESP32-S3 1.28" round display.
// Both videos are built into the sketch - just click Upload, nothing else.
// Tap the screen (or press BOOT) to switch videos.
//
// Libraries (Arduino IDE > Library Manager):
//   "GFX Library for Arduino" by Moon On Our Nation (Arduino_GFX)
//   "JPEGDEC" by Larry Bank
//
// Board settings (Tools menu):
//   Board: ESP32S3 Dev Module
//   Flash Size: 16MB (128Mb)
//   Partition Scheme: Custom   (uses partitions.csv in this folder)
//   PSRAM: QSPI PSRAM
//   USB CDC On Boot: Enabled
//   Upload Speed: 921600       (faster - the upload is about 5 MB)

#include <Arduino_GFX_Library.h>
#include <JPEGDEC.h>
#include <Wire.h>
#include "video_left.h"    // generated: python3 convert_video.py videos/clip.mp4 left
#include "video_right.h"   // generated: python3 convert_video.py videos/clip.mp4 right

// ---- 1 = Touch version (ESP32-S3-Touch-LCD-1.28), 0 = non-touch (ESP32-S3-LCD-1.28) ----
#define TOUCH_VERSION 1

// ---- Which video this board starts on: 0 = left clip, 1 = right clip ----
#define START_VIDEO 0

// ---- Screen rotation 0-3 (90 deg steps) so the video is upright once mounted ----
#define ROTATION 0

#if TOUCH_VERSION
  #define LCD_SCK  10
  #define LCD_MOSI 11
  #define LCD_MISO 12
  #define LCD_CS    9
  #define LCD_DC    8
  #define LCD_RST  14
  #define LCD_BL    2
  #define TP_SDA    6
  #define TP_SCL    7
  #define TP_INT    5
  #define TP_RST   13
  #define TP_ADDR  0x15          // CST816S touch chip
#else
  #define LCD_SCK  10
  #define LCD_MOSI 11
  #define LCD_MISO -1
  #define LCD_CS    9
  #define LCD_DC    8
  #define LCD_RST  12
  #define LCD_BL   40
#endif

#define BOOT_BTN    0            // BOOT button also switches videos
#define FPS         20           // the videos were made at 20 fps
#define SPI_SPEED   80000000     // lower to 40000000 if you see glitches
#define BRIGHTNESS  255          // 0-255; lower it if the screen blows out on camera

struct Video { const uint8_t *data; const uint32_t *offsets; uint32_t frames; };
const Video VIDEOS[] = {
  { left_data,  left_offsets,  left_frames  },
  { right_data, right_offsets, right_frames },
};
const int NUM_VIDEOS = 2;
int currentVideo = START_VIDEO;
uint32_t currentFrame = 0;

Arduino_DataBus *bus = new Arduino_ESP32SPI(LCD_DC, LCD_CS, LCD_SCK, LCD_MOSI, LCD_MISO);
Arduino_GFX *gfx = new Arduino_GC9A01(bus, LCD_RST, ROTATION, true /* IPS */);
JPEGDEC jpeg;

int drawMCU(JPEGDRAW *p) {
  gfx->draw16bitBeRGBBitmap(p->x, p->y, p->pPixels, p->iWidth, p->iHeight);
  return 1;
}

// ---------------- tap / button detection ----------------
volatile unsigned long lastTouchIrq = 0;
void IRAM_ATTR onTouch() { lastTouchIrq = millis(); }

bool tapped() {
  static bool armed = true;
  static unsigned long seenIrq = 0;
  static bool lastBtn = HIGH;
  bool hit = false;

  // touch chip pulses its INT pin while a finger is down;
  // switch once per touch, re-arm after 300 ms with no touch
  unsigned long irq = lastTouchIrq;
  if (irq != seenIrq) {
    seenIrq = irq;
    if (armed) { hit = true; armed = false; }
  } else if (!armed && millis() - irq > 300) {
    armed = true;
  }

  bool btn = digitalRead(BOOT_BTN);
  if (lastBtn == HIGH && btn == LOW) hit = true;
  lastBtn = btn;

  return hit;
}

void setupTouch() {
#if TOUCH_VERSION
  pinMode(TP_RST, OUTPUT);
  digitalWrite(TP_RST, LOW);  delay(10);
  digitalWrite(TP_RST, HIGH); delay(50);
  Wire.begin(TP_SDA, TP_SCL);
  Wire.beginTransmission(TP_ADDR);   // turn off the chip's auto-sleep
  Wire.write(0xFE); Wire.write(0x01);
  Wire.endTransmission();
  pinMode(TP_INT, INPUT_PULLUP);
  attachInterrupt(digitalPinToInterrupt(TP_INT), onTouch, FALLING);
#endif
  pinMode(BOOT_BTN, INPUT_PULLUP);
}

// ---------------- main ----------------
void setup() {
  Serial.begin(115200);

  pinMode(LCD_BL, OUTPUT);
  analogWrite(LCD_BL, BRIGHTNESS);

  if (!gfx->begin(SPI_SPEED)) Serial.println("Display init failed");
  gfx->fillScreen(RGB565_BLACK);

  setupTouch();
}

void loop() {
  static unsigned long nextFrameAt = millis();

  if (tapped()) {
    currentVideo = (currentVideo + 1) % NUM_VIDEOS;
    currentFrame = 0;
    nextFrameAt = millis();
  }

  const Video &v = VIDEOS[currentVideo];
  if (currentFrame >= v.frames) currentFrame = 0;   // loop
  uint32_t start = v.offsets[currentFrame];
  uint32_t len = v.offsets[currentFrame + 1] - start;
  currentFrame++;

  if (jpeg.openFLASH(v.data + start, len, drawMCU)) {
    jpeg.setPixelType(RGB565_BIG_ENDIAN);
    jpeg.decode(0, 0, 0);
    jpeg.close();
  }

  nextFrameAt += 1000 / FPS;
  long wait = (long)(nextFrameAt - millis());
  if (wait > 0) delay(wait);
  else nextFrameAt = millis();
}
