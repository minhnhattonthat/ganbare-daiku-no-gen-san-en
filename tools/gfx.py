"""gfx.py: graphics text redrawn in English (phase 8, docs/re/graphics.md). build.py applies patches(rom) after
engine.apply; each new block is a raw (type 14) block in bank D8, and the loader's LDX/LDY operands point at it.

- **G1 title board** (BG2, tiles 0x8ED54, 4x4 metatile defs 0x919BC, layout 0x91EE2 = 8x8 metatiles): the board is
  rendered from the ROM, the kanji and mallet inside its frame are erased (masked, then the wood grain carried down
  each column), and HAMMERIN' / HARRY is lettered in the carved style of the original (striped blue groove, rim,
  extrusion) with Lilita One (fonts/, OFL). Changed cells get new tiles; ids only the old lettering used are reused.

    python -X utf8 tools/gfx.py [--png DIR]   # write the redrawn images (and the original) as PNGs to look at
"""
import collections
import math
import struct
import sys
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from gfxcomp import decompress  # noqa: E402

GFX = 0x180000  # D8:0000, free space for the new blocks
FONT = ROOT / "fonts" / "LilitaOne-Regular.ttf"
TILES, DEFS, LAYOUT = 0x8ED54, 0x919BC, 0x91EE2
LOADS = {TILES: 0x21952, DEFS: 0x2195C}  # LDX #lo / LDY #bank (a2 lo hi a0 bb 00) that name each block
# CGRAM sub-palettes 1-3, colours 8-15 (title screen); 1 = wood, 2 = wood + red, 3 = wood + blue
PAL = {1: (0x0000, 0x006C, 0x0CF0, 0x19BA, 0x1A1D, 0x269F, 0x3ADF, 0x6FBD),
       2: (0x0000, 0x001B, 0x151F, 0x0CF0, 0x19BA, 0x1A1D, 0x269F, 0x6FBD),
       3: (0x0000, 0x5400, 0x7CE3, 0x0CF0, 0x19BA, 0x1A1D, 0x269F, 0x6FBD)}
BOARD = (3, 0, 5, 7)    # metatile x, y, w, h of the board in the 8x8 layout
INSIDE = (8, 16, 128, 176)  # px inside the frame, board-relative: the part that is redrawn


def rgb(c):
    return (c & 31) * 8, (c >> 5 & 31) * 8, (c >> 10 & 31) * 8


COLOURS = {n: [(0, 0, 0)] * 8 + [rgb(c) for c in p] for n, p in PAL.items()}
BLACK, BLUE_D, BLUE, BROWN, RUST, ORANGE, AMBER, WHITE = COLOURS[3][8:]


def tile_px(tiles, t):
    """4bpp planar tile -> 64 indices."""
    b = tiles[32 * t:32 * t + 32]
    return [sum(((b[2 * y + (p & 1) + 16 * (p >> 1)] >> (7 - x)) & 1) << p for p in range(4))
            for y in range(8) for x in range(8)]


def tile_bytes(px):
    out = bytearray(32)
    for y in range(8):
        for x in range(8):
            v = px[8 * y + x]
            for p in range(4):
                if v >> p & 1:
                    out[2 * y + (p & 1) + 16 * (p >> 1)] |= 0x80 >> x
    return bytes(out)


def entry_px(tiles, e):
    px = tile_px(tiles, e & 0x3FF)
    rows = [px[8 * y:8 * y + 8] for y in range(8)]
    if e & 0x4000:
        rows = [r[::-1] for r in rows]
    if e & 0x8000:
        rows = rows[::-1]
    return [v for r in rows for v in r]


def cells_of(lay, gw, rect):
    """{(cx, cy): index into defs} for every 8x8 cell of rect (metatile x, y, w, h in a layout gw metatiles wide),
    rect-relative. A layout word is the metatile's byte offset in the defs (4x4 entries, 32 bytes each)."""
    mx0, my0, mw, mh = rect
    cells = {}
    for my in range(mh):
        for mx in range(mw):
            m = lay[(my0 + my) * gw + mx0 + mx] & ~0x1F  # low bits: flags (8 = blank/priority), not offset
            for ty in range(4):
                for tx in range(4):
                    cells[(4 * mx + tx, 4 * my + ty)] = m // 2 + 4 * ty + tx
    return cells


def render(tiles, defs, cells, colours, size):
    """RGB image of the cells; colour 0 and palettes not in colours draw black."""
    img = Image.new("RGB", size)
    for (cx, cy), i in cells.items():
        e = defs[i]
        pal = colours.get(e >> 10 & 7)
        for k, v in enumerate(entry_px(tiles, e)):
            img.putpixel((8 * cx + k % 8, 8 * cy + k // 8), pal[v] if pal and v else (0, 0, 0))
    return img


def erase(img):
    """Plain wood inside the frame: the grain of the first clean row carried down, swaying left and right."""
    x0, y0, w, h = INSIDE
    src = [img.getpixel((x, y0 + 1)) for x in range(x0, x0 + w)]
    out = img.copy()
    for y in range(y0, y0 + h):
        for x in range(w):
            out.putpixel((x0 + x, y), src[min(w - 1, max(0, x + round(3 * math.sin(y / 13 + x / 23))))])
    return out


def word(text, box):
    """1-bit mask of text scaled to fill box (w, h), no antialiasing."""
    f = ImageFont.truetype(str(FONT), 96)
    l, t, r, b = f.getbbox(text)
    m = Image.new("L", (r - l + 4, b - t + 4))
    ImageDraw.Draw(m).text((2 - l, 2 - t), text, font=f, fill=255)
    m = m.crop(m.getbbox()).resize(box, Image.LANCZOS)
    return m.point(lambda v: 255 if v >= 128 else 0)


def letters(text, box, gap):
    """[(mask, x)] one per letter, widths in the font's proportions, filling box (w, h) with gap px between."""
    f = ImageFont.truetype(str(FONT), 96)
    ws = [f.getbbox(c)[2] - f.getbbox(c)[0] for c in text]
    scale = (box[0] - gap * (len(text) - 1)) / sum(ws)
    out, x = [], 0
    for c, w in zip(text, ws):
        out.append((word(c, (round(w * scale), box[1])), x))
        x += round(w * scale) + gap
    return out


def emboss(img, mask, at):
    """Raised wooden letters with a black outline and a brown drop shadow (the original's small がんばれ!)."""
    big = Image.new("L", img.size)
    big.paste(mask, at)
    edge = big.filter(ImageFilter.MaxFilter(3))
    shadow = ImageChops.offset(edge, 1, 1)
    shadow = ImageChops.lighter(shadow, ImageChops.offset(edge, 2, 2))
    px = img.load()
    w, h = img.size
    for y in range(h):
        for x in range(w):
            if big.getpixel((x, y)):
                top = y and not big.getpixel((x, y - 1)) or x and not big.getpixel((x - 1, y))
                px[x, y] = AMBER if top else ORANGE
            elif edge.getpixel((x, y)):
                px[x, y] = BLACK
            elif shadow.getpixel((x, y)):
                px[x, y] = BROWN
    return img


def carve(img, mask, at):
    """Letters cut into the board: striped blue groove with a dark top-left inner shadow, an orange rim with a dark
    outer edge, a brown extrusion down-right and a white glint on top-left corners."""
    big = Image.new("L", img.size)
    big.paste(mask, at)
    rim = big.filter(ImageFilter.MaxFilter(5))
    edge = rim.filter(ImageFilter.MaxFilter(3))
    ext = Image.new("L", img.size)
    for d in (1, 2, 3):
        ext = ImageChops.lighter(ext, ImageChops.offset(edge, d, d))
    w, h = img.size
    px = img.load()
    for y in range(h):
        for x in range(w):
            def on(m, dx=0, dy=0):
                return 0 <= x + dx < w and 0 <= y + dy < h and m.getpixel((x + dx, y + dy))
            if on(big):
                px[x, y] = BLUE_D if not on(big, -1, -1) or (x + y) // 2 % 2 else BLUE
            elif on(rim):
                px[x, y] = AMBER if not on(rim, -1, -1) else ORANGE if not on(rim, 1, 1) else RUST
                if not on(rim, -1, 0) and not on(rim, 0, -1):
                    px[x, y] = WHITE
            elif on(edge):
                px[x, y] = BROWN if on(edge, -1, -1) else BLACK
            elif on(ext):
                px[x, y] = BROWN
    return img


def letter(img):
    x0, y0, w, _ = INSIDE
    emboss(img, word("HAMMERIN'", (w - 10, 34)), (x0 + 4, y0 + 10))
    for m, x in letters("HARRY", (w - 14, 92), 4):
        carve(img, m, (x0 + 5 + x, y0 + 60))
    return img


def changed_cells(img, orig, cells):
    return [c for c in cells if any(img.getpixel((8 * c[0] + k % 8, 8 * c[1] + k // 8)) !=
                                    orig.getpixel((8 * c[0] + k % 8, 8 * c[1] + k // 8)) for k in range(64))]


def encode(tiles, defs, jobs):
    """jobs = [(img, cells, changed, pick)]: each changed cell gets a tile (deduplicated) and its def entry;
    pick(pixels, old entry) -> (palette, colours, first usable index). Tile ids that only changed cells used are reused, then
    the set grows. Returns (tiles, defs)."""
    tiles, defs = bytearray(tiles), list(defs)
    redrawn = {cells[c] for _, cells, changed, _ in jobs for c in changed}
    keep = {d & 0x3FF for i, d in enumerate(defs) if i not in redrawn}
    free = sorted({defs[i] & 0x3FF for i in redrawn} - keep - {0})
    made = {}
    for img, cells, changed, pick in jobs:
        for c in sorted(changed, key=lambda c: (c[1], c[0])):
            px = [img.getpixel((8 * c[0] + k % 8, 8 * c[1] + k // 8)) for k in range(64)]
            pal, cols, lo = pick(px, defs[cells[c]])
            idx = [min(range(lo, 16), key=lambda n: sum((a - b) ** 2 for a, b in zip(cols[n], p))) for p in px]
            for k, v in enumerate(idx):  # the image shows what ships
                img.putpixel((8 * c[0] + k % 8, 8 * c[1] + k // 8), cols[v])
            data = tile_bytes(idx)
            if data not in made:
                if free:
                    t = free.pop(0)
                    tiles[32 * t:32 * t + 32] = data
                else:
                    t = len(tiles) // 32
                    tiles += data
                made[data] = t
            defs[cells[c]] = defs[cells[c]] & 0x2000 | pal << 10 | made[data]
    return bytes(tiles), defs


def raw(data):
    return bytes([14]) + struct.pack("<H", len(data)) + data


def title(rom):
    """-> ([(name, original, English image)], {block: new data})"""
    tiles = decompress(rom, TILES)[0]
    defs = list(struct.unpack("<880H", decompress(rom, DEFS)[0]))
    lay = struct.unpack("<64H", decompress(rom, LAYOUT)[0])
    cells = cells_of(lay, 8, BOARD)
    orig = render(tiles, defs, cells, COLOURS, (32 * BOARD[2], 32 * BOARD[3]))
    img = letter(erase(orig))

    def pick(px, _):
        pal = 3 if {BLUE, BLUE_D} & set(px) else 1
        return pal, COLOURS[pal], 8
    new_tiles, new_defs = encode(tiles, defs, [(img, cells, changed_cells(img, orig, cells), pick)])
    return [("title", orig, img)], {TILES: new_tiles, DEFS: struct.pack("<880H", *new_defs)}


B_TILES, B_DEFS, B_LAYOUT = 0x8AF06, 0x8DEBE, 0x8E98B
LOADS |= {B_TILES: 0x2340C, B_DEFS: 0x23416}
# CGRAM sub-palette 4 on the closed book (the plaque); its text is colour 0, holes onto the red cover below
B_PAL = {4: [rgb(c) for c in (0x0000, 0x437F, 0x32FD, 0x227B, 0x1619, 0x0DB6, 0x0953, 0x0000,
                              0x0885, 0x18FD, 0x0879, 0x000C, 0x6B5A, 0x5EB5, 0x5252, 0x41CE)]}
# the plaque on the closed cover, and its copy on the cover lifting off (squeezed, sheared, top cut off), in the
# 16x16-metatile BG1 layout: (rect in metatiles, plaque body columns rect-relative)
PLAQUES = (((5, 0, 2, 3), (18, 61)), ((12, 0, 2, 2), (20, 59)))
# 3x7 pixel capitals (M 5, N 4, I and ' 1 wide), drawn as holes in the plaque
PIXEL_FONT = {
    "H": ("#.#", "#.#", "#.#", "###", "#.#", "#.#", "#.#"),
    "A": (".#.", "#.#", "#.#", "###", "#.#", "#.#", "#.#"),
    "M": ("#...#", "##.##", "#.#.#", "#.#.#", "#...#", "#...#", "#...#"),
    "E": ("###", "#..", "#..", "###", "#..", "#..", "###"),
    "R": ("##.", "#.#", "#.#", "##.", "#.#", "#.#", "#.#"),
    "I": ("#",) * 7,
    "N": ("#..#", "##.#", "##.#", "#.##", "#.##", "#..#", "#..#"),
    "'": ("#", "#", ".", ".", ".", ".", "."),
    "Y": ("#.#", "#.#", "#.#", ".#.", ".#.", ".#.", ".#."),
}


def pixel_text(text, scale=1):
    """[(x, y)] ink pixels of text in PIXEL_FONT, 1 px apart, each pixel scale x scale; and the width."""
    out, x = [], 0
    for c in text:
        g = PIXEL_FONT[c]
        for y, row in enumerate(g):
            for gx, v in enumerate(row):
                if v == "#":
                    out += [(scale * (x + gx) + i, scale * y + j) for i in range(scale) for j in range(scale)]
        x += len(g[0]) + 1
    return out, scale * (x - 1)


def holes(img, cols):
    """Colour-0 pixels inside the plaque body (plaque on both sides along the row, within cols)."""
    w, h = img.size
    out = set()
    for y in range(h):
        row = [img.getpixel((x, y)) != (0, 0, 0) for x in range(w)]
        for x in range(cols[0], cols[1]):
            if not row[x] and any(row[cols[0]:x]) and any(row[x + 1:cols[1]]):
                out.add((x, y))
    return out


def fill_holes(img, pts):
    """Each hole takes the colour along the plaque's 45-degree shading bands (up-right, else down-left)."""
    w, h = img.size
    for x, y in sorted(pts):
        for k in range(1, 40):
            for px, py in ((x + k, y - k), (x - k, y + k)):
                if 0 <= px < w and 0 <= py < h and (px, py) not in pts and img.getpixel((px, py)) != (0, 0, 0):
                    img.putpixel((x, y), img.getpixel((px, py)))
                    break
            else:
                continue
            break


def bottoms(img, cols):
    """Lowest plaque pixel of each body column (to map the flat plaque onto the lifted one)."""
    return {x: max(y for y in range(img.size[1]) if img.getpixel((x, y)) != (0, 0, 0)) for x in range(*cols)
            if any(img.getpixel((x, y)) != (0, 0, 0) for y in range(img.size[1]))}


B_BACK = 0x8EB23  # BG1 layout of the back cover (book variant 1, after the ending)
BACK_RECT = (0, 8, 16, 8)  # metatiles: screens 2-3, the flat back cover and its copy lifting off
# flat ©アイレム line: アイレム (x0, y0, x1, y1 px in BACK_RECT) becomes IREM; the lifted copy is the flat line
# squeezed and sheared: x' = X + (x - FX) * SX, y' = Y + (y - FY) + (x - FX) * SY
KANA = (56, 191, 88, 201)
LIFT = (48, 192, 352, 157, 0.82, 0.21)  # fitted to the © and the end of the kana (the digits' far end agrees)


def back_cover(rom, tiles, defs, jobs):
    """G3: the back cover's copyright line spells the publisher in katakana (アイレム); English: IREM, in the same
    gold (colour 3) with the dark shadow (colour 8) right and below, on the flat cover and the lifted copy."""
    lay = struct.unpack("<256H", decompress(rom, B_BACK)[0])
    cells = cells_of(lay, 16, BACK_RECT)
    orig = render(tiles, defs, cells, B_PAL, (32 * BACK_RECT[2], 32 * BACK_RECT[3]))
    img = orig.copy()
    gold, shade = B_PAL[4][3], B_PAL[4][8]
    x0, y0, x1, y1 = KANA
    fx, fy, lx, ly, sx, sy = LIFT

    def lifted(x, y):
        return round(lx + (x - fx) * sx), round(ly + (y - fy) + (x - fx) * sy)

    def lifted_ink(x, y):  # letters keep their width (squeezed 4 px letters merge); only the start moves
        return round(lx + (x0 - fx) * sx) + x - x0, round(ly + (y - fy) + (x - fx) * sy)
    for x in range(x0, x1):
        for y in range(y0, y1):
            for p in ((x, y), lifted(x, y)):
                if img.getpixel(p) in (gold, shade):
                    img.putpixel(p, (0, 0, 0))
    pts, _ = pixel_text("IREM")
    ink = {(x0 + 1 + x, y0 + 1 + y) for x, y in pts}
    for x, y in sorted(ink):
        for p in ((x + 1, y), (x, y + 1), (x + 1, y + 1)):
            if p not in ink:
                img.putpixel(p, shade)
                img.putpixel(lifted_ink(*p), shade)
    for p in ink:
        img.putpixel(p, gold)
        img.putpixel(lifted_ink(*p), gold)
    jobs.append((img, cells, changed_cells(img, orig, cells), lambda px, _: (4, B_PAL[4], 0)))
    return orig, img


def book(rom):
    tiles = decompress(rom, B_TILES)[0]
    n = len(decompress(rom, B_DEFS)[0]) // 2
    defs = list(struct.unpack(f"<{n}H", decompress(rom, B_DEFS)[0]))
    lay = struct.unpack("<256H", decompress(rom, B_LAYOUT)[0])
    imgs, jobs, ink = [], [], []
    for k, (rect, cols) in enumerate(PLAQUES):
        cells = cells_of(lay, 16, rect)
        orig = render(tiles, defs, cells, B_PAL, (32 * rect[2], 32 * rect[3]))
        img = orig.copy()
        fill_holes(img, holes(img, cols))
        if k == 0:
            # HAMMERIN' over a double-size HARRY, centred on the plaque body
            mid = (cols[0] + cols[1]) // 2
            for text, scale, y in (("HAMMERIN'", 1, 33), ("HARRY", 2, 46)):
                pts, w = pixel_text(text, scale)
                ink += [(mid - w // 2 + x, y + yy) for x, yy in pts]
            flat = bottoms(img, cols)
            for p in ink:
                img.putpixel(p, (0, 0, 0))
        else:
            # same pixels on the lifted copy: columns squeezed between the body edges, each column shifted by the
            # difference of the bottom edges
            lift = bottoms(img, cols)
            fx, lx = sorted(flat), sorted(lift)
            for x, y in ink:
                u = lx[0] + round((x - fx[0]) * (len(lx) - 1) / (len(fx) - 1))
                v = y - flat[x] + lift[u]
                if 0 <= v < img.size[1] and img.getpixel((u, v)) != (0, 0, 0):
                    img.putpixel((u, v), (0, 0, 0))
        imgs.append((f"book{k}", orig, img))
        jobs.append((img, cells, changed_cells(img, orig, cells), lambda px, _: (4, B_PAL[4], 0)))
    imgs.append(("back",) + back_cover(rom, tiles, defs, jobs))
    new_tiles, new_defs = encode(tiles, defs, jobs)
    return imgs, {B_TILES: new_tiles, B_DEFS: struct.pack(f"<{n}H", *new_defs)}


C_TILES, C_DEFS, C_LAYOUT = 0x788C5, 0x792F5, 0x7949C
LOADS |= {C_TILES: 0x23ACA, C_DEFS: 0x23AD4}
# CGRAM sub-palettes 2 (light sign) and 3 (dark sign) on the continue screen
C_PAL = {n: [rgb(c) for c in p] for n, p in (
    (2, (0x3235, 0x7BDD, 0x0000, 0x1E1B, 0x32FF, 0x539E, 0x006B, 0x0935, 0x00B0, 0x00AB, 0x0D2F, 0x19B3, 0x2A37,
         0x0068, 0x0000, 0x0000)),
    (3, (0x3235, 0x7BDD, 0x0000, 0x006A, 0x008D, 0x00CF, 0x0023, 0x0048, 0x0026, 0x00AB, 0x0D2F, 0x19B3, 0x2A37,
         0x0068, 0x0000, 0x0000)))}
# lettered part of each sign face (x0, y0, x1, y1 px in the 8x8-metatile layout), its palette, the new word;
# letters are colour 5 with a colour-6 outline in both palettes
SIGNS = (((29, 98, 86, 125), 2, "YEAH!"), ((181, 98, 237, 125), 3, "NOPE"))


def signs(rom):
    """Continue screen (G6): the two carved signposts, retry (left) and quit (right). Letter pixels take their
    row's commonest other colour (the grain runs along the log), then the English is cut in the same two colours."""
    tiles = decompress(rom, C_TILES)[0]
    n = len(decompress(rom, C_DEFS)[0]) // 2
    defs = list(struct.unpack(f"<{n}H", decompress(rom, C_DEFS)[0]))
    lay = struct.unpack("<64H", decompress(rom, C_LAYOUT)[0])
    cells = cells_of(lay, 8, (0, 0, 8, 8))
    orig = render(tiles, defs, cells, C_PAL, (256, 256))
    img = orig.copy()
    for (x0, y0, x1, y1), pal, text in SIGNS:
        fill, line = C_PAL[pal][5], C_PAL[pal][6]
        for y in range(y0, y1):
            row = [img.getpixel((x, y)) for x in range(x0, x1)]
            bg = collections.Counter(c for c in row if c not in (fill, line)).most_common(1)[0][0]
            for x in range(x0, x1):
                if img.getpixel((x, y)) in (fill, line):
                    img.putpixel((x, y), bg)
        big = Image.new("L", img.size)
        big.paste(word(text, (x1 - x0 - 6, y1 - y0 - 8)), (x0 + 3, y0 + 4))
        rim = big.filter(ImageFilter.MaxFilter(3))
        for y in range(y0, y1):
            for x in range(x0, x1):
                if big.getpixel((x, y)):
                    img.putpixel((x, y), fill)
                elif rim.getpixel((x, y)):
                    img.putpixel((x, y), line)

    def pick(px, entry):
        pal = entry >> 10 & 7
        return pal, C_PAL[pal], 1
    new_tiles, new_defs = encode(tiles, defs, [(img, cells, changed_cells(img, orig, cells), pick)])
    return [("continue", orig, img)], {C_TILES: new_tiles, C_DEFS: struct.pack(f"<{n}H", *new_defs)}


S_TILES = 0xD44A0  # raw 4bpp OBJ tiles, VRAM C000 in stage play (tile t at S_TILES + 32t)
# the shout's 11 sprites (OAM in stage play): x, y px in its 64x32 box, first tile, 16x16
S_SPRITES = ((0, 16, 0x0E, 1), (32, 16, 0x20, 1), (48, 16, 0x22, 1), (48, 0, 0x24, 1), (0, 8, 0x28, 0),
             (8, 8, 0x29, 0), (16, 8, 0x26, 1), (16, 24, 0x2A, 0), (24, 24, 0x2B, 0), (32, 8, 0x2C, 0),
             (40, 8, 0x2D, 0))
S_PAL = [rgb(c) for c in (0x4210, 0x0000, 0x11BE, 0x1E9F, 0x4F5F, 0x00AD, 0x1FFE, 0x1B5F, 0x6F59, 0x5672, 0x00BF,
                          0x5109, 0x3001, 0x261C, 0x5FFF, 0x7FFF)]  # OBJ palette 0
S_WORD = 55  # the kana (い reaches into the ! sprites) end here; the tall ! (x 55-63) is kept
OUTLINE, SHADE, GLINT = 1, 0xC, 0xF


def shout_cells():
    """[(tile, x, y)] for each 8x8 tile of the shout."""
    return [(t + k, x + 8 * (k & 1), y + 8 * (k >> 4)) for x, y, t, big in S_SPRITES for k in ((0, 1, 16, 17)
                                                                                           if big else (0,))]


def shout(rom):
    """G8: Gen-san's flaming てやんでい! pop-up (enemy beaten, game over) as TEYANDEI!: the kana's per-row flame colours
    (2-colour dither by column parity), black outline, dark-blue shadow below, white glint on top edges.
    Returns (orig, img) as palette-index images and the in-place tile writes."""
    orig = Image.new("L", (64, 32))
    for t, x, y in shout_cells():
        for k, v in enumerate(tile_px(rom[S_TILES:S_TILES + 0x800], t)):
            orig.putpixel((x + k % 8, y + k // 8), v)
    fills = {}
    for y in range(32):
        for p in (0, 1):
            c = collections.Counter(orig.getpixel((x, y)) for x in range(p, S_WORD, 2))
            c = [v for v, _ in c.most_common() if v not in (0, OUTLINE, SHADE, 0xE, GLINT)]
            if c:
                fills[y, p] = c[0]
    img = orig.copy()
    ImageDraw.Draw(img).rectangle((0, 0, S_WORD - 1, 31), fill=0)
    big = Image.new("L", img.size)
    for m, x in letters("TEYANDEI", (S_WORD - 3, 18), 1):
        big.paste(m, (1 + x, 10))
    edge = big.filter(ImageFilter.MaxFilter(3))
    shadow = ImageChops.lighter(ImageChops.offset(edge, 0, 1), ImageChops.offset(edge, 1, 2))
    for y in range(32):
        for x in range(S_WORD):
            if big.getpixel((x, y)):
                near = min((k for k in fills if k[1] == x % 2), key=lambda k: abs(k[0] - y))
                img.putpixel((x, y), GLINT if not big.getpixel((x, y - 1)) else fills[near])
            elif edge.getpixel((x, y)):
                img.putpixel((x, y), OUTLINE)
            elif shadow.getpixel((x, y)):
                img.putpixel((x, y), SHADE)
    writes = []
    for t, x, y in shout_cells():
        new = tile_bytes([img.getpixel((x + k % 8, y + k // 8)) for k in range(64)])
        old = rom[S_TILES + 32 * t:S_TILES + 32 * t + 32]
        if new != old:
            writes.append((S_TILES + 32 * t, old, new, f"G8 shout OBJ tile {t:02X}"))
    return (orig, img), writes


def shout_rgb(img):
    out = Image.new("RGB", img.size)
    out.putdata([S_PAL[v] for v in img.getdata()])
    return out


SCREENS = ((title, "G1 title"), (book, "G2 book cover"), (signs, "G6 continue signs"))


def patches(rom):
    """[(offset, old bytes, new bytes, why)] for build.py; rom = the expanded ROM."""
    out, at = [], GFX
    for screen, what in SCREENS:
        for blk, data in screen(rom)[1].items():
            new = raw(data)
            assert len(new) <= 0x10000 - (at & 0xFFFF), what
            out.append((at, b"\xff" * len(new), new, f"{what} block {blk:06X}"))
            ld = LOADS[blk]
            old = bytes([0xA2, blk & 0xFF, blk >> 8 & 0xFF, 0xA0, 0xC0 | blk >> 16, 0])
            new_ld = bytes([0xA2, at & 0xFF, at >> 8 & 0xFF, 0xA0, 0xC0 | at >> 16, 0])
            out.append((ld, old, new_ld, f"{what} block {blk:06X} pointer"))
            at += len(new)
    return out + shout(rom)[1]


def main():
    rom = (ROOT / "rom" / "Ganbare! Daiku no Gen-san (Japan).sfc").read_bytes()
    d = Path(sys.argv[sys.argv.index("--png") + 1] if "--png" in sys.argv else ROOT / "work" / "gfx")
    d.mkdir(parents=True, exist_ok=True)
    for screen, what in SCREENS:
        imgs, blocks = screen(rom)
        for name, orig, img in imgs:
            orig.save(d / f"{name}_jp.png")
            img.save(d / f"{name}_en.png")
        print(what, {f"{b:06X}": len(v) for b, v in blocks.items()})
    (orig, img), writes = shout(rom)
    for name, im in (("shout_jp", orig), ("shout_en", img)):
        shout_rgb(im).resize((512, 256), Image.NEAREST).save(d / f"{name}.png")
    print("G8 shout", len(writes), "tiles")


if __name__ == "__main__":
    main()
