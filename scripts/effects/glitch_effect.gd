extends Node
## Glitch post-processing effect controller.

signal glitch_triggered(intensity: float)
signal glitch_ended()

var _glitch_timer: float = 0.0
var _glitch_duration: float = 0.0
var _is_active: bool = false
var _intensity: float = 0.0


func trigger_glitch(intensity: float = 0.5, duration: float = 0.3) -> void:
	_intensity = clampf(intensity, 0.0, 1.0)
	_glitch_duration = duration
	_glitch_timer = 0.0
	_is_active = true
	GlobalState.is_glitching = true
	glitch_triggered.emit(_intensity)


func _process(delta: float) -> void:
	if not _is_active: return

	_glitch_timer += delta
	if _glitch_timer >= _glitch_duration:
		_is_active = false
		GlobalState.is_glitching = false
		glitch_ended.emit()


func get_current_offset(intensity_scale: float = 1.0) -> Vector2:
	## Returns a random glitch offset for horizontal slice displacement.
	if not _is_active: return Vector2.ZERO

	var decay := 1.0 - (_glitch_timer / _glitch_duration)
	var dist := _intensity * decay * intensity_scale * 20.0
	return Vector2(randf_range(-dist, dist), randf_range(-dist * 0.3, dist * 0.3))
