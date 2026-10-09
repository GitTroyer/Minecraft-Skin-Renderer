import os
import io
import math
import requests
import numpy as np
import moderngl
from PIL import Image
from termcolor import colored

# ============================================================
# CONFIGURATION
# ============================================================

DEFAULT_SIZE = 512

# ============================================================
# SHADERS
# ============================================================

VERTEX_SHADER = """
#version 330

in vec3 in_position;
in vec3 in_normal;
in vec2 in_uv;

uniform mat4 mvp;
uniform mat3 normal_matrix;

out vec3 v_normal;
out vec2 v_uv;

void main()
{
    gl_Position = mvp * vec4(in_position, 1.0);
    v_normal = normalize(normal_matrix * in_normal);
    v_uv = in_uv;
}
"""

FRAGMENT_SHADER = """
#version 330

uniform sampler2D skin_texture;

uniform vec3 light_direction;
uniform vec3 fill_direction;

in vec3 v_normal;
in vec2 v_uv;

out vec4 fragColor;

void main()
{
    vec4 tex = texture(skin_texture, v_uv);

    if (tex.a < 0.05)
        discard;

    vec3 normal = normalize(v_normal);
    vec3 light = normalize(light_direction);
    vec3 fill = normalize(fill_direction);

    float main_light = max(dot(normal, light), 0.0);
    float fill_amount = max(dot(normal, fill), 0.0);

    float lighting = 0.35 + main_light * 0.55 + fill_amount * 0.15;
    lighting = clamp(lighting, 0.0, 1.0);

    fragColor = vec4(tex.rgb * lighting, tex.a);
}
"""

# ============================================================
# MATH
# ============================================================

def perspective(fov, aspect, near, far):
    f = 1.0 / math.tan(fov / 2.0)
    m = np.zeros((4, 4), dtype=np.float32)

    m[0, 0] = f / aspect
    m[1, 1] = f
    m[2, 2] = (far + near) / (near - far)
    m[2, 3] = (2.0 * far * near) / (near - far)
    m[3, 2] = -1.0

    return m


def look_at(eye, target, up):
    eye = np.asarray(eye, dtype=np.float32)
    target = np.asarray(target, dtype=np.float32)
    up = np.asarray(up, dtype=np.float32)

    forward = target - eye
    forward /= np.linalg.norm(forward)

    right = np.cross(forward, up)
    right /= np.linalg.norm(right)

    real_up = np.cross(right, forward)

    m = np.eye(4, dtype=np.float32)

    m[0, :3] = right
    m[1, :3] = real_up
    m[2, :3] = -forward

    m[0, 3] = -np.dot(right, eye)
    m[1, 3] = -np.dot(real_up, eye)
    m[2, 3] = np.dot(forward, eye)

    return m


def rotation_x(angle):
    c = math.cos(angle)
    s = math.sin(angle)
    return np.array([[1, 0, 0], [0, c, -s], [0, s, c]], dtype=np.float32)


def rotation_y(angle):
    c = math.cos(angle)
    s = math.sin(angle)
    return np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]], dtype=np.float32)


def rotation_z(angle):
    c = math.cos(angle)
    s = math.sin(angle)
    return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]], dtype=np.float32)


# ============================================================
# SKIN
# ============================================================

def load_skin(skin_url):
    response = requests.get(
        skin_url,
        timeout=15,
        headers={"User-Agent": "MinecraftSkinRenderer/1.0"}
    )
    response.raise_for_status()

    image = Image.open(io.BytesIO(response.content)).convert("RGBA")

    if image.size == (128, 128):
        image = image.resize((64, 64), Image.Resampling.NEAREST)

    if image.size != (64, 64):
        raise ValueError("The skin must be 64x64 or 128x128")

    return image


# ============================================================
# UV
# ============================================================

def uv(x, y, width, height):
    u0 = x / 64.0
    u1 = (x + width) / 64.0
    # v0 assigns the bottom edge of the cut to the back of the face
    v0 = (y + height) / 64.0
    # v1 assigns the top edge of the cut to the top of the face
    v1 = y / 64.0

    return (u0, v0, u1, v1)


# ============================================================
# UV MAPS
# ============================================================

def HEAD():
    return {
        "top":    uv(8, 0, 8, 8),
        "bottom": uv(16, 0, 8, 8),
        "left":   uv(0, 8, 8, 8),
        "front":  uv(8, 8, 8, 8),
        "right":  uv(16, 8, 8, 8),
        "back":   uv(24, 8, 8, 8)
    }


def HEAD_OVERLAY():
    return {
        "top":    uv(40, 0, 8, 8),
        "bottom": uv(48, 0, 8, 8),
        "left":   uv(32, 8, 8, 8),
        "front":  uv(40, 8, 8, 8),
        "right":  uv(48, 8, 8, 8),
        "back":   uv(56, 8, 8, 8)
    }


def BODY():
    return {
        "top":    uv(20, 16, 8, 4),
        "bottom": uv(28, 16, 8, 4),
        "left":   uv(16, 20, 4, 12),
        "front":  uv(20, 20, 8, 12),
        "right":  uv(28, 20, 4, 12),
        "back":   uv(32, 20, 8, 12)
    }


def BODY_OVERLAY():
    return {
        "top":    uv(20, 32, 8, 4),
        "bottom": uv(28, 32, 8, 4),
        "left":   uv(16, 36, 4, 12),
        "front":  uv(20, 36, 8, 12),
        "right":  uv(28, 36, 4, 12),
        "back":   uv(32, 36, 8, 12)
    }


def RIGHT_ARM():
    return {
        "top":    uv(44, 16, 4, 4),
        "bottom": uv(48, 16, 4, 4),
        "left":   uv(40, 20, 4, 12),
        "front":  uv(44, 20, 4, 12),
        "right":  uv(48, 20, 4, 12),
        "back":   uv(52, 20, 4, 12)
    }


def RIGHT_ARM_OVERLAY():
    return {
        "top":    uv(44, 32, 4, 4),
        "bottom": uv(48, 32, 4, 4),
        "left":   uv(40, 36, 4, 12),
        "front":  uv(44, 36, 4, 12),
        "right":  uv(48, 36, 4, 12),
        "back":   uv(52, 36, 4, 12)
    }


def LEFT_ARM():
    return {
        "top":    uv(36, 48, 4, 4),
        "bottom": uv(40, 48, 4, 4),
        "left":   uv(32, 52, 4, 12),
        "front":  uv(36, 52, 4, 12),
        "right":  uv(40, 52, 4, 12),
        "back":   uv(44, 52, 4, 12)
    }


def LEFT_ARM_OVERLAY():
    return {
        "top":    uv(52, 48, 4, 4),
        "bottom": uv(56, 48, 4, 4),
        "left":   uv(48, 52, 4, 12),
        "front":  uv(52, 52, 4, 12),
        "right":  uv(56, 52, 4, 12),
        "back":   uv(60, 52, 4, 12)
    }


def RIGHT_LEG():
    return {
        "top":    uv(4, 16, 4, 4),
        "bottom": uv(8, 16, 4, 4),
        "left":   uv(0, 20, 4, 12),
        "front":  uv(4, 20, 4, 12),
        "right":  uv(8, 20, 4, 12),
        "back":   uv(12, 20, 4, 12)
    }


def RIGHT_LEG_OVERLAY():
    return {
        "top":    uv(4, 32, 4, 4),
        "bottom": uv(8, 32, 4, 4),
        "left":   uv(0, 36, 4, 12),
        "front":  uv(4, 36, 4, 12),
        "right":  uv(8, 36, 4, 12),
        "back":   uv(12, 36, 4, 12)
    }


def LEFT_LEG():
    return {
        "top":    uv(20, 48, 4, 4),
        "bottom": uv(24, 48, 4, 4),
        "left":   uv(16, 52, 4, 12),
        "front":  uv(20, 52, 4, 12),
        "right":  uv(24, 52, 4, 12),
        "back":   uv(28, 52, 4, 12)
    }


def LEFT_LEG_OVERLAY():
    return {
        "top":    uv(4, 48, 4, 4),
        "bottom": uv(8, 48, 4, 4),
        "left":   uv(0, 52, 4, 12),
        "front":  uv(4, 52, 4, 12),
        "right":  uv(8, 52, 4, 12),
        "back":   uv(12, 52, 4, 12)
    }


# ============================================================
# 3D MODEL
# ============================================================

def create_box(center, size, uv_map, transform=None):
    cx, cy, cz = center
    sx, sy, sz = size

    hx = sx / 2
    hy = sy / 2
    hz = sz / 2

    vertices = []

    def transform_vertex(position, normal):
        position = np.array(position, dtype=np.float32)
        normal = np.array(normal, dtype=np.float32)

        if transform is not None:
            position = transform[:3, :3] @ position + transform[:3, 3]
            normal = transform[:3, :3] @ normal

        return position, normal

    def add_face(p1, p2, p3, p4, normal, tex):
        u0, v0, u1, v1 = tex

        points = [p1, p2, p3, p1, p3, p4]
        texcoords = [
            (u0, v0), (u1, v0), (u1, v1),
            (u0, v0), (u1, v1), (u0, v1)
        ]

        for point, texcoord in zip(points, texcoords):
            point, n = transform_vertex(point, normal)
            vertices.extend([
                point[0], point[1], point[2],
                n[0], n[1], n[2],
                texcoord[0], texcoord[1]
            ])

    # FRONT
    add_face(
        (cx - hx, cy - hy, cz + hz),
        (cx + hx, cy - hy, cz + hz),
        (cx + hx, cy + hy, cz + hz),
        (cx - hx, cy + hy, cz + hz),
        (0, 0, 1),
        uv_map["front"]
    )

    # BACK
    add_face(
        (cx + hx, cy - hy, cz - hz),
        (cx - hx, cy - hy, cz - hz),
        (cx - hx, cy + hy, cz - hz),
        (cx + hx, cy + hy, cz - hz),
        (0, 0, -1),
        uv_map["back"]
    )

    # LEFT
    add_face(
        (cx - hx, cy - hy, cz - hz),
        (cx - hx, cy - hy, cz + hz),
        (cx - hx, cy + hy, cz + hz),
        (cx - hx, cy + hy, cz - hz),
        (-1, 0, 0),
        uv_map["left"]
    )

    # RIGHT
    add_face(
        (cx + hx, cy - hy, cz + hz),
        (cx + hx, cy - hy, cz - hz),
        (cx + hx, cy + hy, cz - hz),
        (cx + hx, cy + hy, cz + hz),
        (1, 0, 0),
        uv_map["right"]
    )

    # TOP
    add_face(
        (cx - hx, cy + hy, cz + hz),
        (cx + hx, cy + hy, cz + hz),
        (cx + hx, cy + hy, cz - hz),
        (cx - hx, cy + hy, cz - hz),
        (0, 1, 0),
        uv_map["top"]
    )

    # BOTTOM
    add_face(
        (cx - hx, cy - hy, cz - hz),
        (cx + hx, cy - hy, cz - hz),
        (cx + hx, cy - hy, cz + hz),
        (cx - hx, cy - hy, cz + hz),
        (0, -1, 0),
        uv_map["bottom"]
    )

    return np.array(vertices, dtype=np.float32)


# ============================================================
# TRANSFORMATION MATRICES FOR EXTREMITIES
# ============================================================

def part_transform(pivot, rotations):
    """
    Applies a pure rotation around the joint pivot.
    """
    pivot = np.array(pivot, dtype=np.float32)

    rx = rotation_x(rotations[0])
    ry = rotation_y(rotations[1])
    rz = rotation_z(rotations[2])

    rotation = rz @ ry @ rx

    result = np.eye(4, dtype=np.float32)
    result[:3, :3] = rotation
    result[:3, 3] = pivot - rotation @ pivot

    return result


# ============================================================
# MODEL
# ============================================================

def create_player():
    parts = []

    # HEAD AND BODY
    parts.append(create_box((0, 28, 0), (8, 8, 8), HEAD()))
    parts.append(create_box((0, 28, 0), (8.5, 8.5, 8.5), HEAD_OVERLAY()))
    parts.append(create_box((0, 18, 0), (8, 12, 4), BODY()))
    parts.append(create_box((0, 18, 0), (8.5, 12.5, 4.5), BODY_OVERLAY()))

    # RIGHT ARM (Forward / Outward)
    transform_r_arm = part_transform(
        pivot=(-6, 24, 0),
        rotations=(math.radians(-18), math.radians(0), math.radians(-4))
    )
    parts.append(create_box((-6, 18, 0), (4, 12, 4), RIGHT_ARM(), transform_r_arm))
    parts.append(create_box((-6, 18, 0), (4.5, 12.5, 4.5), RIGHT_ARM_OVERLAY(), transform_r_arm))

    # LEFT ARM (Forward / Outward)
    transform_l_arm = part_transform(
        pivot=(6, 24, 0),
        rotations=(math.radians(18), math.radians(0), math.radians(4))
    )
    parts.append(create_box((6, 18, 0), (4, 12, 4), LEFT_ARM(), transform_l_arm))
    parts.append(create_box((6, 18, 0), (4.5, 12.5, 4.5), LEFT_ARM_OVERLAY(), transform_l_arm))

    # RIGHT LEG (Forward / Outward)
    transform_r_leg = part_transform(
        pivot=(-2, 12, 0),
        rotations=(math.radians(22), 0, 0)
    )
    parts.append(create_box((-2, 6, 0), (4, 12, 4), RIGHT_LEG(), transform_r_leg))
    parts.append(create_box((-2, 6, 0), (4.5, 12.5, 4.5), RIGHT_LEG_OVERLAY(), transform_r_leg))

    # LEFT LEG (Forward / Outward)
    transform_l_leg = part_transform(
        pivot=(2, 12, 0),
        rotations=(math.radians(-22), 0, 0)
    )
    parts.append(create_box((2, 6, 0), (4, 12, 4), LEFT_LEG(), transform_l_leg))
    parts.append(create_box((2, 6, 0), (4.5, 12.5, 4.5), LEFT_LEG_OVERLAY(), transform_l_leg))

    return np.concatenate(parts)


# ============================================================
# RENDERS
# ============================================================

def render_skin_gif(skin_url: str, output_path: str, width: int=512, height: int=512, num_frames: int=120, fps: int=30) -> str:
    """ Renders a Minecraft skin as a 3D rotating GIF.
    Args:
        skin_url (str): URL of the Minecraft skin image (64x64 or 128x128).
        output_path (str): Path to save the output GIF.
        width (int): Width of the GIF in pixels.
        height (int): Height of the GIF in pixels.
        num_frames (int): Number of frames in the animation.
        fps (int): Frames per second of the animation.

    Returns:
        str: Path to the generated GIF file.
    """
    try:
        skin = load_skin(skin_url)

        ctx = moderngl.create_standalone_context(require=330)
        ctx.enable(moderngl.DEPTH_TEST)
        ctx.enable(moderngl.BLEND)
        ctx.blend_func = (moderngl.SRC_ALPHA, moderngl.ONE_MINUS_SRC_ALPHA)

        program = ctx.program(
            vertex_shader=VERTEX_SHADER,
            fragment_shader=FRAGMENT_SHADER
        )

        vertices = create_player()
        vbo = ctx.buffer(vertices.tobytes())
        vao = ctx.vertex_array(
            program,
            [(vbo, "3f 3f 2f", "in_position", "in_normal", "in_uv")]
        )

        texture = ctx.texture((64, 64), 4, skin.tobytes())
        texture.filter = (moderngl.NEAREST, moderngl.NEAREST)
        texture.repeat_x = False
        texture.repeat_y = False
        texture.use(location=0)

        program["skin_texture"] = 0

        projection = perspective(math.radians(30), width / height, 0.1, 200.0)
        camera = look_at(eye=(0, 40, 60), target=(0, 16, 0), up=(0, 1, 0))

        program["light_direction"].value = (-0.5, 0.8, 0.7)
        program["fill_direction"].value = (0.7, 0.3, 0.2)

        framebuffer = ctx.simple_framebuffer((width, height), components=4)

        frames = []

        # Generates frames by rotating 360 degrees completely
        for i in range(num_frames):
            angle = (2.0 * math.pi * i) / num_frames

            model = np.eye(4, dtype=np.float32)
            model[:3, :3] = rotation_y(angle)

            mvp = projection @ camera @ model
            program["mvp"].write(mvp.T.astype(np.float32).tobytes())

            normal_matrix = np.linalg.inv(model[:3, :3]).T
            program["normal_matrix"].write(normal_matrix.astype(np.float32).tobytes())

            framebuffer.use()
            framebuffer.clear(0.0, 0.0, 0.0, 0.0)
            vao.render(moderngl.TRIANGLES)

            data = framebuffer.read(components=4, alignment=1)
            img = Image.frombytes("RGBA", (width, height), data)
            img = img.transpose(Image.Transpose.FLIP_TOP_BOTTOM)
            frames.append(img)

        # Saves the sequence as an animated GIF
        duration_ms = int(1000 / fps)
        frames[0].save(
            output_path,
            save_all=True,
            append_images=frames[1:],
            duration=duration_ms,
            loop=0,
            disposal=2
        )

        # Resource cleanup
        framebuffer.release()
        texture.release()
        vao.release()
        vbo.release()
        program.release()
        ctx.release()

        print(colored(f"GIF successfully generated at: {output_path}", "green"))
        return output_path
    
    except Exception as e:
        print(colored(f"Error rendering GIF: {e}", "red"))



def render_skin_image(skin_url: str, output_path: str, width: int=512, height: int=512) -> str:
    """ Renders a Minecraft skin as a 2D image.
    Args:
        skin_url (str): URL of the Minecraft skin image (64x64 or 128x128).
        output_path (str): Path to save the output image.
        width (int): Width of the output image in pixels.
        height (int): Height of the output image in pixels.

    Returns:
        str: Path to the generated image file.
    """
    try:
        skin = load_skin(skin_url)

        ctx = moderngl.create_standalone_context(require=330)
        ctx.enable(moderngl.DEPTH_TEST)
        ctx.enable(moderngl.BLEND)
        ctx.blend_func = (moderngl.SRC_ALPHA, moderngl.ONE_MINUS_SRC_ALPHA)

        program = ctx.program(
            vertex_shader=VERTEX_SHADER,
            fragment_shader=FRAGMENT_SHADER
        )

        vertices = create_player()
        vbo = ctx.buffer(vertices.tobytes())
        vao = ctx.vertex_array(
            program,
            [(vbo, "3f 3f 2f", "in_position", "in_normal", "in_uv")]
        )

        texture = ctx.texture((64, 64), 4, skin.tobytes())
        texture.filter = (moderngl.NEAREST, moderngl.NEAREST)
        texture.repeat_x = False
        texture.repeat_y = False
        texture.use(location=0)

        program["skin_texture"] = 0

        projection = perspective(math.radians(30), width / height, 0.1, 200.0)
        camera = look_at(eye=(28, 40, 55), target=(0, 16, 0), up=(0, 1, 0))

        model = np.eye(4, dtype=np.float32)
        model[:3, :3] = rotation_y(math.radians(-18))

        mvp = projection @ camera @ model
        program["mvp"].write(mvp.T.astype(np.float32).tobytes())

        normal_matrix = np.linalg.inv(model[:3, :3]).T
        program["normal_matrix"].write(normal_matrix.astype(np.float32).tobytes())

        program["light_direction"].value = (-0.5, 0.8, 0.7)
        program["fill_direction"].value = (0.7, 0.3, 0.2)

        framebuffer = ctx.simple_framebuffer((width, height), components=4)
        framebuffer.use()
        framebuffer.clear(0.0, 0.0, 0.0, 0.0)

        vao.render(moderngl.TRIANGLES)

        data = framebuffer.read(components=4, alignment=1)
        image = Image.frombytes("RGBA", (width, height), data)

        # Invert only the final output of the OpenGL Framebuffer
        image = image.transpose(Image.Transpose.FLIP_TOP_BOTTOM)

        image.save(output_path, "PNG")

        framebuffer.release()
        texture.release()
        vao.release()
        vbo.release()
        program.release()
        ctx.release()

        print(colored(f"Image successfully generated at: {output_path}", "green"))
        return output_path
    
    except Exception as e:
        print(colored(f"Error rendering image: {e}", "red"))


if __name__ == "__main__": # Example usage
    os.makedirs("MinecraftSkinRenderer/src/renders", exist_ok=True)
    
    # render_skin_gif(
    #     skin_url="http://textures.minecraft.net/texture/75eb993fa75e1ef66cdb432c484850e8e1b32af07293014e06665ba0ac32a3ad",
    #     output_path="MinecraftSkinRenderer/src/renders/MC_skin_3d_turnable.gif",
    #     width=512,
    #     height=512,
    #     num_frames=120,
    #     fps=30
    # )

    render_skin_image(
        skin_url="http://textures.minecraft.net/texture/75eb993fa75e1ef66cdb432c484850e8e1b32af07293014e06665ba0ac32a3ad",
        output_path="MinecraftSkinRenderer/src/renders/MC_skin_3d.png",
        width=512,
        height=512
    )