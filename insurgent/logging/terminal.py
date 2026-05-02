from insurgent.rich_utils import style_text as rich_style_text

# If you ever want to format output, use Text for color/styling.

def style_text(text, **kwargs):
    """
    Style text with the specified options.
    A convenience wrapper around Rich's text styling.
    """
    return rich_style_text(text, **kwargs)
