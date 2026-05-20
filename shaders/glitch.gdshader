shader_type canvas_item;
// Glitch post-processing shader — horizontal slice displacement + noise.

uniform float intensity : hint_range(0.0, 1.0) = 0.0;
uniform float time : hint_range(0.0, 60.0) = 0.0;

float hash(vec2 p) {
	return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453);
}

void fragment() {
	vec2 uv = UV;

	// Divide screen into horizontal slices
	float slice_count = 8.0 + (1.0 - intensity) * 100.0;
	float slice = floor(uv.y * slice_count) / slice_count;

	// Each slice may shift independently
	float slice_hash = hash(vec2(slice, floor(time * 5.0)));
	float shift_amount = step(0.7, slice_hash) * intensity * 0.05 * (slice_hash - 0.5) * 2.0;

	vec2 shifted_uv = vec2(uv.x + shift_amount, uv.y);

	// Color channel separation
	float r_shift = intensity * 0.008 * (hash(vec2(slice, time)) - 0.5);
	float b_shift = intensity * 0.008 * (hash(vec2(slice, time + 1.0)) - 0.5);

	float r = texture(TEXTURE, shifted_uv + vec2(r_shift, 0.0)).r;
	float g = texture(TEXTURE, shifted_uv).g;
	float b = texture(TEXTURE, shifted_uv + vec2(b_shift, 0.0)).b;

	vec4 color = vec4(r, g, b, 1.0);

	// Scanline noise
	float scanline = sin(uv.y * 1080.0 * 0.5) * 0.5 + 0.5;
	color.rgb *= mix(1.0, scanline, intensity * 0.3);

	// Random static flickers
	float static_noise = step(0.98, hash(vec2(uv.y * 500.0, time * 60.0)));
	color.rgb = mix(color.rgb, vec3(1.0), static_noise * intensity * 0.5);

	// Edge darkening during glitch
	float edge = abs(uv.y - 0.5) * 2.0;
	color.rgb *= mix(1.0, edge, intensity * 0.4);

	COLOR = color;
}
