"""Original line art for the site: an Ionic column that dissolves into binary digits."""
import math


def spiral(cx, cy, r0, r1, turns, flip=1):
    pts = []
    n = 70
    for i in range(n + 1):
        t = i / n
        th = t * turns * 2 * math.pi
        r = r1 - (r1 - r0) * t
        pts.append((cx + flip * r * math.cos(th + math.pi), cy + r * math.sin(th + math.pi)))
    return "M" + " L".join(f"{x:.1f},{y:.1f}" for x, y in pts)


def column(stroke="#e4672a", binary=True, mono="JetBrains Mono, ui-monospace, monospace"):
    s = [f'<svg viewBox="0 0 200 380" xmlns="http://www.w3.org/2000/svg" fill="none" stroke="{stroke}" stroke-width="1.2" stroke-linecap="round" stroke-linejoin="round" role="img" aria-label="Ionic column line drawing that dissolves into binary digits">']
    # abacus
    s.append('<path d="M36 22 H164 L158 36 H42 Z"/><path d="M42 36 H158"/>')
    # volutes and bolster
    s.append(f'<path d="{spiral(58, 62, 3, 17, 2.6)}"/><path d="{spiral(142, 62, 3, 17, 2.6, -1)}"/>')
    s.append('<path d="M58 45 C80 34 120 34 142 45"/><path d="M62 79 C84 92 116 92 138 79"/>')
    s.append('<path d="M75 50 C90 44 110 44 125 50"/>')
    # egg and dart dots
    for i in range(7):
        x = 78 + i * 7.3
        s.append(f'<ellipse cx="{x:.1f}" cy="64" rx="2.4" ry="3.4"/>')
    # neck ring
    s.append('<path d="M70 98 H130"/><path d="M68 104 H132"/>')
    # shaft with entasis
    s.append('<path d="M72 104 C70 190 70 260 72 318"/><path d="M128 104 C130 190 130 260 128 318"/>')
    # flutes left half as lines
    for x in (82, 91):
        s.append(f'<path d="M{x} 108 C{x-1} 190 {x-1} 260 {x} 314" stroke-opacity=".8"/>')
    # right half as binary
    if binary:
        rows = 24
        for r in range(rows):
            y = 116 + r * 8.6
            for k, x in enumerate((101, 110, 119)):
                ch = "01"[(r * 3 + k * 5 + (r // 3)) % 2]
                op = 0.95 - 0.45 * (r / rows) * (k / 2 + .3)
                s.append(f'<text x="{x}" y="{y:.1f}" font-family="{mono}" font-size="8" fill="{stroke}" stroke="none" fill-opacity="{max(op,.25):.2f}" text-anchor="middle">{"01"[(r*3+k*5+(r//3))%2]}</text>')
    else:
        for x in (112, 122):
            s.append(f'<path d="M{x} 108 C{x-1} 190 {x-1} 260 {x} 314"/>')
    # base
    s.append('<path d="M66 318 H134"/><path d="M62 326 C62 332 138 332 138 326 Z"/><path d="M54 336 H146 V346 H54 Z"/><path d="M46 346 H154 V356 H46 Z"/>')
    s.append('</svg>')
    return "".join(s)


def seal(ink="#ddd5c8", copper="#e4672a"):
    """Circular seal with text on a path and the column in the centre."""
    col = column(copper, True).replace('<svg viewBox="0 0 200 380" xmlns="http://www.w3.org/2000/svg"', '<svg x="112" y="96" width="136" height="208" viewBox="0 0 200 380"').replace('role="img" aria-label="Ionic column line drawing that dissolves into binary digits"', '')
    meander = "".join(f'<path transform="rotate({k*11.25} 180 180) translate(176 8)" d="M0 0h8v8h-5v-5h2v3" stroke="{ink}" stroke-opacity=".38" fill="none" stroke-width="1"/>' for k in range(32))
    return f'''<svg viewBox="0 0 360 360" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Seal: clinical AI governance, questionnaire to plan">
<defs><path id="top" d="M 48 180 A 132 132 0 0 1 312 180"/><path id="bot" d="M 36 180 A 144 144 0 0 0 324 180"/></defs>
<circle cx="180" cy="180" r="170" fill="#1f2125" stroke="{ink}" stroke-opacity=".55"/>
<circle cx="180" cy="180" r="156" fill="none" stroke="{ink}" stroke-opacity=".3" stroke-dasharray="2 4"/>
{meander}
<circle cx="180" cy="180" r="112" fill="#17181b" stroke="{ink}" stroke-opacity=".5"/>
<text font-family="JetBrains Mono, ui-monospace, monospace" font-size="13" letter-spacing="3.2" fill="{ink}"><textPath href="#top" startOffset="50%" text-anchor="middle">CLINICAL AI GOVERNANCE</textPath></text>
<text font-family="JetBrains Mono, ui-monospace, monospace" font-size="13" letter-spacing="3.2" fill="{ink}"><textPath href="#bot" startOffset="50%" text-anchor="middle" side="left">QUESTIONNAIRE TO PLAN</textPath></text>
{col}
</svg>'''


def arch():
    return '''<svg class="arch" viewBox="0 0 600 900" preserveAspectRatio="xMidYMax slice" xmlns="http://www.w3.org/2000/svg" fill="none" stroke="currentColor" stroke-opacity=".2" stroke-dasharray="3 5" aria-hidden="true">
<path d="M60 900 V300 A240 240 0 0 1 540 300 V900"/><path d="M110 900 V310 A190 190 0 0 1 490 310 V900"/>
<path d="M0 300 H600 M300 0 V900 M0 120 H600" stroke-dasharray="2 8"/><circle cx="300" cy="300" r="240" stroke-dasharray="1 9"/></svg>'''


def corner():
    """Dotted line capital with a volute, drawn for the corners of a page. Original drawing."""
    s = ['<svg class="corner" viewBox="0 0 320 300" xmlns="http://www.w3.org/2000/svg" fill="none" stroke="currentColor" stroke-linecap="round" stroke-dasharray="1.5 3.6" aria-hidden="true">']
    for y in (14, 34, 52):
        s.append(f'<path d="M0 {y}H250"/>')
    for x in range(8, 246, 14):
        s.append(f'<path d="M{x} 17v14" />')
    s.append('<path d="M0 66H236M0 76H224" stroke-dasharray="1 5"/>')
    s.append(f'<path d="{spiral(78, 150, 4, 58, 3.1)}"/><path d="{spiral(78, 150, 4, 44, 3.1)}" stroke-opacity=".6"/>')
    s.append('<path d="M0 78C40 80 70 86 100 98M136 100C190 82 214 80 236 78"/><path d="M20 210C34 230 60 250 90 258M0 190C10 210 24 236 40 252"/>')
    s.append('<g stroke="none" fill="currentColor" font-family="JetBrains Mono, monospace" font-size="9" fill-opacity=".5">')
    for i, (x, y) in enumerate(((150, 112), (166, 126), (158, 142), (176, 156), (166, 172), (188, 186), (176, 204), (200, 220))):
        s.append(f'<text x="{x}" y="{y}">{"01" if i % 2 else "10"}</text>')
    s.append('</g></svg>')
    return "".join(s)


if __name__ == "__main__":
    open("/tmp/seal.svg", "w").write(seal())
    open("/tmp/col.svg", "w").write(column())
