shader_type canvas_item;
// Text corruption shader — replaces characters with garbled symbols.
// Controlled via instance uniform: corruption_level (0.0 = clean, 1.0 = fully garbled).

uniform float corruption_level : hint_range(0.0, 1.0) = 0.0;
uniform float time : hint_range(0.0, 60.0) = 0.0;
uniform vec3 corruption_color : source_color = vec3(1.0, 0.0, 0.0);

// Simple hash for pseudo-random per-pixel behavior
float hash(vec2 p) {
	return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453);
}

void fragment() {
	vec4 original = texture(TEXTURE, UV);

	// At low corruption, pixels occasionally shift horizontally
	float pixel_hash = hash(floor(UV * vec2(1920.0, 1080.0)));
	float shift = step(1.0 - corruption_level * 0.3, pixel_hash) * corruption_level * 3.0;

	vec2 shifted_uv = UV + vec2(shift * 0.001, hash(vec2(pixel_hash, time)) * corruption_level * 0.002);

	vec4 color = texture(TEXTURE, shifted_uv);

	// At higher corruption, color channels separate (chromatic aberration)
	if (corruption_level > 0.5) {
		float ca = (corruption_level - 0.5) * 2.0;
		float r = texture(TEXTURE, shifted_uv + vec2(ca * 0.003, 0.0)).r;
		float b = texture(TEXTURE, shifted_uv - vec2(ca * 0.003, 0.0)).b;
		color = vec4(r, color.g, b, color.a);
	}

	// Corruption color bleed at edges
	color.rgb = mix(color.rgb, corruption_color, corruption_level * 0.15 * pixel_hash);

	// Flicker at high corruption
	float flicker = step(0.95, hash(vec2(time * 10.0, UV.y * 100.0)));
	color.a *= mix(1.0, flicker, corruption_level * 0.2);

	COLOR = color;
}
