"""
"""

import random

from wheezy.captcha.comp import Draw, Image, ImageFilter, getrgb, truetype


def captcha(drawings, width=200, height=75):
    def render(text):
        image = Image.new("RGB", (width, height), (255, 255, 255))
        for drawing in drawings:
            image = drawing(image, text)
            assert image
        return image

    return render


# region: captcha drawers


def background(color="#EEEECC"):
    color = getrgb(color)

    def drawer(image, text):
        Draw(image).rectangle([(0, 0), image.size], fill=color)
        return image

    return drawer


def smooth():
    def drawer(image, text):
        return image.filter(ImageFilter.SMOOTH)

    return drawer


def curve(color="#5C87B2", width=4, number=6):
    from wheezy.captcha.bezier import make_bezier

    if not callable(color):
        c = getrgb(color)

        def color():
            return c

    def drawer(image, text):
        dx, height = image.size
        dx = dx / number
        path = [(dx * i, random.randint(0, height)) for i in range(1, number)]
        bcoefs = make_bezier(number - 1)
        points = []
        for coefs in bcoefs:
            points.append(
                tuple(
                    sum([coef * p for coef, p in zip(coefs, ps)])
                    for ps in zip(*path)
                )
            )
        draw = Draw(image)
        draw.line(points, fill=color(), width=width)
        return image

    return drawer


def noise(number=50, color="#EEEECC", level=2):
    if not callable(color):
        c = getrgb(color)

        def color():
            return c

    def drawer(image, text):
        width, height = image.size
        dx = width / 10
        width = width - dx
        dy = height / 10
        height = height - dy
        draw = Draw(image)
        for _ in range(number):
            x = int(random.uniform(dx, width))
            y = int(random.uniform(dy, height))
            draw.line(((x, y), (x + level, y)), fill=color(), width=level)
        return image

    return drawer


def text(
    fonts, font_sizes=None, drawings=None, color="#5C87B2", squeeze_factor=0.8
):
    fonts = tuple(
        [
            truetype(name, size)
            for name in fonts
            for size in font_sizes or (65, 70, 75)
        ]
    )
    if not callable(color):
        c = getrgb(color)

        def color():
            return c

    def drawer(image, text):
        draw = Draw(image)
        char_images = []
        for c in text:
            font = random.choice(fonts)
            c_width, c_height = draw.textsize(c, font=font)
            char_image = Image.new("RGB", (c_width, c_height), (0, 0, 0))
            char_draw = Draw(char_image)
            char_draw.text((0, 0), c, font=font, fill=color())
            char_image = char_image.crop(char_image.getbbox())
            for drawing in drawings:
                char_image = drawing(char_image)
            char_images.append(char_image)
        width, height = image.size
        offset = int(
            (
                width
                - sum(
                    int(i.size[0] * squeeze_factor) for i in char_images[:-1]
                )
                - char_images[-1].size[0]
            )
            / 2
        )
        for char_image in char_images:
            c_width, c_height = char_image.size
            mask = char_image.convert("L").point(lambda i: i * 1.97)
            image.paste(
                char_image, (offset, int((height - c_height) / 2)), mask
            )
            offset += int(c_width * squeeze_factor)
        return image

    return drawer


# region: text drawers


def warp(dx_factor=0.27, dy_factor=0.21):
    def drawer(image):
        width, height = image.size
        dx = width * dx_factor
        dy = height * dy_factor
        x1 = int(random.uniform(-dx, dx))
        y1 = int(random.uniform(-dy, dy))
        x2 = int(random.uniform(-dx, dx))
        y2 = int(random.uniform(-dy, dy))
        image2 = Image.new(
            "RGB", (width + abs(x1) + abs(x2), height + abs(y1) + abs(y2))
        )
        image2.paste(image, (abs(x1), abs(y1)))
        width2, height2 = image2.size
        return image2.transform(
            (width, height),
            Image.QUAD,
            (
                x1,
                y1,
                -x1,
                height2 - y2,
                width2 + x2,
                height2 + y2,
                width2 - x2,
                -y1,
            ),
        )

    return drawer


def offset(dx_factor=0.1, dy_factor=0.2):
    def drawer(image):
        width, height = image.size
        dx = int(random.random() * width * dx_factor)
        dy = int(random.random() * height * dy_factor)
        image2 = Image.new("RGB", (width + dx, height + dy))
        image2.paste(image, (dx, dy))
        return image2

    return drawer


def rotate(angle=25):
    def drawer(image):
        return image.rotate(
            random.uniform(-angle, angle), Image.BILINEAR, expand=1
        )

    return drawer


if __name__ == "__main__":
    import string

    captcha_image = captcha(
        drawings=[
            background(),
            text(
                fonts=[
                    "fonts/CourierNew-Bold.ttf",
                    "fonts/LiberationMono-Bold.ttf",
                ],
                drawings=[warp(), rotate(), offset()],
            ),
            curve(),
            noise(),
            smooth(),
        ]
    )
    image = captcha_image(random.sample(string.uppercase + string.digits, 4))
    image.save("sample.jpg", "JPEG", quality=75)
