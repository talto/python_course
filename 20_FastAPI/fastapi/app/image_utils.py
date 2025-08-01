from io import BytesIO
from PIL import Image, ImageDraw
import numpy as np

def make_gradient_png(seed: int = 0, size: int = 256) -> bytes:
    rng = np.random.default_rng(seed)

    # Генерируем шум по каждому цвету
    r = rng.integers(0, 256, (size, size), dtype=np.uint8)
    g = rng.integers(0, 256, (size, size), dtype=np.uint8)
    b = rng.integers(0, 256, (size, size), dtype=np.uint8)

    img = np.stack([r, g, b], axis=-1)
    pil_img = Image.fromarray(img, mode='RGB')

    # Рисуем случайные линии
    draw = ImageDraw.Draw(pil_img)
    for _ in range(5):
        x0 = rng.integers(0, size)
        y0 = rng.integers(0, size)
        x1 = rng.integers(0, size)
        y1 = rng.integers(0, size)
        color = tuple(rng.integers(0, 256, 3).tolist())
        draw.line((x0, y0, x1, y1), fill=color, width=3)

    buf = BytesIO()
    pil_img.save(buf, format="PNG")
    return buf.getvalue()
