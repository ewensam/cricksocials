"""Pillow-based image compositor (Phase 6).

Renders a square (1080x1080) Instagram-ready post: a match photo with a
semi-transparent brand-colour overlay, the club logo, and the result/score
line plus standout performer highlights.
"""

from __future__ import annotations

from datetime import date
from io import BytesIO
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from cricksocials.config import Config
from cricksocials.parser import BattingPerformance, BowlingPerformance, InningsData, MatchResult
from cricksocials.stats import (
    find_our_innings,
    format_batting,
    format_bowling,
    format_score_line,
    select_batting_highlight,
    select_bowling_highlight,
)

CANVAS_SIZE = (1080, 1080)
LOGO_WIDTH = 140
MARGIN = 50
HEADLINE_FONT_SIZE = 56
DETAIL_FONT_SIZE = 36
LINE_SPACING = 46


def compose_post_image(match: MatchResult, photo_bytes: bytes, config: Config) -> bytes:
    """Render a post image for *match* using *photo_bytes* as the background."""
    canvas = _build_background(photo_bytes, config)
    draw = ImageDraw.Draw(canvas)

    our_innings = find_our_innings(match.innings, match.home_club)
    score_line = format_score_line(match, match.home_club, config.club.short_name)
    detail_lines = [score_line, *_highlight_lines(our_innings, config)]

    _draw_text_block(draw, config, detail_lines)
    _paste_logo(canvas, config)

    return _to_png_bytes(canvas)


def compose_preview_image(config: Config) -> bytes:
    """Render a sample post image with dummy match data, for `cricksocials preview`."""
    return compose_post_image(_dummy_match(config), _dummy_photo_bytes(config), config)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _highlight_lines(our_innings: InningsData | None, config: Config) -> list[str]:
    if our_innings is None:
        return []
    lines = []
    batting = select_batting_highlight(our_innings.batting, config.stats)
    if batting:
        lines.append(format_batting(batting))
    bowling = select_bowling_highlight(our_innings.bowling, config.stats)
    if bowling:
        lines.append(format_bowling(bowling))
    return lines


def _build_background(photo_bytes: bytes, config: Config) -> Image.Image:
    photo = Image.open(BytesIO(photo_bytes)).convert("RGB")
    photo = _crop_to_cover(photo, CANVAS_SIZE)

    overlay_colour = _hex_to_rgb(config.branding.colours.primary)
    alpha = round(config.branding.overlay_opacity * 255)
    overlay = Image.new("RGBA", CANVAS_SIZE, (*overlay_colour, alpha))

    canvas = Image.alpha_composite(photo.convert("RGBA"), overlay)
    return canvas.convert("RGB")


def _crop_to_cover(image: Image.Image, size: tuple[int, int]) -> Image.Image:
    """Resize+crop *image* to fill *size* exactly, preserving aspect ratio (cover fit)."""
    target_w, target_h = size
    src_w, src_h = image.size
    scale = max(target_w / src_w, target_h / src_h)
    new_w, new_h = round(src_w * scale), round(src_h * scale)
    image = image.resize((new_w, new_h), Image.Resampling.LANCZOS)
    left = (new_w - target_w) // 2
    top = (new_h - target_h) // 2
    return image.crop((left, top, left + target_w, top + target_h))


def _paste_logo(canvas: Image.Image, config: Config) -> None:
    logo_path = Path(config.branding.logo_path)
    if not logo_path.is_file():
        return
    logo = Image.open(logo_path).convert("RGBA")
    ratio = LOGO_WIDTH / logo.width
    logo = logo.resize((LOGO_WIDTH, round(logo.height * ratio)), Image.Resampling.LANCZOS)
    canvas.paste(logo, (MARGIN, MARGIN), logo)


def _draw_text_block(
    draw: ImageDraw.ImageDraw,
    config: Config,
    lines: list[str],
) -> None:
    text_colour = _hex_to_rgb(config.branding.colours.text)
    max_width = CANVAS_SIZE[0] - 2 * MARGIN

    block_height = HEADLINE_FONT_SIZE + max(len(lines) - 1, 0) * LINE_SPACING
    y = CANVAS_SIZE[1] - MARGIN - block_height

    for index, line in enumerate(lines):
        font_path = config.branding.fonts.bold if index == 0 else config.branding.fonts.regular
        size = HEADLINE_FONT_SIZE if index == 0 else DETAIL_FONT_SIZE
        font = _fit_font(draw, str(font_path), line, size, max_width)
        draw.text((MARGIN, y), line, font=font, fill=text_colour)
        y += LINE_SPACING


def _fit_font(
    draw: ImageDraw.ImageDraw,
    font_path: str,
    text: str,
    start_size: int,
    max_width: int,
) -> ImageFont.FreeTypeFont:
    """Shrink the font size until *text* fits within *max_width*."""
    size = start_size
    font = ImageFont.truetype(font_path, size)
    while size > 16 and draw.textlength(text, font=font) > max_width:
        size -= 2
        font = ImageFont.truetype(font_path, size)
    return font


def _hex_to_rgb(hex_colour: str) -> tuple[int, int, int]:
    h = hex_colour.lstrip("#")
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))


def _to_png_bytes(image: Image.Image) -> bytes:
    buf = BytesIO()
    image.save(buf, format="PNG")
    return buf.getvalue()


def _dummy_match(config: Config) -> MatchResult:
    our_team = config.club.name
    return MatchResult(
        match_id="0",
        date=date.today(),
        home_club=our_team,
        ground="Preview Ground",
        result_text="WON BY 42 RUNS",
        result_for_home_club="win",
        innings=[
            InningsData(
                team_name=our_team,
                total_runs=187,
                wickets_down=6,
                overs="40.0",
                all_out=False,
                extras=12,
                batting=[
                    BattingPerformance(
                        name="Sam Preview",
                        runs=67,
                        balls=58,
                        fours=8,
                        sixes=2,
                        not_out=True,
                        how_out="",
                    ),
                ],
                bowling=[
                    BowlingPerformance(
                        name="Alex Sample",
                        overs="8",
                        maidens=1,
                        runs=24,
                        wickets=3,
                        wides=0,
                        no_balls=0,
                    ),
                ],
            ),
            InningsData(
                team_name="Preview Opposition CC",
                total_runs=145,
                wickets_down=10,
                overs="38.2",
                all_out=True,
                extras=9,
                batting=[],
                bowling=[],
            ),
        ],
    )


def _dummy_photo_bytes(config: Config) -> bytes:
    from cricksocials.adapters.photo_source import LocalFolderPhotoSource, pick_random_photo

    source = LocalFolderPhotoSource(config.photos.local)
    ref = pick_random_photo(source, "win")
    if ref:
        return source.fetch_photo(ref)

    blank = Image.new("RGB", CANVAS_SIZE, _hex_to_rgb(config.branding.colours.primary))
    return _to_png_bytes(blank)
