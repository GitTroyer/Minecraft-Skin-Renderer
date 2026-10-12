# Minecraft Skin Renderer

![Minecraft Skin Renderer logo](MCSR_logo.png)

A lightweight Python library for rendering Minecraft player skins as:

- 2D static images
- 3D-style rotating animations in GIF format
- OpenGL-based generated previews using the skin texture directly

This project is useful for creating profile previews, skin showcases, Discord/website assets, and animated Minecraft skin cards.

---

## Features

- Load the Minecraft skin texture from a URL
- Accept 64x64 and 128x128 skin textures
- Render a static PNG image
- Render a rotating animated GIF
- Uses OpenGL via `moderngl` for fast 3D-style rendering
- Simple Python API for quick integration


## Installation

Install from PyPI:

```bash
pip install minecraft-skin-renderer
```

For local development:

```bash
git clone https://github.com/GitTroyer/Minecraft-Skin-Renderer.git
cd Minecraft-Skin-Renderer
```


## Requirements

- Python 3.9+
- numpy
- requests
- Pillow
- moderngl
- termcolor

These dependencies are automatically installed when you install the package properly.


## Quick Start

```python
from minecraft_skin_renderer import render_skin_image, render_skin_gif
import os

skin_url="http://textures.minecraft.net/texture/75eb993fa75e1ef66cdb432c484850e8e1b32af07293014e06665ba0ac32a3ad"

os.makedirs("renders", exist_ok=True)

render_skin_image(
    skin_url=skin_url,
    output_path="renders/skin_render.png",
    width=512,
    height=512,
)

render_skin_gif(
    skin_url=skin_url,
    output_path="renders/skin_animation.gif",
    width=512,
    height=512,
    num_frames=120,
    fps=30,
)
```


## API Reference

### `render_skin_image(skin_url: str, output_path: str, width: int = 512, height: int = 512) -> str`

Render a single skin preview as a PNG image.

Parameters:

- `skin_url`: URL of the Minecraft skin image (64x64 or 128x128)
- `output_path`: Destination file path for the output PNG
- `width`: Output width in pixels
- `height`: Output height in pixels

Returns:

- The output path as a string

### `render_skin_gif(skin_url: str, output_path: str, width: int = 512, height: int = 512, num_frames: int = 120, fps: int = 30) -> str`

Render a full 360-degree animated preview of the skin as a GIF.

Parameters:

- `skin_url`: URL of the Minecraft skin image
- `output_path`: Output GIF path
- `width`: GIF width in pixels
- `height`: GIF height in pixels
- `num_frames`: Total number of frames in the animation
- `fps`: Frames per second

Returns:

- The generated GIF path


## Example Output

The library creates images like this:

- **A static 3D-styled render**

    ![Skin 3D Render PNG](src/renders/MC_skin_3d.png)

- **A rotating GIF animation around the character model**

    ![Skin 3D Render GIF](src/renders/MC_skin_3d_turnable.gif)

The default example uses a Minecraft skin texture URL and saves it to the `renders/` directory.


## Supported Skin Types

The renderer supports:

- 64x64 skins
- 128x128 skins automatically resized to the standard 64x64 format for rendering

If the image is not in a compatible format, the library raises a `ValueError`.


## Development Notes

This project is designed to be easy to extend. You can add:

- custom lighting
- different camera angles
- pose presets
- CLI arguments
- support for custom output formats


## Contributing

Contributions are welcome. If you want to improve the rendering quality, fix compatibility issues, or add new features, feel free to open a pull request or issue.


## Useful Links

- PyPI package: on it
- GitHub repository: https://github.com/GitTroyer/Minecraft-Skin-Renderer
- Pull requests: https://github.com/GitTroyer/Minecraft-Skin-Renderer/pulls
- Issues: https://github.com/GitTroyer/Minecraft-Skin-Renderer/issues


## License

This project is distributed under the [MIT license](https://github.com/GitTroyer/Minecraft-Skin-Renderer/blob/main/LICENSE) unless otherwise noted.

---

