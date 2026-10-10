"""Colors of the user interface, in one place.

Only the dark palette exists so far. The light palette and the switch between them come with the theme toggle.
"""

PALETTE = {
    "sidebar": "#22303f",
    "panel": "#2a3f55",
    "preview_bg": "#f6f9fc",
    "window_bg": "#e9eff6",
    "green": "#2aa650",
    "blue": "#2d8fca",
    "red": "#d94836",
    "orange": "#e67e22",
    "muted": "#5f6b77",
    "white": "#ffffff",
    "black": "#000000",
}


def hover_color(color: str, factor: float = 0.85) -> str:
    """Returns a darker '#rrggbb' version of a color, used for hover states."""
    red, green, blue = (int(color[i:i + 2], 16) for i in (1, 3, 5))
    return "#{:02x}{:02x}{:02x}".format(*(round(channel * factor) for channel in (red, green, blue)))
