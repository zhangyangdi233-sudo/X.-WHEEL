extends Node
## Scene transition controller — Capitolo cards, glitch folds, fades.

signal transition_complete()

@onready var _color_rect: ColorRect = %TransitionOverlay
@onready var _capitolo_label: Label = %CapitoloLabel
@onready var _capitolo_sub: Label = %CapitoloSub
@onready var _anim: AnimationPlayer = %TransitionAnim


func _ready() -> void:
	_color_rect.hide()
	_capitolo_label.hide()
	_capitolo_sub.hide()


func show_capitolo(number: int, subtitle_zh: String, subtitle_ja: String) -> void:
	## Display the Capitolo card (black screen → white bold title → fade to scene).
	var sub: String = subtitle_zh if LanguageManager.current_language == LanguageManager.Language.CHINESE else subtitle_ja

	_capitolo_label.text = "Capitolo " + str(number)
	_capitolo_sub.text = "—— " + sub + " ——"

	_color_rect.color = Color.BLACK
	_color_rect.modulate.a = 1.0
	_color_rect.show()
	_capitolo_label.show()
	_capitolo_sub.show()

	var tween := create_tween()
	tween.tween_interval(0.5)  # pure black pause
	tween.tween_callback(func():
		_capitolo_label.modulate.a = 1.0
	)
	tween.tween_interval(2.0)  # hold capitolo card
	tween.tween_property(_color_rect, "modulate:a", 0.0, 1.0)
	tween.parallel().tween_property(_capitolo_label, "modulate:a", 0.0, 1.0)
	tween.parallel().tween_property(_capitolo_sub, "modulate:a", 0.0, 1.0)
	tween.tween_callback(func():
		_color_rect.hide()
		_capitolo_label.hide()
		_capitolo_sub.hide()
		transition_complete.emit()
	)


func flash_black(duration: float = 0.3) -> void:
	## Quick black flash — used for the 1999 chatroom ↔ tower intercut.
	_color_rect.color = Color.BLACK
	_color_rect.modulate.a = 0.0
	_color_rect.show()

	var tween := create_tween()
	tween.tween_property(_color_rect, "modulate:a", 1.0, duration * 0.3)
	tween.tween_interval(duration * 0.4)
	tween.tween_property(_color_rect, "modulate:a", 0.0, duration * 0.3)
	tween.tween_callback(_color_rect.hide)


func fade_to_black(duration: float = 1.0) -> Signal:
	_color_rect.color = Color.BLACK
	_color_rect.modulate.a = 0.0
	_color_rect.show()

	var tween := create_tween()
	tween.tween_property(_color_rect, "modulate:a", 1.0, duration)
	return tween.finished


func fade_from_black(duration: float = 1.0) -> void:
	var tween := create_tween()
	tween.tween_property(_color_rect, "modulate:a", 0.0, duration)
	tween.tween_callback(_color_rect.hide)


func glitch_transition_to(target_scene: String) -> void:
	## Glitch-fold the screen and transition to a new scene.
	GlitchEffect.trigger_glitch(0.8, 0.5)

	await get_tree().create_timer(0.3).timeout
	_color_rect.color = Color.BLACK
	_color_rect.modulate.a = 1.0
	_color_rect.show()

	await get_tree().create_timer(0.2).timeout
	get_tree().change_scene_to_file(target_scene)

	await get_tree().create_timer(0.1).timeout
	fade_from_black(0.5)
