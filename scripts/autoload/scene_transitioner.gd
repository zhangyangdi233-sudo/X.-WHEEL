extends Node
## Scene transition controller — autoload singleton. Self-contained (no @onready to scene nodes).
## Handles cartridge transitions, Capitolo cards, glitch folds, fades.

signal transition_complete()

var _color_rect: ColorRect
var _title_label: Label
var _title_sub: Label


func _ready() -> void:
	# Create self-contained UI nodes (not dependent on any scene)
	_color_rect = ColorRect.new()
	_color_rect.name = "TransitionOverlay"
	_color_rect.set_anchors_preset(Control.PRESET_FULL_RECT)
	_color_rect.color = Color.BLACK
	_color_rect.modulate.a = 0.0
	_color_rect.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(_color_rect)

	_title_label = Label.new()
	_title_label.name = "TitleLabel"
	_title_label.add_theme_font_size_override("font_size", 72)
	_title_label.add_theme_color_override("font_color", Color.WHITE)
	_title_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_title_label.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	_title_label.anchors_preset = Control.PRESET_CENTER
	_title_label.modulate.a = 0.0
	add_child(_title_label)

	_title_sub = Label.new()
	_title_sub.name = "TitleSub"
	_title_sub.add_theme_font_size_override("font_size", 24)
	_title_sub.add_theme_color_override("font_color", Color.WHITE)
	_title_sub.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_title_sub.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	_title_sub.anchors_preset = Control.PRESET_CENTER
	_title_sub.position = Vector2(0, 80)
	_title_sub.modulate.a = 0.0
	add_child(_title_sub)


# ─── Capitolo cards (preserved for backward compatibility) ───

func show_capitolo(number: int, subtitle_zh: String, subtitle_ja: String) -> void:
	var sub: String = subtitle_zh if LanguageManager.current_language == LanguageManager.Language.CHINESE else subtitle_ja

	_title_label.text = "Capitolo " + str(number)
	_title_sub.text = "—— " + sub + " ——"

	_color_rect.color = Color.BLACK
	_color_rect.modulate.a = 1.0
	_title_label.show()
	_title_sub.show()

	var tween := create_tween()
	tween.tween_interval(0.5)
	tween.tween_callback(func():
		_title_label.modulate.a = 1.0
	)
	tween.tween_interval(2.0)
	tween.tween_property(_color_rect, "modulate:a", 0.0, 1.0)
	tween.parallel().tween_property(_title_label, "modulate:a", 0.0, 1.0)
	tween.parallel().tween_property(_title_sub, "modulate:a", 0.0, 1.0)
	tween.tween_callback(func():
		_title_label.hide()
		_title_sub.hide()
		transition_complete.emit()
	)


# ─── Cartridge transitions (NEW) ───

func transition_to_cartridge(cartridge_scene_path: String) -> void:
	## Glitch transition + CRT power-on effect.
	GlitchEffect.trigger_glitch(0.6, 0.4)
	await get_tree().create_timer(0.3).timeout
	_color_rect.color = Color.BLACK
	_color_rect.modulate.a = 1.0
	await get_tree().create_timer(0.2).timeout
	get_tree().change_scene_to_file(cartridge_scene_path)
	await get_tree().create_timer(0.1).timeout
	# CRT power-on: fade overlay alpha from 1→0 over 1.5s
	var tween := create_tween()
	tween.tween_property(_color_rect, "modulate:a", 0.0, 1.5)


func transition_from_cartridge(return_scene: String) -> void:
	## CRT power-off + dark fade back to selection.
	# CRT power-off: fade to black over 1.5s
	var tween := create_tween()
	tween.tween_property(_color_rect, "modulate:a", 1.0, 1.5)
	tween.tween_callback(func():
		get_tree().change_scene_to_file(return_scene)
	)
	tween.tween_interval(0.3)
	tween.tween_property(_color_rect, "modulate:a", 0.0, 1.0)


func transition_to_final_chapter() -> void:
	## Console glitch animation + pull-back from desk, then load final chapter.
	GlitchEffect.trigger_glitch(1.0, 0.8)
	await get_tree().create_timer(0.5).timeout
	_color_rect.color = Color.BLACK
	_color_rect.modulate.a = 1.0
	await get_tree().create_timer(0.5).timeout
	get_tree().change_scene_to_file("res://scenes/final_chapter.tscn")
	await get_tree().create_timer(0.2).timeout
	var tween := create_tween()
	tween.tween_property(_color_rect, "modulate:a", 0.0, 2.0)


# ─── General-purpose transitions (preserved from original) ───

func flash_black(duration: float = 0.3) -> void:
	_color_rect.color = Color.BLACK
	_color_rect.modulate.a = 0.0
	var tween := create_tween()
	tween.tween_property(_color_rect, "modulate:a", 1.0, duration * 0.3)
	tween.tween_interval(duration * 0.4)
	tween.tween_property(_color_rect, "modulate:a", 0.0, duration * 0.3)


func fade_to_black(duration: float = 1.0) -> Signal:
	_color_rect.color = Color.BLACK
	_color_rect.modulate.a = 0.0
	var tween := create_tween()
	tween.tween_property(_color_rect, "modulate:a", 1.0, duration)
	return tween.finished


func fade_from_black(duration: float = 1.0) -> void:
	var tween := create_tween()
	tween.tween_property(_color_rect, "modulate:a", 0.0, duration)


func glitch_transition_to(target_scene: String) -> void:
	GlitchEffect.trigger_glitch(0.8, 0.5)
	await get_tree().create_timer(0.3).timeout
	_color_rect.color = Color.BLACK
	_color_rect.modulate.a = 1.0
	await get_tree().create_timer(0.2).timeout
	get_tree().change_scene_to_file(target_scene)
	await get_tree().create_timer(0.1).timeout
	fade_from_black(0.5)
