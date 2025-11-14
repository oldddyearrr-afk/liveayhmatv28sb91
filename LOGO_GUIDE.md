# 🎨 Logo/Watermark Guide

## Quick Start

1. **Prepare your logo**:
   - Format: PNG with transparency (recommended)
   - Also supported: JPG, GIF
   - Recommended size: 200x100 px or smaller

2. **Place logo file** in project directory:
   ```bash
   # Upload your logo.png file to the project root
   ```

3. **Enable logo** in `config.sh`:
   ```bash
   LOGO_ENABLED="true"
   LOGO_PATH="logo.png"
   ```

4. **Start streaming**:
   ```bash
   ./control.sh start
   ```

## Logo Settings

### Position

Choose where to place your logo:

```bash
# In config.sh
LOGO_POSITION="topright"    # Top right corner (default)
# OR
LOGO_POSITION="topleft"     # Top left corner
# OR
LOGO_POSITION="bottomright" # Bottom right corner
# OR
LOGO_POSITION="bottomleft"  # Bottom left corner
```

### Offset from Edges

Adjust distance from screen edges (in pixels):

```bash
LOGO_OFFSET_X="10"  # Horizontal offset (pixels)
LOGO_OFFSET_Y="10"  # Vertical offset (pixels)
```

Example:
- `LOGO_OFFSET_X="20"` and `LOGO_OFFSET_Y="20"` = 20 pixels from edges
- `LOGO_OFFSET_X="50"` and `LOGO_OFFSET_Y="30"` = 50px from side, 30px from top/bottom

### Logo Size

Resize your logo:

```bash
# Keep original size
LOGO_SIZE=""

# Resize to specific dimensions (WxH)
LOGO_SIZE="200:100"   # 200px wide, 100px tall

# Scale proportionally
LOGO_SIZE="150:-1"    # 150px wide, height auto
LOGO_SIZE="-1:80"     # Width auto, 80px tall
```

### Opacity

Make logo more transparent:

```bash
# Fully opaque (default)
LOGO_OPACITY="1.0"

# Semi-transparent
LOGO_OPACITY="0.7"    # 70% opaque

# Very subtle
LOGO_OPACITY="0.3"    # 30% opaque
```

## Complete Example

### Example 1: Simple Top-Right Logo

```bash
# In config.sh
LOGO_ENABLED="true"
LOGO_PATH="logo.png"
LOGO_POSITION="topright"
LOGO_OFFSET_X="20"
LOGO_OFFSET_Y="20"
LOGO_SIZE=""
LOGO_OPACITY="1.0"
```

Result: Full-opacity logo in top-right corner, 20px from edges

### Example 2: Subtle Bottom-Left Watermark

```bash
# In config.sh
LOGO_ENABLED="true"
LOGO_PATH="watermark.png"
LOGO_POSITION="bottomleft"
LOGO_OFFSET_X="30"
LOGO_OFFSET_Y="30"
LOGO_SIZE="120:-1"    # 120px wide, auto height
LOGO_OPACITY="0.5"    # 50% transparent
```

Result: Semi-transparent watermark in bottom-left, resized to 120px wide

### Example 3: Large Top-Left Branding

```bash
# In config.sh
LOGO_ENABLED="true"
LOGO_PATH="brand.png"
LOGO_POSITION="topleft"
LOGO_OFFSET_X="10"
LOGO_OFFSET_Y="10"
LOGO_SIZE="300:150"   # 300x150 pixels
LOGO_OPACITY="0.9"    # Slightly transparent
```

Result: Large brand logo in top-left corner

## Troubleshooting

### Logo doesn't appear

1. Check logo file exists:
   ```bash
   ls -la logo.png
   ```

2. Verify settings in `config.sh`:
   ```bash
   grep LOGO config.sh
   ```

3. Check stream logs:
   ```bash
   ./control.sh logs
   ```

### Logo looks distorted

- Use PNG with transparency for best results
- Set `LOGO_SIZE` to maintain aspect ratio:
  - `LOGO_SIZE="200:-1"` (width fixed, height auto)
  - `LOGO_SIZE="-1:100"` (height fixed, width auto)

### Logo is too big/small

Adjust `LOGO_SIZE`:
```bash
LOGO_SIZE="150:-1"  # Smaller
LOGO_SIZE="300:-1"  # Larger
```

### Logo blocks content

- Reduce opacity: `LOGO_OPACITY="0.6"`
- Reposition: Change `LOGO_POSITION`
- Make smaller: Reduce `LOGO_SIZE`

## Tips

✅ **Best Practices**:
- Use PNG with transparency for professional look
- Keep logo small (100-200px wide) to not block content
- Use subtle opacity (0.6-0.8) for watermarks
- Place in corner that doesn't block important content

❌ **Avoid**:
- Very large logos that block the view
- Logos in center of screen
- Fully opaque logos on important content areas

## Disable Logo

To disable logo overlay:

```bash
# In config.sh
LOGO_ENABLED="false"
```

Then restart stream:
```bash
./control.sh restart
```
