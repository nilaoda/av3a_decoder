# av3a_decoder
AVS3-P3 / Audio Vivid Decoder

**!!ONLY 5.1.4 LAYOUT TESTED!!**

**!!VERY SLOW, BUT WORKS!!**

# Steps

## 1. Extract av3a audio from MPEG2-TS file (**Optional**)

You can use `es_extractor.py` to do that:
```
python es_extractor.py sample.ts sample.av3a 0x101
```
Note: You can use mediainfo to find av3a track pid, maybe `0x101` or `0x1100`

## 2. Decode av3a to PCM
```
python av3a_decoder.py sample.av3a sample.wav
```

## 3. Post Process
### You can set channel layout
5.1.4 Example:
```
ffmpeg -i sample.wav -filter "channelmap=0|1|2|3|4|5|6|7|8|9:FL+FR+FC+LFE+SL+SR+TFL+TFR+TBL+TBR" sample_layout.wav
```
### You can encode wav to 448 kbps 5.1(side) AC3
```
ffmpeg -i sample.wav -filter "channelmap=0|1|2|3|4|5:FL+FR+FC+LFE+SL+SR" -b:a 448k sample_layout.ac3
```

# Links
* https://github.com/wuxianlin/ijkplayer-av3a
* https://github.com/maiyao1988/ExAndroidNativeEmu
* https://www.nrta.gov.cn/art/2023/3/9/art_3715_63623.html
* https://www.nrta.gov.cn/art/2020/4/24/art_3715_50841.html