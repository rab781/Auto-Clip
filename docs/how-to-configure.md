# How-to: Configure the Bot

This guide walks you through configuring Auto-Clip Bot V2 settings, such as styling your subtitles and limiting download limits, so you customize the generated clips to your brand.

## Step 1: Open the Configuration File

You configure the bot by editing the `content-bot/config.py` file. Open this file in your text editor.

## Step 2: Configure Caption Settings

To change the styling of your subtitles, modify the `CAPTION_SETTINGS` dictionary.

You can select between `animated` or `simple` styles, change the `font`, or update the `highlight_color`.
For brevity, the example below only shows a few commonly customized keys; refer to `content-bot/config.py` for the full set of supported caption options (font size, colors, outline/shadow, positioning, etc.).

```python
# content-bot/config.py
# NOTE: Partial example — only commonly changed keys are shown here.
# Other CAPTION_SETTINGS options (font_size, colors, outline/shadow,
# positioning, etc.) remain at their defaults defined in config.py.
CAPTION_SETTINGS = {
    "font": "Arial",  # Ensure the font is installed on your system
    "style": "animated",
    "highlight_color": "&H00FFFF"  # Yellow highlight
}
```

## Step 3: Set Output Video Dimensions

To adjust the size of the generated vertical clips, you modify the `VIDEO_SETTINGS` dictionary.

```python
# content-bot/config.py
VIDEO_SETTINGS = {
    "output_width": 1080,
    "output_height": 1920,
    "min_clip_duration": 15,
    "max_clip_duration": 300,
}
```

## Step 4: Verify Your Configuration

You verify your configuration by performing a dry run before processing long videos. Run the following command:

```bash
python content-bot/main.py --url https://youtu.be/dQw4w9WgXcQ --dry-run
```

If the command succeeds, you configured the application correctly.