shader_type canvas_item;
// Mood-driven color grading shader.
// Transitions from deep blue → green → red based on mood_level.

uniform float mood_level : hint_range(0.0, 1.0) = 0.0;
uniform sampler2D screen_texture : hint_screen_texture, repeat_disable, filter_nearest;

// Deep blue #0C1725, Signal green #35A146, Warning red #FF0000
const vec3 deep_blue = vec3(0.047, 0.09, 0.145);
const vec3 signal_green = vec3(0.208, 0.631, 0.275);
const vec3 warning_red = vec3(1.0, 0.0, 0.0);

void fragment() {
	vec4 original = texture(screen_texture, SCREEN_UV);

	// Target tint: blue at 0, green at 0.5, red at 1.0
	vec3 tint;
	if (mood_level < 0.5) {
		tint = mix(deep_blue, signal_green, mood_level * 2.0);
	} else {
		tint = mix(signal_green, warning_red, (mood_level - 0.5) * 2.0);
	}

	// Subtle color overlay — preserve original luminance
	float luminance = dot(original.rgb, vec3(0.299, 0.587, 0.114));
	vec3 tinted = mix(original.rgb, tint, mood_level * 0.25);

	// Desaturate slightly as mood increases
	float saturation = 1.0 - mood_level * 0.4;
	vec3 gray = vec3(luminance);
	tinted = mix(gray, tinted, saturation);

	COLOR = vec4(tinted, original.a);
}
