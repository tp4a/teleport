""" ``comp`` module.
"""

try:  # pragma: nocover
    from PIL import Image, ImageFilter
    from PIL.ImageColor import getrgb
    from PIL.ImageDraw import Draw
    from PIL.ImageFont import truetype
except ImportError:  # pragma: nocover
    import Image  # noqa
    import ImageFilter  # noqa
    from ImageColor import getrgb  # noqa
    from ImageDraw import Draw  # noqa
    from ImageFont import truetype  # noqa
