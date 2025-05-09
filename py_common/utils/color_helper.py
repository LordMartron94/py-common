from typing import Union, Tuple, Dict

class ColorHelper:
    """
    Helper class meant to streamline the use of colors for several purposes.
    """

    def __init__(self):
        # Cache for storing converted hex to RGB values
        self._rgb_cache: Dict[str, Tuple[int, int, int]] = {}

    def _convert_hex_to_rgb(self, hex_color: str) -> Tuple[int, int, int]:
        """
        Converts a hex color to a tuple of RGB values.
        Uses caching to speed up repeated conversions.
        """
        if hex_color in self._rgb_cache:
            return self._rgb_cache[hex_color]

        # Directly parse the hex string in one go to reduce overhead
        rgb = (int(hex_color[1:3], 16), int(hex_color[3:5], 16), int(hex_color[5:7], 16))
        self._rgb_cache[hex_color] = rgb
        return rgb

    def colorize_string(self, string: str, text_color_hex: str, background_color_hex: Union[str, None] = None) -> str:
        """
        Colorizes a string with a given color.
        """
        # Get the text color (cached or computed)
        text_color_rgb = self._convert_hex_to_rgb(text_color_hex)
        closest_ansi_color_code = f"\x1b[38;2;{text_color_rgb[0]};{text_color_rgb[1]};{text_color_rgb[2]}m"

        # Prepare the colored string
        colored_string = f"{closest_ansi_color_code}{string}"

        # Add background color if specified
        if background_color_hex:
            background_color_rgb = self._convert_hex_to_rgb(background_color_hex)
            closest_ansi_color_code_background = f"\x1b[48;2;{background_color_rgb[0]};{background_color_rgb[1]};{background_color_rgb[2]}m"
            colored_string = f"{closest_ansi_color_code_background}{colored_string}"

        return colored_string
