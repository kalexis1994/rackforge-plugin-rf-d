"""Project and light the RF-D rocker as SVG at package generation time."""
from math import asin, atan2, cos, pi, radians, sin, sqrt, tan

# Panel coordinates: x right, y down, z out of the faceplate.
CAMERA_TILT = radians(21)
LIGHT_AZIMUTH = radians(225)
LIGHT_ELEVATION = radians(36)
LIGHT = (
    cos(LIGHT_ELEVATION) * cos(LIGHT_AZIMUTH),
    cos(LIGHT_ELEVATION) * sin(LIGHT_AZIMUTH),
    sin(LIGHT_ELEVATION),
)
VIEW = (0, sin(CAMERA_TILT), cos(CAMERA_TILT))
HALF_VECTOR = tuple(light + eye for light, eye in zip(LIGHT, VIEW))
HALF_VECTOR_NORM = sqrt(sum(value * value for value in HALF_VECTOR))
HALF_VECTOR = tuple(value / HALF_VECTOR_NORM for value in HALF_VECTOR)
CAMERA_COS = cos(CAMERA_TILT)
CAMERA_SIN = sin(CAMERA_TILT)

HALF_WIDTH = 19
RADIUS = 35
MOUTH_EDGE = radians(24)
PIVOT_HEIGHT = 4
ROCK_ANGLE = radians(12)
FLOOR_ANGLE = asin(PIVOT_HEIGHT / RADIUS)


def coordinates(point):
    return f"{point[0]:.2f},{point[1]:.2f}"


def polygon(points):
    coords = " ".join(map(coordinates, points))
    return f'<polygon points="{coords}"'


def arc(project, start, end, width):
    """Project a cubic segment of the circular shoulder, including its tangents."""
    scale = 4 / 3 * tan((end - start) / 4)
    u0, z0 = cos(start), sin(start)
    u1, z1 = cos(end), sin(end)
    points = ((u0 - scale * z0, z0 + scale * u0), (u1 + scale * z1, z1 - scale * u1), (u1, z1))
    return "C" + " ".join(coordinates(project(RADIUS * u, width, RADIUS * z)) for u, z in points)


def dot(left, right):
    return sum(a * b for a, b in zip(left, right))


def tint(normal):
    diffuse = max(0, dot(normal, LIGHT))
    specular = max(0, dot(normal, HALF_VECTOR)) ** 14
    shade = .44 + .65 * diffuse + .25 * specular
    if shade >= .79:
        return "#fff5e3", (shade - .79) * .91
    return "#0d100e", (.79 - shade) * 1.12


def surface(shape, color, alpha):
    return (shape + ' fill="var(--switch, #467e9f)"/>'
            + shape + f' fill="{color}" opacity="{alpha:.3f}"/>')


def shoulder_light(name, project, start, end, direction):
    first = project(RADIUS * cos(start), 0, RADIUS * sin(start))
    last = project(RADIUS * cos(end), 0, RADIUS * sin(end))
    nx, ny = direction
    stops = []
    for step in range(7):
        fraction = step / 6
        angle = start + fraction * (end - start)
        color, alpha = tint((cos(angle) * nx, cos(angle) * ny, sin(angle)))
        stops.append(f'<stop offset="{fraction:.3f}" stop-color="{color}" stop-opacity="{alpha:.3f}"/>')
    return (f'<linearGradient id="{name}" gradientUnits="userSpaceOnUse" '
            f'x1="{first[0]:.2f}" y1="{first[1]:.2f}" x2="{last[0]:.2f}" y2="{last[1]:.2f}">'
            + "".join(stops) + "</linearGradient>")


def rocker_cap(name, direction, pressed):
    # Orient the physical piece before projecting it. The light and eye stay
    # in panel coordinates for both states of all three orientations.
    ux, uy = direction
    vx, vy = -uy, ux
    tilt = ROCK_ANGLE if pressed else -ROCK_ANGLE
    left, right = pi - MOUTH_EDGE - tilt, MOUTH_EDGE - tilt

    def project(u, v, z):
        return (50 + u * ux + v * vx,
                50 + (u * uy + v * vy) * CAMERA_COS - (PIVOT_HEIGHT + z) * CAMERA_SIN)

    def rim(angle, width):
        return project(RADIUS * cos(angle), width, RADIUS * sin(angle))

    w = HALF_WIDTH
    shadow = [project(u, v, -PIVOT_HEIGHT) for u, v in
              ((-RADIUS, -w), (RADIUS, -w), (RADIUS, w), (-RADIUS, w))]
    shadow = [(x - LIGHT[0] * 3, y - LIGHT[1] * 3 + 1) for x, y in shadow]
    parts = [f'<g id="{name}">', polygon(shadow) + ' fill="#090806" opacity=".76"/>']
    gradients = []

    # The housing covers the back of the disk below z=0. Draw only the
    # exposed circular shoulders whose normals face the camera.
    view_angle = atan2(VIEW[2], VIEW[1] * uy)
    shoulder_ranges = ((max(left, view_angle - pi / 2), min(pi + FLOOR_ANGLE, view_angle + pi / 2)),
                       (max(-FLOOR_ANGLE, view_angle - pi / 2), min(right, view_angle + pi / 2)))
    for side, (start, end) in enumerate(shoulder_ranges):
        if end <= start:
            continue
        path = (f'M{coordinates(rim(start, -w))}' + arc(project, start, end, -w)
                + f'L{coordinates(rim(end, w))}' + arc(project, end, start, w) + "Z")
        light_id = f"{name}-shoulder-{side}"
        gradients.append(shoulder_light(light_id, project, start, end, direction))
        parts.append(surface(f'<path d="{path}"', f"url(#{light_id})", 1))

    if vy:
        near = w * vy
        cheek = (f'M{coordinates(rim(pi + FLOOR_ANGLE, near))}' + arc(project, pi + FLOOR_ANGLE, left, near)
                 + f'L{coordinates(project(0, near, 0))}L{coordinates(rim(right, near))}'
                 + arc(project, right, -FLOOR_ANGLE, near) + "Z")
        parts.append(surface(f'<path d="{cheek}"', "#10110e", .4))

    for end, sign in ((left, -1), (right, 1)):
        face = polygon([project(0, -w, 0), rim(end, -w), rim(end, w), project(0, w, 0)])
        normal_u = -sign * sin(end)
        normal = (normal_u * ux, normal_u * uy, sign * cos(end))
        parts.append(surface(face, *tint(normal)))
    seam = f'M{coordinates(project(0, -w, 0))}L{coordinates(project(0, w, 0))}'
    parts.append(f'<path d="{seam}" fill="none" stroke="#151611" stroke-opacity=".32" stroke-width=".9"/></g>')
    return "".join(gradients + parts)


def rocker_symbols():
    return "\n".join(
        rocker_cap(f"rocker-{name}-{state}", axis, state == "on")
        for name, axis in (("horizontal", (1, 0)), ("up", (0, -1)), ("down", (0, 1)))
        for state in ("off", "on")
    )
