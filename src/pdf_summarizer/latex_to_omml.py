"""Convert LaTeX math expressions to OMML for real equations in Word documents."""

import logging
import re
import xml.etree.ElementTree as ET
from typing import List

from docx.oxml import OxmlElement
from docx.oxml.ns import qn

logger = logging.getLogger(__name__)

_MATHML_NS = 'http://www.w3.org/1998/Math/MathML'

# Characters that are not allowed in XML text nodes
_CONTROL_CHAR_RE = re.compile(r'[\x00-\x08\x0b\x0c\x0e-\x1f]')


def _sanitize_xml_text(text: str) -> str:
    """Remove control characters that are not valid in XML."""
    return _CONTROL_CHAR_RE.sub('', text)


def _preprocess_latex(latex: str) -> str:
    """Pre-process LaTeX to fix common issues before passing to latex2mathml."""
    # Replace \left[ and \right] with \left[ and \right] (no change needed)
    # But handle cases where \left and \right are used with brackets that
    # latex2mathml might misinterpret
    latex = latex.replace('\\left[', '\\left[')
    latex = latex.replace('\\right]', '\\right]')
    return latex


def latex_to_omml(latex: str) -> OxmlElement:
    """Convert LaTeX math to an ``m:oMath`` element (inline equation).

    Falls back to a plain text run if conversion fails.
    """
    from latex2mathml.converter import convert as latex2mathml_convert

    try:
        cleaned = _preprocess_latex(latex)
        mathml = latex2mathml_convert(cleaned)
        root = ET.fromstring(mathml)
        omath = OxmlElement('m:oMath')
        _convert_children(root, omath)
        return omath
    except Exception as exc:
        logger.warning("LaTeX→OMML conversion failed: %s — %s", exc, latex)
        return _fallback_omath(latex)


def latex_to_omath_para(latex: str) -> OxmlElement:
    """Convert LaTeX to an ``m:oMathPara`` element (display equation)."""
    omath_para = OxmlElement('m:oMathPara')
    omath_para.append(latex_to_omml(latex))
    return omath_para


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _local_tag(el: ET.Element) -> str:
    t = el.tag
    return t.split('}', 1)[1] if '}' in t else t


def _convert_children(source: ET.Element, parent: OxmlElement):
    for child in source:
        for elem in _convert_element(child):
            parent.append(elem)


def _convert_element(element: ET.Element) -> List[OxmlElement]:
    tag = _local_tag(element)

    # --- containers that just pass through children ------------------------
    if tag in ('mrow', 'mstyle', 'merror', 'mpadded', 'mphantom', 'math',
               'menclose', 'semantics', 'annotation', 'annotation-xml'):
        out: List[OxmlElement] = []
        for ch in element:
            out.extend(_convert_element(ch))
        return out

    # --- text runs: identifiers, numbers, operators, text ------------------
    if tag in ('mi', 'mn', 'mo', 'mtext', 'ms'):
        text = _itertext_strip(element)
        if not text:
            return []
        r = OxmlElement('m:r')
        t = OxmlElement('m:t')
        t.text = text
        r.append(t)
        return [r]

    # --- fraction ----------------------------------------------------------
    if tag == 'mfrac':
        ch = list(element)
        f = OxmlElement('m:f')
        num = OxmlElement('m:num')
        den = OxmlElement('m:den')
        if ch:
            _fill_container(num, ch[0])
        if len(ch) >= 2:
            _fill_container(den, ch[1])
        f.append(num)
        f.append(den)
        return [f]

    # --- superscript -------------------------------------------------------
    if tag == 'msup':
        ch = list(element)
        ssup = OxmlElement('m:sSup')
        e = OxmlElement('m:e')
        lim = OxmlElement('m:lim')
        if ch:
            _fill_container(e, ch[0])
        if len(ch) >= 2:
            _fill_container(lim, ch[1])
        ssup.append(e)
        ssup.append(lim)
        return [ssup]

    # --- subscript ---------------------------------------------------------
    if tag == 'msub':
        ch = list(element)
        ssub = OxmlElement('m:sSub')
        e = OxmlElement('m:e')
        lim = OxmlElement('m:lim')
        if ch:
            _fill_container(e, ch[0])
        if len(ch) >= 2:
            _fill_container(lim, ch[1])
        ssub.append(e)
        ssub.append(lim)
        return [ssub]

    # --- subscript + superscript -------------------------------------------
    if tag == 'msubsup':
        ch = list(element)
        ssubsup = OxmlElement('m:sSubSup')
        e = OxmlElement('m:e')
        sub_el = OxmlElement('m:sub')
        sup_el = OxmlElement('m:sup')
        if ch:
            _fill_container(e, ch[0])
        if len(ch) >= 2:
            _fill_container(sub_el, ch[1])
        if len(ch) >= 3:
            _fill_container(sup_el, ch[2])
        ssubsup.append(e)
        ssubsup.append(sub_el)
        ssubsup.append(sup_el)
        return [ssubsup]

    # --- square root -------------------------------------------------------
    if tag == 'msqrt':
        rad = OxmlElement('m:rad')
        e = OxmlElement('m:e')
        for ch in element:
            _fill_container(e, ch)
        rad.append(e)
        return [rad]

    # --- root (n-th root) --------------------------------------------------
    if tag == 'mroot':
        ch = list(element)
        rad = OxmlElement('m:rad')
        deg = OxmlElement('m:deg')
        e = OxmlElement('m:e')
        if ch:
            _fill_container(e, ch[0])
        if len(ch) >= 2:
            _fill_container(deg, ch[1])
        rad.append(deg)
        rad.append(e)
        return [rad]

    # --- overscript (e.g. vector arrow, hat) -------------------------------
    if tag == 'mover':
        ch = list(element)
        if len(ch) >= 2:
            accent_ch = next(iter(ch[1]), ch[1])
            accent_tag = _local_tag(accent_ch) if isinstance(accent_ch, ET.Element) else ''
            # Single character accent → m:acc
            if accent_tag in ('mo', 'mi') and len(accent_ch.text or '') <= 2:
                acc = OxmlElement('m:acc')
                acc_pr = OxmlElement('m:accPr')
                chr_el = OxmlElement('m:chr')
                chr_el.set(qn('w:val'), accent_ch.text or '')
                acc_pr.append(chr_el)
                acc.append(acc_pr)
                e = OxmlElement('m:e')
                _fill_container(e, ch[0])
                acc.append(e)
                return [acc]
        # fallback: treat as bar
        bar = OxmlElement('m:bar')
        bar_pr = OxmlElement('m:barPr')
        pos = OxmlElement('m:pos')
        pos.set(qn('w:val'), 'top')
        bar_pr.append(pos)
        bar.append(bar_pr)
        e = OxmlElement('m:e')
        _fill_container(e, ch[0])
        bar.append(e)
        return [bar]

    # --- underscript -------------------------------------------------------
    if tag == 'munder':
        ch = list(element)
        limlow = OxmlElement('m:limLow')
        e = OxmlElement('m:e')
        lim = OxmlElement('m:lim')
        if ch:
            _fill_container(e, ch[0])
        if len(ch) >= 2:
            _fill_container(lim, ch[1])
        limlow.append(e)
        limlow.append(lim)
        return [limlow]

    # --- underscript + overscript ------------------------------------------
    if tag == 'munderover':
        ch = list(element)
        limupp = OxmlElement('m:limUpp')
        e = OxmlElement('m:e')
        lim = OxmlElement('m:lim')
        if ch:
            _fill_container(e, ch[0])
        if len(ch) >= 3:
            # middle child → underscript, last child → overscript
            sub_el = OxmlElement('m:sub')
            sup_el = OxmlElement('m:sup')
            _fill_container(sub_el, ch[1])
            _fill_container(sup_el, ch[2])
            e.append(sub_el)
            e.append(sup_el)
        limupp.append(e)
        limupp.append(lim)
        return [limupp]

    # --- n-ary (sum / int / prod) ------------------------------------------
    if tag == 'munderover' and _is_nary(element):
        return _build_nary(element)

    # --- spacing -----------------------------------------------------------
    if tag in ('mspace',):
        return []

    # --- fallback: process children recursively ----------------------------
    out: List[OxmlElement] = []
    for ch in element:
        out.extend(_convert_element(ch))
    return out


def _fill_container(container: OxmlElement, mathml_node):
    """Fill an OMML container element (e, num, den, lim, …) with converted
    children from a MathML node."""
    if isinstance(mathml_node, ET.Element):
        children = list(mathml_node)
        if children:
            for ch in children:
                for elem in _convert_element(ch):
                    container.append(elem)
        else:
            # Leaf node with text content (e.g. <mi>x</mi>)
            text = (mathml_node.text or '').strip()
            if text:
                r = OxmlElement('m:r')
                t = OxmlElement('m:t')
                t.text = text
                r.append(t)
                container.append(r)
    else:
        r = OxmlElement('m:r')
        t = OxmlElement('m:t')
        t.text = str(mathml_node)
        r.append(t)
        container.append(r)


def _itertext_strip(el: ET.Element) -> str:
    """Concatenate and strip text content of a MathML element."""
    parts = [el.text or ''] + [child.tail or '' for child in el]
    return ''.join(parts).strip()


def _is_nary(element: ET.Element) -> bool:
    """Heuristic: does this munderover represent an n-ary operator?"""
    ch = list(element)
    if len(ch) < 2:
        return False
    op = ch[1]
    if isinstance(op, ET.Element) and _local_tag(op) in ('mo', 'mi'):
        text = op.text or ''
        return text in ('∑', '∏', '∫', '∮', '∑', '∏', '∫')
    return False


def _build_nary(element: ET.Element) -> List[OxmlElement]:
    """Build an m:nary element for sum / int / prod."""
    ch = list(element)
    nary = OxmlElement('m:nary')
    nary_pr = OxmlElement('m:naryPr')
    chr_el = OxmlElement('m:chr')
    op_text = ''
    if len(ch) >= 2 and isinstance(ch[1], ET.Element):
        op_text = ch[1].text or ''
    chr_el.set(qn('w:val'), op_text)
    nary_pr.append(chr_el)
    nary.append(nary_pr)

    e = OxmlElement('m:e')
    sub_el = OxmlElement('m:sub')
    sup_el = OxmlElement('m:sup')

    _fill_container(e, ch[0])
    if len(ch) >= 3:
        _fill_container(sub_el, ch[2])
    if len(ch) >= 4:
        _fill_container(sup_el, ch[3])

    nary.append(e)
    nary.append(sub_el)
    nary.append(sup_el)
    return [nary]


def _fallback_omath(text: str) -> OxmlElement:
    """Create an m:oMath fallback that shows the raw LaTeX as text."""
    omath = OxmlElement('m:oMath')
    r = OxmlElement('m:r')
    t = OxmlElement('m:t')
    t.text = _sanitize_xml_text(text)
    r.append(t)
    omath.append(r)
    return omath
