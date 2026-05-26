shader_type canvas_item;

// CRT monitor bezel + phosphor glow effect
uniform float power_on : hint_range(0.0, 1.0) = 1.0;
uniform vec4 bezel_color : source_color = vec4(0.05, 0.05, 0.05, 1.0);
uniform float curvature : hint_range(0.0, 0.1) = 0.02;

void fragment() {
	vec2 uv = UV;
	vec2 center = uv - 0.5;

	// Barrel distortion (subtle screen curvature)
	float dist = length(center);
	uv += center * dist * dist * curvature;

	// Rounded bezel corners
	float corner_radius = 0.06;
	float edge_dist = 1.0;
	edge_dist = min(edge_dist, smoothstep(0.0, corner_radius, uv.x));
	edge_dist = min(edge_dist, smoothstep(0.0, corner_radius, 1.0 - uv.x));
	edge_dist = min(edge_dist, smoothstep(0.0, corner_radius, uv.y));
	edge_dist = min(edge_dist, smoothstep(0.0, corner_radius, 1.0 - uv.y));

	// Inner shadow at screen edges
	float inner_shadow = smoothstep(0.0, 0.15, uv.x) * smoothstep(0.0, 0.15, 1.0 - uv.x)
		* smoothstep(0.0, 0.15, uv.y) * smoothstep(0.0, 0.15, 1.0 - uv.y);

	// Phosphor glow near center — subtle green tint at full power
	float glow = 1.0 - abs(center.x) * 1.8 - abs(center.y) * 1.4;
	glow = smoothstep(0.0, 0.3, glow) * 0.08 * power_on;

	// Bezel color
	vec3 bezel = bezel_color.rgb;

	// Screen area (inner 92%) — transparent to show content
	float screen_alpha = smoothstep(0.04, 0.08, inner_shadow);

	// Combine
	vec3 color = bezel + vec3(0.15, 0.25, 0.15) * glow;
	COLOR = vec4(color, 1.0 - screen_alpha * edge_dist * power_on);
}
