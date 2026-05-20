shader_type canvas_item;
// Chromatic aberration shader — red/cyan channel offset for analog horror feel.

uniform float aberration_strength : hint_range(0.0, 1.0) = 0.0;
uniform float time : hint_range(0.0, 60.0) = 0.0;

void fragment() {
	vec2 uv = UV;

	// Offset amount increases toward screen edges
	float edge = length(uv - 0.5) * 2.0;
	float offset = aberration_strength * 0.004 * edge;

	// Separate red and blue/cyan channels
	float r = texture(TEXTURE, uv + vec2(offset, 0.0)).r;
	float g = texture(TEXTURE, uv).g;
	float b = texture(TEXTURE, uv - vec2(offset, 0.0)).b;

	vec4 color = vec4(r, g, b, 1.0);

	COLOR = color;
}
