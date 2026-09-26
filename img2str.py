import numpy as np

UPPER_BLOCK = '▀'
BLOCKS = np.array([*' ▄▀█'])


def img_to_str(img: np.ndarray) -> str:
    if img.ndim == 3 and img.shape[2] > 1:
        return img_to_str_rgb(img)
    elif img.dtype == np.bool:
        return img_to_str_bin(img)
    else:
        return img_to_str_gray(img)


def print_img(img: np.ndarray):
    print(img_to_str(img))


class ImgArray(np.ndarray):
    def __new__(cls, object, dtype=None, **kwargs):
        return np.array(object, dtype, **kwargs).view(cls)

    def __repr__(self):
        if self.ndim == 2 or self.ndim == 3 and self.shape[2] in (1, 3, 4):
            return img_to_str(self)
        return super().__repr__()


def img_to_str_bin(img: np.ndarray) -> str:
    img = np.asarray(img, bool)
    height, width = img.shape
    char_inds = img[::2]*2
    char_inds[:height//2] += img[1::2]
    lines = BLOCKS[char_inds].view(f'U{width or 1}').ravel().tolist()
    return '\n'.join(lines)


def img_to_str_gray(img: np.ndarray) -> str:
    if np.issubdtype(img.dtype, np.floating):
        img = img * 255.
    img = np.clip(img, 0, 255).astype(np.uint8)
    if img.ndim == 3:
        # drop singleton channel dimension
        img = img.squeeze(2)
    height, width = img.shape
    lines = []
    for i in range(0, height, 2):
        line = []
        for j in range(width):
            upper = img[i, j]
            line.append(f'\x1b[38;2;{upper};{upper};{upper}m')
            if i+1 < height:
                lower = img[i+1, j]
                line.append(f'\x1b[48;2;{lower};{lower};{lower}m')
            line.append(UPPER_BLOCK)
        lines.append(''.join(line) + '\x1b[0m')
    return '\n'.join(lines)


def img_to_str_rgb(img: np.ndarray) -> str:
    if np.issubdtype(img.dtype, np.floating):
        img = img * 255.
    img = np.clip(img, 0, 255).astype(np.uint8)
    height, width, _ = img.shape
    # drop alpha channel if present
    img = img[:, :, :3]
    lines = []
    for i in range(0, height, 2):
        line = []
        for j in range(width):
            ur, ug, ub = img[i, j]
            line.append(f'\x1b[38;2;{ur};{ug};{ub}m')
            if i+1 < height:
                lr, lg, lb = img[i+1, j]
                line.append(f'\x1b[48;2;{lr};{lg};{lb}m')
            line.append(UPPER_BLOCK)
        lines.append(''.join(line) + '\x1b[0m')
    return '\n'.join(lines)
