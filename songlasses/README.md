# songlasses

Webcam-based glasses reminder. Snaps a photo, asks an AI if you're wearing glasses, and escalates until you put them on.

![no-glasses alert](no-glasses.png)

## How it works

Every 5 minutes, `glasses-watch` takes a webcam snapshot and sends it to Groq's vision API. Three consecutive "no glasses" results trigger escalating alerts:

| Strike | What happens |
|---|---|
| 1st (5 min) | Gentle notification |
| 2nd (10 min) | Critical persistent notification |
| 3rd+ (15 min) | Fullscreen meme overlay (press `Q` to dismiss) |

`NO FACE DETECTED` (away from desk) pauses the streak without resetting it.

## Prerequisites

- `ffmpeg` — webcam capture
- `mpv` — fullscreen image display
- `notify-send` — desktop notifications
- A [Groq API key](https://console.groq.com) (free tier works)

## Setup

**1. Store your Groq API key:**
```fish
echo 'gsk_YOUR_KEY' > ~/.groq_key
chmod 600 ~/.groq_key
```

**2. Symlink the scripts into PATH:**
```fish
set DIR /path/to/songlasses
for f in glasses-check glasses-watch glasses-alert songlasses
    ln -s $DIR/$f ~/.local/bin/$f
end
```

**3. Autostart on login** — add to your Hyprland config:
```ini
exec-once = sleep 15 && glasses-watch
```

## Cheat code

Run `songlasses` in any terminal to reset your strike counter and get a 5-minute pass.

![songlasses cheat](songlasses.png)
