shader_type canvas_item;
// Scanline overlay — CRT monitor scanline effect.

uniform float scanline_opacity : hint_range(0.0, 1.0) = 0.1;
uniform float time : hint_range(0.0, 60.0) = 0.0;
uniform sampler2D screen_texture : hint_screen_texture, repeat_disable, filter_nearest;

void fragment() {
	vec4 original = texture(screen_texture, SCREEN_UV);

	// Horizontal scanlines
	float line = sin(UV.y * 1080.0 * 0.5) * 0.5 + 0.5;
	float scanline = mix(1.0, line, scanline_opacity);

	// Subtle vertical banding (CRT phosphor trails)
	float band = sin(UV.x * 1920.0 * 0.05 + time * 0.3) * 0.05 + 0.95;

	// Slight vignette
	float vignette = 1.0 - length(UV - 0.5) * 0.3;

	vec4 color = original;
	color.rgb *= scanline * band * vignette;

	COLOR = color;
}
