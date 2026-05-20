extends Node
## Screen shake controller — attach to a Camera3D or Camera2D.

enum ShakeTier { SUBTLE = 1, MODERATE = 2, VIOLENT = 3 }

var _shake_intensity: float = 0.0
var _shake_decay: float = 0.9
var _original_offset: Vector3 = Vector3.ZERO
var _target: Node = null


func setup(target: Node) -> void:
	_target = target
	if _target is Camera3D:
		_original_offset = _target.position
	elif _target is Camera2D:
		_original_offset = Vector3(_target.offset.x, _target.offset.y, 0.0)


func trigger(tier: ShakeTier, duration: float = 0.5) -> void:
	match tier:
		ShakeTier.SUBTLE:
			_shake_intensity = 3.0
		ShakeTier.MODERATE:
			_shake_intensity = 12.0
		ShakeTier.VIOLENT:
			_shake_intensity = 25.0

	GlobalState.shake_intensity = _shake_intensity

	var tween := create_tween()
	tween.tween_method(_apply_shake, _shake_intensity, 0.0, duration)
	tween.tween_callback(func():
		_shake_intensity = 0.0
		GlobalState.shake_intensity = 0.0
		_reset_position()
	)


func _apply_shake(current: float) -> void:
	if _target == null: return

	var offset := Vector3(
		randf_range(-current, current),
		randf_range(-current, current),
		0.0
	)

	if _target is Camera3D:
		_target.position = _original_offset + offset
	elif _target is Camera2D:
		_target.offset = Vector2(offset.x, offset.y)


func _reset_position() -> void:
	if _target is Camera3D:
		_target.position = _original_offset
	elif _target is Camera2D:
		_target.offset = Vector2.ZERO
