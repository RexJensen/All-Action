#!/usr/bin/env python3
"""
Build Book One of ALL ACTION: A History of Gambling
Generates a professional PDF with cover, part dividers, chapters, and images.
"""

import os
import re
import textwrap
import PyPDF2
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch, cm
from reportlab.lib.colors import HexColor, black, white, Color
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY, TA_RIGHT
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, PageBreak, Image,
    Table, TableStyle, KeepTogether, Frame, PageTemplate,
    BaseDocTemplate, NextPageTemplate, Flowable
)
from reportlab.platypus.doctemplate import PageTemplate, BaseDocTemplate
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from PIL import Image as PILImage
from io import BytesIO

# ─── Configuration ───────────────────────────────────────────────
BASE_DIR = "/home/user/All-Action"
IMAGES_DIR = os.path.join(BASE_DIR, "images")
OUTPUT_PDF = os.path.join(BASE_DIR, "ALL_ACTION_Book_One.pdf")

PAGE_WIDTH, PAGE_HEIGHT = letter  # 8.5 x 11 inches
MARGIN_TOP = 1.0 * inch
MARGIN_BOTTOM = 0.9 * inch
MARGIN_LEFT = 1.1 * inch
MARGIN_RIGHT = 1.0 * inch
TEXT_WIDTH = PAGE_WIDTH - MARGIN_LEFT - MARGIN_RIGHT

# Colors
DARK_BROWN = HexColor("#2C1810")
GOLD = HexColor("#8B7355")
MEDIUM_BROWN = HexColor("#4A3728")
LIGHT_TAN = HexColor("#F5F0E8")
RULE_COLOR = HexColor("#8B7355")
DARK_RED = HexColor("#6B1C23")

# ─── Styles ──────────────────────────────────────────────────────
styles = getSampleStyleSheet()

body_style = ParagraphStyle(
    'BookBody',
    parent=styles['Normal'],
    fontName='Times-Roman',
    fontSize=10.5,
    leading=14.5,
    alignment=TA_JUSTIFY,
    spaceAfter=8,
    firstLineIndent=18,
    textColor=DARK_BROWN,
)

body_first_style = ParagraphStyle(
    'BookBodyFirst',
    parent=body_style,
    firstLineIndent=0,
)

chapter_title_style = ParagraphStyle(
    'ChapterTitle',
    fontName='Times-Bold',
    fontSize=24,
    leading=30,
    alignment=TA_LEFT,
    textColor=DARK_BROWN,
    spaceAfter=6,
)

chapter_subtitle_style = ParagraphStyle(
    'ChapterSubtitle',
    fontName='Times-Italic',
    fontSize=16,
    leading=22,
    alignment=TA_LEFT,
    textColor=MEDIUM_BROWN,
    spaceAfter=30,
)

chapter_num_style = ParagraphStyle(
    'ChapterNum',
    fontName='Times-Roman',
    fontSize=12,
    leading=16,
    alignment=TA_LEFT,
    textColor=GOLD,
    spaceAfter=8,
    spaceBefore=40,
)

section_break_style = ParagraphStyle(
    'SectionBreak',
    fontName='Times-Roman',
    fontSize=10,
    leading=14,
    alignment=TA_CENTER,
    spaceBefore=16,
    spaceAfter=16,
    textColor=GOLD,
)

sources_header_style = ParagraphStyle(
    'SourcesHeader',
    fontName='Times-Bold',
    fontSize=13,
    leading=18,
    alignment=TA_LEFT,
    textColor=DARK_BROWN,
    spaceBefore=24,
    spaceAfter=10,
)

sources_subheader_style = ParagraphStyle(
    'SourcesSubheader',
    fontName='Times-Bold',
    fontSize=10.5,
    leading=14,
    alignment=TA_LEFT,
    textColor=MEDIUM_BROWN,
    spaceBefore=12,
    spaceAfter=6,
)

source_item_style = ParagraphStyle(
    'SourceItem',
    fontName='Times-Roman',
    fontSize=9,
    leading=12.5,
    alignment=TA_LEFT,
    textColor=DARK_BROWN,
    leftIndent=18,
    firstLineIndent=-18,
    spaceAfter=4,
)

image_caption_style = ParagraphStyle(
    'ImageCaption',
    fontName='Times-Italic',
    fontSize=8.5,
    leading=11,
    alignment=TA_CENTER,
    textColor=MEDIUM_BROWN,
    spaceBefore=4,
    spaceAfter=16,
)

toc_style = ParagraphStyle(
    'TOCEntry',
    fontName='Times-Roman',
    fontSize=11,
    leading=20,
    alignment=TA_LEFT,
    textColor=DARK_BROWN,
    leftIndent=24,
)

toc_part_style = ParagraphStyle(
    'TOCPart',
    fontName='Times-Bold',
    fontSize=12,
    leading=24,
    alignment=TA_LEFT,
    textColor=DARK_BROWN,
    spaceBefore=14,
)

# ─── Custom Flowables ────────────────────────────────────────────

class HorizontalRule(Flowable):
    def __init__(self, width, thickness=0.5, color=RULE_COLOR):
        Flowable.__init__(self)
        self.width = width
        self.thickness = thickness
        self.color = color
        self.height = thickness + 8

    def draw(self):
        self.canv.setStrokeColor(self.color)
        self.canv.setLineWidth(self.thickness)
        self.canv.line(0, 4, self.width, 4)


class OrnamentalBreak(Flowable):
    """A decorative section break with centered ornament."""
    def __init__(self, width):
        Flowable.__init__(self)
        self.width = width
        self.height = 28

    def draw(self):
        self.canv.setStrokeColor(GOLD)
        self.canv.setFillColor(GOLD)
        cx = self.width / 2
        cy = 14
        # Three small diamonds
        for offset in [-20, 0, 20]:
            x = cx + offset
            self.canv.saveState()
            self.canv.translate(x, cy)
            self.canv.rotate(45)
            self.canv.rect(-2, -2, 4, 4, fill=1, stroke=0)
            self.canv.restoreState()
        # Lines on sides
        self.canv.setLineWidth(0.5)
        self.canv.line(cx - 60, cy, cx - 28, cy)
        self.canv.line(cx + 28, cy, cx + 60, cy)


# ─── Data: Book Structure ────────────────────────────────────────

BOOK_STRUCTURE = {
    "parts": [
        {
            "number": "I",
            "title": "BEFORE THE BET",
            "subtitle": "The origins and anthropology of gambling\nfrom prehistory through the medieval world",
            "chapters": [1, 2, 3, 4],
        },
        {
            "number": "II",
            "title": "THE CLASSICAL AND ANCIENT WORLD",
            "subtitle": "Gambling across civilizations\nfrom Greece to the Americas",
            "chapters": [5, 6, 7, 8, 9, 10, 11],
        },
        {
            "number": "III",
            "title": "THE MATHEMATICS OF CHANCE",
            "subtitle": "How probability theory was born from gambling\nand changed the world forever",
            "chapters": [12, 13, 14, 15, 16],
        },
    ]
}

CHAPTER_TITLES = {
    1: "The Gambling Animal",
    2: "Bones and Lots: The Archaeological Record",
    3: "Divination and Its Shadow",
    4: "Games of the First Civilizations",
    5: "Greece: Chance and Fate",
    6: "Rome: The Republic Bets",
    7: "India: Dice, Dharma, and the Mahabharata",
    8: "China: From Liubo to Mah-Jongg",
    9: "Japan: Gambling in the Floating World",
    10: "The Pre-Columbian Americas and the Pacific",
    11: "The Islamic World: Prohibition, Practice, and Paradox",
    12: "Thousands of Years Without Probability",
    13: "Cardano's Liber de Ludo Aleae",
    14: "The Problem of Points",
    15: "From Pascal to Bernoulli: Probability Takes Shape",
    16: "Expected Value, the House Edge, and the Long Run",
}

# Images per chapter (filenames in images dir)
CHAPTER_IMAGES = {}

def discover_images():
    """Find all images for each chapter."""
    if not os.path.exists(IMAGES_DIR):
        return
    for f in sorted(os.listdir(IMAGES_DIR)):
        if not f.lower().endswith(('.jpg', '.jpeg', '.png')):
            continue
        m = re.match(r'ch(\d+)_', f)
        if m:
            ch = int(m.group(1))
            if ch not in CHAPTER_IMAGES:
                CHAPTER_IMAGES[ch] = []
            CHAPTER_IMAGES[ch].append(f)

# ─── Text Extraction ─────────────────────────────────────────────

def extract_chapters_from_markdown(md_path):
    """Extract chapter text from the combined markdown file."""
    with open(md_path, 'r', encoding='utf-8') as f:
        content = f.read()

    chapters = {}
    # Split on chapter headings
    parts = re.split(r'\n# Chapter (\d+)\n', content)
    # parts[0] is before first chapter, then alternating: number, text
    for i in range(1, len(parts) - 1, 2):
        ch_num = int(parts[i])
        ch_text = parts[i + 1].strip()
        # Remove the subtitle line (## Title)
        ch_text = re.sub(r'^## .+\n', '', ch_text, count=1).strip()
        chapters[ch_num] = ch_text

    # Cut off references section from chapter 10
    if 10 in chapters:
        ref_idx = chapters[10].find('\n# References\n')
        if ref_idx > 0:
            chapters[10] = chapters[10][:ref_idx].strip()
        # Also check for "---" followed by references
        ref_idx = chapters[10].find('\n---\n\n# References')
        if ref_idx > 0:
            chapters[10] = chapters[10][:ref_idx].strip()

    return chapters


def extract_chapter_from_pdf(pdf_path):
    """Extract text from a chapter PDF using PyPDF2."""
    text_parts = []
    with open(pdf_path, 'rb') as f:
        reader = PyPDF2.PdfReader(f)
        for page in reader.pages:
            t = page.extract_text()
            if t:
                text_parts.append(t)
    full_text = '\n'.join(text_parts)
    # Remove the "CHAPTER N" and title lines at the start
    full_text = re.sub(r'^CHAPTER \d+\s*\n', '', full_text, count=1)
    # Remove the subtitle
    lines = full_text.split('\n')
    if lines and lines[0].strip():
        # First non-empty line is likely the title - remove it
        full_text = '\n'.join(lines[1:]).strip()
    return full_text


def parse_chapter_text(raw_text):
    """Parse chapter text into structured elements (paragraphs, section breaks, sources)."""
    elements = []
    # Split into sections by horizontal rules (--- or multiple blank lines)
    # In PDF-extracted text, sections are separated by multiple blank lines

    # Normalize line endings
    text = raw_text.replace('\r\n', '\n')

    # Split into paragraphs
    paragraphs = re.split(r'\n\s*\n', text)

    in_sources = False

    for para in paragraphs:
        para = para.strip()
        if not para:
            continue

        # Check for horizontal rule markers
        if para == '---' or para == '***' or re.match(r'^[-*_]{3,}$', para):
            elements.append(('break', None))
            continue

        # Check for Sources section
        if para.startswith('Sources and Further Reading') or para.startswith('**Sources and Further Reading**'):
            in_sources = True
            elements.append(('sources_header', 'Sources and Further Reading'))
            continue

        if in_sources:
            # Check if it's a sub-header (bold text or short line)
            clean = para.replace('**', '').replace('*', '')
            if len(clean) < 80 and not clean.startswith('•') and not clean.startswith('-') and not clean.startswith('On ') and not clean.startswith('Wikipedia'):
                # Likely a sub-header
                if any(c.isalpha() for c in clean):
                    elements.append(('sources_subheader', clean))
                    continue
            elements.append(('source_item', clean))
            continue

        # Regular paragraph - clean up markdown
        clean = para.replace('\n', ' ')
        clean = re.sub(r'\s+', ' ', clean)
        # Handle markdown bold/italic
        clean = clean.replace('**', '')  # Remove bold markers
        # Keep content, remove markdown artifacts
        clean = re.sub(r'^#{1,6}\s+', '', clean)  # Remove heading markers

        if clean.strip():
            elements.append(('paragraph', clean.strip()))

    return elements


# ─── PDF Page Templates ──────────────────────────────────────────

def page_header_footer(canvas_obj, doc):
    """Add headers and footers to regular pages."""
    canvas_obj.saveState()
    page_num = doc.page

    # Page number at bottom center
    canvas_obj.setFont('Times-Roman', 9)
    canvas_obj.setFillColor(GOLD)
    canvas_obj.drawCentredString(PAGE_WIDTH / 2, MARGIN_BOTTOM - 20, str(page_num))

    # Thin rule at top
    if page_num > 6:  # Skip front matter
        canvas_obj.setStrokeColor(RULE_COLOR)
        canvas_obj.setLineWidth(0.3)
        canvas_obj.line(MARGIN_LEFT, PAGE_HEIGHT - MARGIN_TOP + 12,
                       PAGE_WIDTH - MARGIN_RIGHT, PAGE_HEIGHT - MARGIN_TOP + 12)

    canvas_obj.restoreState()


def chapter_first_page(canvas_obj, doc):
    """First page of chapter - no header, just page number."""
    canvas_obj.saveState()
    page_num = doc.page
    canvas_obj.setFont('Times-Roman', 9)
    canvas_obj.setFillColor(GOLD)
    canvas_obj.drawCentredString(PAGE_WIDTH / 2, MARGIN_BOTTOM - 20, str(page_num))
    canvas_obj.restoreState()


def blank_page(canvas_obj, doc):
    """Completely blank page."""
    pass


# ─── Build PDF ───────────────────────────────────────────────────

def add_cover_page(story):
    """Create the front cover."""
    story.append(Spacer(1, 0.5 * inch))

    # Cover image
    cover_img_path = os.path.join(IMAGES_DIR, "ch16_The_Card_Players.jpg")
    if os.path.exists(cover_img_path):
        try:
            img = PILImage.open(cover_img_path)
            iw, ih = img.size
            aspect = ih / iw
            display_width = TEXT_WIDTH * 0.85
            display_height = display_width * aspect
            if display_height > 4.5 * inch:
                display_height = 4.5 * inch
                display_width = display_height / aspect

            story.append(Spacer(1, 0.3 * inch))
            cover_image = Image(cover_img_path, width=display_width, height=display_height)
            cover_image.hAlign = 'CENTER'
            story.append(cover_image)
            story.append(Spacer(1, 0.4 * inch))
        except Exception as e:
            print(f"Cover image error: {e}")
            story.append(Spacer(1, 2 * inch))
    else:
        story.append(Spacer(1, 2.5 * inch))

    # Title
    title_style = ParagraphStyle(
        'CoverTitle',
        fontName='Times-Bold',
        fontSize=36,
        leading=42,
        alignment=TA_CENTER,
        textColor=DARK_BROWN,
    )
    story.append(Paragraph("ALL ACTION", title_style))
    story.append(Spacer(1, 8))

    # Subtitle
    sub_style = ParagraphStyle(
        'CoverSub',
        fontName='Times-Italic',
        fontSize=16,
        leading=22,
        alignment=TA_CENTER,
        textColor=MEDIUM_BROWN,
    )
    story.append(Paragraph("A Complete History of Gambling", sub_style))
    story.append(Spacer(1, 24))

    # Rule
    story.append(HorizontalRule(TEXT_WIDTH * 0.4, thickness=1, color=GOLD))
    story.append(Spacer(1, 16))

    # Book number
    book_style = ParagraphStyle(
        'CoverBook',
        fontName='Times-Roman',
        fontSize=14,
        leading=20,
        alignment=TA_CENTER,
        textColor=GOLD,
    )
    story.append(Paragraph("BOOK ONE: FOUNDATIONS", book_style))

    story.append(PageBreak())


def add_half_title(story):
    """Half-title page."""
    story.append(Spacer(1, 3 * inch))
    ht_style = ParagraphStyle(
        'HalfTitle',
        fontName='Times-Bold',
        fontSize=24,
        leading=30,
        alignment=TA_CENTER,
        textColor=DARK_BROWN,
    )
    story.append(Paragraph("ALL ACTION", ht_style))
    story.append(PageBreak())


def add_title_page(story):
    """Full title page."""
    story.append(Spacer(1, 1.8 * inch))

    t1 = ParagraphStyle('T1', fontName='Times-Bold', fontSize=32, leading=40,
                        alignment=TA_CENTER, textColor=DARK_BROWN)
    story.append(Paragraph("ALL ACTION", t1))
    story.append(Spacer(1, 12))

    t2 = ParagraphStyle('T2', fontName='Times-Italic', fontSize=15, leading=20,
                        alignment=TA_CENTER, textColor=MEDIUM_BROWN)
    story.append(Paragraph("A Complete History and Encyclopedia of Gambling", t2))
    story.append(Spacer(1, 6))
    story.append(Paragraph("In Five Books", t2))

    story.append(Spacer(1, 40))
    story.append(HorizontalRule(TEXT_WIDTH * 0.3, thickness=0.8, color=GOLD))
    story.append(Spacer(1, 40))

    t3 = ParagraphStyle('T3', fontName='Times-Bold', fontSize=16, leading=22,
                        alignment=TA_CENTER, textColor=DARK_BROWN)
    story.append(Paragraph("BOOK ONE", t3))
    story.append(Spacer(1, 8))

    t4 = ParagraphStyle('T4', fontName='Times-Roman', fontSize=14, leading=20,
                        alignment=TA_CENTER, textColor=MEDIUM_BROWN)
    story.append(Paragraph("FOUNDATIONS", t4))
    story.append(Spacer(1, 10))

    t5 = ParagraphStyle('T5', fontName='Times-Italic', fontSize=11, leading=16,
                        alignment=TA_CENTER, textColor=GOLD)
    story.append(Paragraph(
        "The origins, anthropology, and mathematics<br/>"
        "of gambling from prehistory through the Enlightenment",
        t5
    ))

    story.append(PageBreak())


def add_copyright_page(story):
    """Copyright/colophon page."""
    story.append(Spacer(1, 5 * inch))

    cp = ParagraphStyle('Copyright', fontName='Times-Roman', fontSize=8.5,
                        leading=12, alignment=TA_CENTER, textColor=MEDIUM_BROWN)

    story.append(Paragraph("ALL ACTION: A Complete History and Encyclopedia of Gambling", cp))
    story.append(Spacer(1, 6))
    story.append(Paragraph("Book One: Foundations", cp))
    story.append(Spacer(1, 16))
    story.append(Paragraph(
        "Images courtesy of The Metropolitan Museum of Art, Open Access Collection.<br/>"
        "Used under Creative Commons Zero (CC0) public domain dedication.",
        cp
    ))
    story.append(Spacer(1, 16))
    story.append(Paragraph(
        "Set in Times New Roman. Composed and typeset digitally.",
        cp
    ))

    story.append(PageBreak())


def add_table_of_contents(story):
    """Table of contents."""
    story.append(Spacer(1, 0.8 * inch))

    toc_title = ParagraphStyle('TOCTitle', fontName='Times-Bold', fontSize=20,
                               leading=26, alignment=TA_CENTER, textColor=DARK_BROWN,
                               spaceAfter=30)
    story.append(Paragraph("CONTENTS", toc_title))
    story.append(Spacer(1, 10))
    story.append(HorizontalRule(TEXT_WIDTH * 0.3, thickness=0.5, color=GOLD))
    story.append(Spacer(1, 20))

    for part in BOOK_STRUCTURE["parts"]:
        story.append(Paragraph(
            f"PART {part['number']}: {part['title']}",
            toc_part_style
        ))
        for ch_num in part["chapters"]:
            title = CHAPTER_TITLES[ch_num]
            story.append(Paragraph(
                f"Chapter {ch_num}  &mdash;  {title}",
                toc_style
            ))

    story.append(PageBreak())


def add_part_divider(story, part_data):
    """Create a part divider page."""
    story.append(Spacer(1, 2.5 * inch))

    part_num_style = ParagraphStyle(
        'PartNum',
        fontName='Times-Roman',
        fontSize=14,
        leading=18,
        alignment=TA_CENTER,
        textColor=GOLD,
    )
    story.append(Paragraph(f"PART {part_data['number']}", part_num_style))
    story.append(Spacer(1, 16))

    story.append(HorizontalRule(TEXT_WIDTH * 0.25, thickness=0.8, color=GOLD))
    story.append(Spacer(1, 20))

    part_title_style = ParagraphStyle(
        'PartTitle',
        fontName='Times-Bold',
        fontSize=26,
        leading=34,
        alignment=TA_CENTER,
        textColor=DARK_BROWN,
    )
    story.append(Paragraph(part_data['title'], part_title_style))
    story.append(Spacer(1, 20))

    part_sub_style = ParagraphStyle(
        'PartSub',
        fontName='Times-Italic',
        fontSize=12,
        leading=18,
        alignment=TA_CENTER,
        textColor=MEDIUM_BROWN,
    )
    for line in part_data['subtitle'].split('\n'):
        story.append(Paragraph(line, part_sub_style))

    story.append(Spacer(1, 30))
    story.append(OrnamentalBreak(TEXT_WIDTH))

    story.append(PageBreak())


def add_chapter_image(story, img_filename, caption=None):
    """Add an image with optional caption."""
    img_path = os.path.join(IMAGES_DIR, img_filename)
    if not os.path.exists(img_path):
        return

    try:
        img = PILImage.open(img_path)
        iw, ih = img.size
        aspect = ih / iw

        max_width = TEXT_WIDTH * 0.75
        max_height = 3.2 * inch

        display_width = max_width
        display_height = display_width * aspect

        if display_height > max_height:
            display_height = max_height
            display_width = display_height / aspect

        image_obj = Image(img_path, width=display_width, height=display_height)
        image_obj.hAlign = 'CENTER'

        elements = [
            Spacer(1, 8),
            image_obj,
        ]

        if caption:
            elements.append(Paragraph(caption, image_caption_style))
        else:
            # Generate caption from filename
            name = img_filename.replace('.jpg', '').replace('.jpeg', '').replace('.png', '')
            name = re.sub(r'^ch\d+_', '', name)
            name = name.replace('_', ' ')
            elements.append(Paragraph(name, image_caption_style))

        elements.append(Spacer(1, 4))
        story.append(KeepTogether(elements))
    except Exception as e:
        print(f"Image error for {img_filename}: {e}")


def add_chapter(story, ch_num, chapter_text, is_first_in_part=False):
    """Add a complete chapter to the story."""
    title = CHAPTER_TITLES[ch_num]

    # Chapter opening
    story.append(Spacer(1, 0.6 * inch))
    story.append(Paragraph(f"CHAPTER {ch_num}", chapter_num_style))
    story.append(Paragraph(title, chapter_title_style))
    story.append(HorizontalRule(TEXT_WIDTH * 0.2, thickness=0.5, color=GOLD))
    story.append(Spacer(1, 16))

    # Get images for this chapter
    ch_images = CHAPTER_IMAGES.get(ch_num, [])
    images_placed = 0

    # Place first image near the start if available
    if ch_images:
        add_chapter_image(story, ch_images[0])
        images_placed = 1

    # Parse and add text
    elements = parse_chapter_text(chapter_text)

    para_count = 0
    first_para = True

    # Calculate where to insert remaining images
    total_paras = sum(1 for e in elements if e[0] == 'paragraph')
    image_interval = max(1, total_paras // (len(ch_images) - images_placed + 1)) if len(ch_images) > images_placed else 999
    next_image_at = image_interval

    for elem_type, elem_text in elements:
        if elem_type == 'paragraph':
            para_count += 1

            # Escape special characters for ReportLab
            safe_text = elem_text
            safe_text = safe_text.replace('&', '&amp;')
            safe_text = safe_text.replace('<', '&lt;')
            safe_text = safe_text.replace('>', '&gt;')
            # Restore italic markers (simple approach)

            if first_para:
                story.append(Paragraph(safe_text, body_first_style))
                first_para = False
            else:
                story.append(Paragraph(safe_text, body_style))

            # Insert images at intervals
            if para_count >= next_image_at and images_placed < len(ch_images):
                add_chapter_image(story, ch_images[images_placed])
                images_placed += 1
                next_image_at = para_count + image_interval

        elif elem_type == 'break':
            story.append(OrnamentalBreak(TEXT_WIDTH))
            first_para = True

        elif elem_type == 'sources_header':
            story.append(Spacer(1, 12))
            story.append(HorizontalRule(TEXT_WIDTH * 0.2, thickness=0.5, color=GOLD))
            story.append(Paragraph("Sources and Further Reading", sources_header_style))

        elif elem_type == 'sources_subheader':
            safe_text = elem_text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            story.append(Paragraph(safe_text, sources_subheader_style))

        elif elem_type == 'source_item':
            safe_text = elem_text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            # Handle bullet points
            if safe_text.startswith('• ') or safe_text.startswith('- '):
                safe_text = '&bull; ' + safe_text[2:]
            story.append(Paragraph(safe_text, source_item_style))

    # Place any remaining images at the end
    while images_placed < len(ch_images):
        add_chapter_image(story, ch_images[images_placed])
        images_placed += 1

    story.append(PageBreak())


def add_end_page(story):
    """Add a final page."""
    story.append(Spacer(1, 3 * inch))

    end_style = ParagraphStyle(
        'EndStyle',
        fontName='Times-Italic',
        fontSize=12,
        leading=18,
        alignment=TA_CENTER,
        textColor=MEDIUM_BROWN,
    )
    story.append(OrnamentalBreak(TEXT_WIDTH))
    story.append(Spacer(1, 20))
    story.append(Paragraph("End of Book One", end_style))
    story.append(Spacer(1, 16))
    story.append(Paragraph(
        "The story continues in Book Two: The Games",
        ParagraphStyle('EndSub', fontName='Times-Italic', fontSize=10,
                      leading=14, alignment=TA_CENTER, textColor=GOLD)
    ))
    story.append(Spacer(1, 30))
    story.append(OrnamentalBreak(TEXT_WIDTH))


def build_book():
    """Main function to build the complete book PDF."""
    print("Discovering images...")
    discover_images()
    print(f"Found images for chapters: {sorted(CHAPTER_IMAGES.keys())}")
    for ch, imgs in sorted(CHAPTER_IMAGES.items()):
        print(f"  Ch {ch}: {len(imgs)} images")

    print("\nExtracting chapter text from markdown...")
    md_chapters = extract_chapters_from_markdown(os.path.join(BASE_DIR, "ALL_ACTION_Book.md"))
    print(f"Extracted {len(md_chapters)} chapters from markdown: {sorted(md_chapters.keys())}")

    print("\nExtracting chapters 11-16 from PDFs...")
    pdf_chapters = {}
    for ch_num in range(11, 17):
        pdf_path = os.path.join(BASE_DIR, f"chapter{ch_num}.pdf")
        if os.path.exists(pdf_path):
            pdf_chapters[ch_num] = extract_chapter_from_pdf(pdf_path)
            print(f"  Ch {ch_num}: {len(pdf_chapters[ch_num])} chars")

    # Merge all chapters
    all_chapters = {}
    all_chapters.update(md_chapters)
    all_chapters.update(pdf_chapters)

    print(f"\nTotal chapters available: {sorted(all_chapters.keys())}")

    # Build the story
    story = []

    print("\nBuilding book structure...")

    # Front matter
    add_cover_page(story)
    add_half_title(story)
    add_title_page(story)
    add_copyright_page(story)
    add_table_of_contents(story)

    # Blank page before Part I
    story.append(PageBreak())

    # Parts and chapters
    for part in BOOK_STRUCTURE["parts"]:
        add_part_divider(story, part)

        for i, ch_num in enumerate(part["chapters"]):
            if ch_num in all_chapters:
                print(f"  Adding Chapter {ch_num}: {CHAPTER_TITLES[ch_num]}")
                add_chapter(story, ch_num, all_chapters[ch_num], is_first_in_part=(i == 0))
            else:
                print(f"  WARNING: Chapter {ch_num} text not found!")

    # End page
    add_end_page(story)

    # Build the PDF
    print(f"\nGenerating PDF: {OUTPUT_PDF}")

    doc = BaseDocTemplate(
        OUTPUT_PDF,
        pagesize=letter,
        leftMargin=MARGIN_LEFT,
        rightMargin=MARGIN_RIGHT,
        topMargin=MARGIN_TOP,
        bottomMargin=MARGIN_BOTTOM,
        title="ALL ACTION: Book One - Foundations",
        author="All Action",
        subject="A Complete History of Gambling",
    )

    # Create page templates
    frame = Frame(
        MARGIN_LEFT, MARGIN_BOTTOM,
        TEXT_WIDTH, PAGE_HEIGHT - MARGIN_TOP - MARGIN_BOTTOM,
        id='normal'
    )

    doc.addPageTemplates([
        PageTemplate(id='normal', frames=frame, onPage=page_header_footer),
        PageTemplate(id='chapter_first', frames=frame, onPage=chapter_first_page),
        PageTemplate(id='blank', frames=frame, onPage=blank_page),
    ])

    doc.build(story)

    # Get file size
    size_mb = os.path.getsize(OUTPUT_PDF) / (1024 * 1024)
    print(f"\nBook generated successfully!")
    print(f"Output: {OUTPUT_PDF}")
    print(f"Size: {size_mb:.1f} MB")


if __name__ == '__main__':
    build_book()
