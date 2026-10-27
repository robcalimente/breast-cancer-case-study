"""Explanatory schematics. Drawn shapes are not clinical specimens or model inputs."""
from pathlib import Path


def write_measurement_schematics(project: Path) -> None:
    size = '''<text x="140" y="27" class="kicker">01 / SIZE</text>
<ellipse cx="140" cy="144" rx="69" ry="59" fill="#e7f2f2" stroke="#286b70" stroke-width="2.5"/>
<circle cx="140" cy="144" r="3" fill="#253c47"/>
<path d="M140 144 H208" fill="none" stroke="#a94b40" stroke-width="2" marker-end="url(#measure-arrow)"/>
<text x="169" y="132" class="label">radius</text>
<text x="136" y="174" class="muted">area</text>
<path d="M191 184 L226 211" fill="none" stroke="#286b70" stroke-width="1.5"/>
<text x="223" y="227" class="label">outline</text>
<text x="140" y="263" class="caption">Radius, perimeter, area</text>
<text x="140" y="285" class="muted">Measurements of a nucleus</text>'''
    boundary = '''<text x="140" y="27" class="kicker">02 / BOUNDARY</text>
<path d="M92 93 C125 65 187 73 204 109 C226 146 194 155 177 159 C162 166 190 178 198 190 C217 217 179 233 144 222 C102 238 63 204 72 165 C62 127 70 108 92 93 Z" fill="#e7f2f2" stroke="#286b70" stroke-width="2.5"/>
<path d="M237 130 L182 157" fill="none" stroke="#a94b40" stroke-width="1.5" marker-end="url(#measure-arrow)"/>
<text x="230" y="116" class="label">inward dent</text>
<text x="140" y="263" class="caption">Shape of the contour</text>
<text x="140" y="285" class="muted">Concavity describes inward dents</text>'''
    squares = []
    for row in range(11):
        for column in range(11):
            shade = 65 + (row * 31 + column * 17) % 145
            squares.append(f'<rect x="{74 + column * 12}" y="{78 + row * 12}" width="12" height="12" fill="rgb({shade},{shade},{shade})"/>')
    texture = '''<text x="140" y="27" class="kicker">03 / IMAGE TEXTURE</text>
<defs><clipPath id="nucleus-pixels"><ellipse cx="140" cy="144" rx="65" ry="65"/></clipPath></defs>
<g clip-path="url(#nucleus-pixels)">''' + "".join(squares) + '''</g>
<ellipse cx="140" cy="144" rx="65" ry="65" fill="none" stroke="#286b70" stroke-width="2.5"/>
<text x="140" y="263" class="caption">Variation in brightness</text>
<text x="140" y="285" class="muted">A property of image pixels</text>'''
    style = '''<style>text{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;fill:#253c47;text-anchor:middle}.kicker{font-size:12px;font-weight:650;letter-spacing:1px;fill:#286b70}.label{font-size:12px}.caption{font-size:15px;font-weight:600}.muted{font-size:12px;fill:#59636f}</style>'''
    for mobile, filename in [(False, "nuclear-measurements.svg"), (True, "nuclear-measurements-mobile.svg")]:
        width, height = (280, 936) if mobile else (840, 312)
        pieces = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" role="img" aria-labelledby="measurement-title measurement-description">',
                  '<title id="measurement-title">How nuclear size, boundary shape, and image texture become measurements</title>',
                  '<desc id="measurement-description">Conceptual drawings of nuclei, not specimen images and not to scale. Radius runs from center toward the outline, area is enclosed by it, and perimeter follows it. A second contour illustrates an inward dent. A grayscale pattern illustrates brightness variation. None of the drawings has a diagnosis.</desc>',
                  f'<rect width="{width}" height="{height}" fill="#ffffff"/>', style,
                  '<defs><marker id="measure-arrow" markerWidth="6" markerHeight="6" refX="5" refY="3" orient="auto"><path d="M0 0 L6 3 L0 6" fill="none" stroke="#a94b40" stroke-width="1"/></marker></defs>']
        for index, panel in enumerate([size, boundary, texture]):
            x, y = (0, index * 312) if mobile else (index * 280, 0)
            pieces.append(f'<g transform="translate({x} {y})">{panel}</g>')
        pieces.append('</svg>')
        (project / "site/assets" / filename).write_text("\n".join(pieces) + "\n")
