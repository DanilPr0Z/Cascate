"""
Vertical product label — dynamic height.

  ┌──────────────────────┐  HEADER  (логотип по центру)
  ├──────────────────────┤
  │  Название товара     │
  │ ──────────────────── │
  │  Материалы: …        │  автоперенос, всё помещается
  │  Размеры:   …        │
  │  Страна:    …        │
  │ ──────────────────── │
  │  9 999 ₽             │  или зачёркнуто + новая + бейдж
  ├──────────────────────┤  ← 20px отступ от цены
  │    ┌────────────┐    │  QR по центру
  │    │  QR CODE   │    │
  │    └────────────┘    │
  │   Отсканируйте QR    │
  └──────────────────────┘

Ширина: 650px, высота: авто (контент + QR-блок).
"""

from PIL import Image, ImageDraw, ImageFont
import qrcode as qrcode_lib
import os

# ── Palette ───────────────────────────────────────────────────────────────────
C_WHITE       = '#ffffff'
C_DIVIDER     = '#cccccc'
C_LABEL       = '#888888'
C_VALUE       = '#111111'
C_NAME        = '#000000'
C_PRICE       = '#000000'
C_PRICE_OLD   = '#aaaaaa'
C_DISCOUNT_BG = '#1a1a1a'
C_DISCOUNT_FG = '#ffffff'
C_QR_BG       = '#f4f4f4'
C_QR_CAPTION  = '#888888'

# ── Fixed dimensions ──────────────────────────────────────────────────────────
W          = 650
PAD        = 32
HEADER_H   = 80
LABEL_COL  = 130
GAP_QR     = 20
QR_PAD     = 24
CAPTION_H  = 28


def _load_fonts(base=22):
    from django.conf import settings
    candidates = [
        os.path.join(settings.BASE_DIR, 'static', 'fonts', 'DejaVuSans-Bold.ttf'),
        os.path.join(settings.BASE_DIR, 'static', 'fonts', 'DejaVuSans.ttf'),
        '/System/Library/Fonts/Supplemental/Arial Unicode.ttf',
        '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',
        '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
    ]
    path = next((p for p in candidates if os.path.exists(p)), None)
    if not path:
        f = ImageFont.load_default()
        return {k: f for k in ('caption', 'small', 'regular', 'bold', 'price', 'price_old', 'badge')}

    def ttf(sz):
        return ImageFont.truetype(path, sz)

    return {
        'caption':   ttf(int(base * 0.70)),
        'small':     ttf(int(base * 0.86)),
        'regular':   ttf(base),
        'bold':      ttf(int(base * 1.45)),
        'price':     ttf(int(base * 2.05)),
        'price_old': ttf(int(base * 1.40)),
        'badge':     ttf(int(base * 0.82)),
    }


def _wrap(text, font, max_width, draw):
    words = text.split()
    if not words:
        return ['']
    lines, cur = [], []
    for word in words:
        test = ' '.join(cur + [word])
        if draw.textbbox((0, 0), test, font=font)[2] <= max_width:
            cur.append(word)
        else:
            if cur:
                lines.append(' '.join(cur))
            cur = [word]
    if cur:
        lines.append(' '.join(cur))
    return lines or [text]


def _text_h(draw, text, font):
    b = draw.textbbox((0, 0), text, font=font)
    return b[3] - b[1]


def _text_w(draw, text, font):
    b = draw.textbbox((0, 0), text, font=font)
    return b[2] - b[0]


def generate_product_card(product, output_dir):
    from django.conf import settings

    fonts  = _load_fonts(22)
    inner  = W - 2 * PAD

    # ── Measuring pass ────────────────────────────────────────────────────────
    _tmp  = Image.new('RGB', (W, 4000), C_WHITE)
    _draw = ImageDraw.Draw(_tmp)

    def measure():
        y = HEADER_H + PAD

        name_lines = _wrap(product.name, fonts['bold'], inner, _draw)[:3]
        y += len(name_lines) * 40 + 8
        y += 1 + 14  # divider + gap

        specs = []
        if product.materials:  specs.append(product.materials)
        if product.dimensions: specs.append(product.dimensions)
        if product.country:    specs.append(product.country)

        for val in specs:
            val_lines = _wrap(val, fonts['regular'], inner - LABEL_COL, _draw)
            y += max(30, len(val_lines) * 26 + 4)

        if specs:
            y += 8

        y += 1 + 12  # divider + gap

        discount = getattr(product, 'discount', 0) or 0
        if discount > 0:
            y += _text_h(_draw, '0', fonts['price_old']) + 10
            y += _text_h(_draw, '0', fonts['price']) + 8
        else:
            y += _text_h(_draw, '0', fonts['price']) + 8

        return y

    info_bottom = measure()

    qr_zone_y  = info_bottom + GAP_QR
    qr_size    = min(inner - 2 * QR_PAD, 240)
    qr_block_h = QR_PAD + qr_size + 10 + CAPTION_H + QR_PAD
    total_h    = qr_zone_y + qr_block_h

    # ── Real canvas ───────────────────────────────────────────────────────────
    card = Image.new('RGB', (W, total_h), C_WHITE)
    draw = ImageDraw.Draw(card)

    # ── HEADER ────────────────────────────────────────────────────────────────
    try:
        logo_path = os.path.join(settings.BASE_DIR, 'static', 'images', 'logo-navbar.png')
        if os.path.exists(logo_path):
            logo = Image.open(logo_path).convert('RGBA')
            lh = HEADER_H - 16
            lw = int(logo.width * lh / logo.height)
            logo = logo.resize((lw, lh), Image.Resampling.LANCZOS)
            card.paste(logo, ((W - lw) // 2, 8), logo)
    except Exception as e:
        print(f'[label] logo: {e}')
        draw.text((PAD, 22), 'Cascate Porte', fill=C_NAME, font=fonts['bold'])

    # ── INFO ZONE ─────────────────────────────────────────────────────────────
    y = HEADER_H + PAD

    name_lines = _wrap(product.name, fonts['bold'], inner, draw)[:3]
    for line in name_lines:
        draw.text((PAD, y), line, fill=C_NAME, font=fonts['bold'])
        y += 40
    y += 8

    draw.line([(PAD, y), (W - PAD, y)], fill=C_DIVIDER, width=1)
    y += 14

    specs = []
    if product.materials:  specs.append(('Материалы', product.materials))
    if product.dimensions: specs.append(('Размеры',   product.dimensions))
    if product.country:    specs.append(('Страна',    product.country))

    for lbl, val in specs:
        draw.text((PAD, y), lbl + ':', fill=C_LABEL, font=fonts['small'])
        val_lines = _wrap(val, fonts['regular'], inner - LABEL_COL, draw)
        row_h = 0
        for vl in val_lines:
            draw.text((PAD + LABEL_COL, y + row_h), vl, fill=C_VALUE, font=fonts['regular'])
            row_h += 26
        y += max(30, row_h + 4)

    if specs:
        y += 8

    draw.line([(PAD, y), (W - PAD, y)], fill=C_DIVIDER, width=1)
    y += 12

    # Price
    discount = getattr(product, 'discount', 0) or 0

    if discount > 0:
        old_text = f"{int(product.price):,} ₽".replace(',', '\u202f')
        oh = _text_h(draw, old_text, fonts['price_old'])
        ow = _text_w(draw, old_text, fonts['price_old'])
        draw.text((PAD, y), old_text, fill=C_PRICE_OLD, font=fonts['price_old'])
        draw.line([(PAD, y + oh // 2), (PAD + ow, y + oh // 2)], fill=C_PRICE_OLD, width=2)

        badge = f'-{discount}%'
        bw = _text_w(draw, badge, fonts['badge']) + 14
        bh = _text_h(draw, badge, fonts['badge']) + 8
        bx, by = PAD + ow + 12, y + (oh - bh) // 2
        draw.rounded_rectangle([(bx, by), (bx + bw, by + bh)], radius=5, fill=C_DISCOUNT_BG)
        draw.text((bx + 7, by + 4), badge, fill=C_DISCOUNT_FG, font=fonts['badge'])

        y += oh + 10

        discounted = int(product.price * (100 - discount) / 100)
        new_text = f"{discounted:,} ₽".replace(',', '\u202f')
        draw.text((PAD, y), new_text, fill=C_PRICE, font=fonts['price'])
        y += _text_h(draw, new_text, fonts['price']) + 8
    else:
        price_text = f"{int(product.price):,} ₽".replace(',', '\u202f')
        draw.text((PAD, y), price_text, fill=C_PRICE, font=fonts['price'])
        y += _text_h(draw, price_text, fonts['price']) + 8

    # ── QR ZONE ───────────────────────────────────────────────────────────────
    qr_zone_y = y + GAP_QR
    draw.rectangle([(0, qr_zone_y), (W, total_h)], fill=C_QR_BG)
    draw.line([(0, qr_zone_y), (W, qr_zone_y)], fill=C_DIVIDER, width=1)

    qr = qrcode_lib.QRCode(
        version=1,
        error_correction=qrcode_lib.constants.ERROR_CORRECT_M,
        box_size=8,
        border=2,
    )
    qr.add_data(f"https://cascateporte.ru{product.get_absolute_url()}")
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color='#1a1a1a', back_color='white').convert('RGB')
    qr_img = qr_img.resize((qr_size, qr_size), Image.Resampling.LANCZOS)

    qr_x = (W - qr_size) // 2
    qr_y = qr_zone_y + QR_PAD
    card.paste(qr_img, (qr_x, qr_y))
    draw.rectangle(
        [(qr_x - 2, qr_y - 2), (qr_x + qr_size + 2, qr_y + qr_size + 2)],
        outline=C_DIVIDER, width=1,
    )

    cap = 'Отсканируйте QR-код'
    cw = _text_w(draw, cap, fonts['caption'])
    draw.text(((W - cw) // 2, qr_y + qr_size + 10), cap, fill=C_QR_CAPTION, font=fonts['caption'])

    # ── SAVE ──────────────────────────────────────────────────────────────────
    filename = f'card_{product.slug}.png'
    filepath = os.path.join(output_dir, filename)
    card.save(filepath, 'PNG', optimize=True)
    return filepath
