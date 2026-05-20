shader_type canvas_item;
// Vignette overlay — darkens screen edges, used for tension/immersion.

uniform float vignette_intensity : hint_range(0.0, 1.0) = 0.3;
uniform vec4 edge_color : source_color = vec4(0.047, 0.09, 0.145, 1.0); // #0C1725
uniform float red_bleed : hint_range(0.0, 1.0) = 0.0; // red creeping in at climax
uniform sampler2D screen_texture : hint_screen_texture, repeat_disable, filter_nearest;

void fragment() {
	vec4 original = texture(screen_texture, SCREEN_UV);

	// Radial gradient from center
	float dist = length(UV - 0.5) * 1.4;

	// Vignette strength
	float vignette = smoothstep(0.3, 1.0, dist) * vignette_intensity;

	// Red bleed at extreme mood (climax)
	vec4 vignette_color = edge_color;
	if (red_bleed > 0.0) {
		vignette_color = mix(edge_color, vec4(1.0, 0.0, 0.0, 1.0), red_bleed * vignette);
	}

	vec4 color = mix(original, vignette_color, vignette);

	COLOR = color;
}
