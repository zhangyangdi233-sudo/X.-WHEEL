class_name CartridgeBaseController
extends Node3D
## Shared base controller for all 3 cartridge scenes.
## Handles CRT framework setup, dialogue lifecycle, and cartridge completion.

signal cartridge_started()
signal cartridge_completed()

# ─── Override in subclasses ───
@export var cartridge_name: String = ""
@export var dialogue_csv: String = ""

# ─── CRT overlay references ───
var _crt_bezel: ColorRect
var _transition_overlay: ColorRect
var _power_indicator: Label
var _mood_overlay: ColorRect
var _vignette_overlay: ColorRect
var _forum_overlay: Control
var _forum_label: Label

# ─── State ───
var is_active: bool = false
var _has_cigarette_butt: bool = false
var _ui_layer: CanvasLayer


func _ready() -> void:
	_validate_setup()
	_find_crt_overlays()
	_setup_dialogue_box()
	_connect_signals()
	_power_on_sequence()


func _validate_setup() -> void:
	if cartridge_name.is_empty():
		push_warning("cartridge_base: cartridge_name not set on ", name)
	if dialogue_csv.is_empty():
		push_warning("cartridge_base: dialogue_csv not set on ", name)


func _find_crt_overlays() -> void:
	var ui := get_node_or_null("UICanvas")
	if ui:
		_ui_layer = ui
		_crt_bezel = ui.get_node_or_null("CRTBezel") as ColorRect
		_transition_overlay = ui.get_node_or_null("TransitionOverlay") as ColorRect
		_power_indicator = ui.get_node_or_null("PowerIndicator") as Label
		_mood_overlay = ui.get_node_or_null("MoodOverlay") as ColorRect
		_vignette_overlay = ui.get_node_or_null("VignetteOverlay") as ColorRect


func _setup_dialogue_box() -> void:
	# Instantiate dialogue box into the UI layer
	if not _ui_layer: return
	var db_scene := load("res://scenes/ui/dialogue_box.tscn")
	if db_scene:
		var db: Node = db_scene.instantiate()
		db.name = "DialogueBox"
		_ui_layer.add_child(db)
	_create_forum_overlay()


func _create_forum_overlay() -> void:
	if not _ui_layer:
		return
	_forum_overlay = Control.new()
	_forum_overlay.name = "ForumOverlay"
	_forum_overlay.set_anchors_preset(Control.PRESET_FULL_RECT)
	_forum_overlay.mouse_filter = Control.MOUSE_FILTER_STOP
	_forum_overlay.modulate.a = 0.0
	_forum_overlay.hide()

	var bg := ColorRect.new()
	bg.set_anchors_preset(Control.PRESET_FULL_RECT)
	bg.color = Color(0.02, 0.025, 0.035, 0.9)
	_forum_overlay.add_child(bg)

	_forum_label = Label.new()
	_forum_label.name = "ForumText"
	_forum_label.set_anchors_preset(Control.PRESET_CENTER)
	_forum_label.offset_left = -420
	_forum_label.offset_right = 420
	_forum_label.offset_top = -120
	_forum_label.offset_bottom = 160
	_forum_label.add_theme_font_override("font", LanguageManager.get_current_font())
	_forum_label.add_theme_font_size_override("font_size", 18)
	_forum_label.add_theme_color_override("font_color", Color("3FA943"))
	_forum_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_forum_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_forum_overlay.add_child(_forum_label)

	_ui_layer.add_child(_forum_overlay)


func _connect_signals() -> void:
	DialogueManager.dialogue_advanced.connect(_on_dialogue_line)
	DialogueManager.dialogue_ended.connect(_on_dialogue_ended)
	DialogueManager.keyboard_simulation_started.connect(_on_keyboard_sim_started)
	DialogueManager.minigame_triggered.connect(_on_minigame_triggered)
	DialogueManager.title_card_requested.connect(_on_title_card_requested)
	DialogueManager.credit_roll_requested.connect(_on_credit_roll)


# ─── Power on/off sequences ───

func _power_on_sequence() -> void:
	# Start with transition overlay covering the screen
	if _transition_overlay:
		_transition_overlay.modulate = Color(0, 0, 0, 1)

	# Fade transition overlay from black to transparent (CRT power-on)
	if _transition_overlay:
		var tween := create_tween()
		tween.tween_property(_transition_overlay, "modulate:a", 0.0, 1.5)
		tween.tween_callback(func():
			is_active = true
			_setup_environment()
			_on_cartridge_start()
			if not dialogue_csv.is_empty():
				DialogueManager.start_dialogue(dialogue_csv)
			cartridge_started.emit()
		)
	else:
		await get_tree().create_timer(1.5).timeout
		is_active = true
		_setup_environment()
		_on_cartridge_start()
		if not dialogue_csv.is_empty():
			DialogueManager.start_dialogue(dialogue_csv)
		cartridge_started.emit()

	# Animate CRT bezel power_on from 0 to 1
	_animate_crt_power(0.0, 1.0, 1.5)


func _power_off_sequence() -> void:
	is_active = false

	# Animate CRT power off
	_animate_crt_power(1.0, 0.0, 1.5)

	# Fade to black
	if _transition_overlay:
		var tween := create_tween()
		tween.tween_property(_transition_overlay, "modulate:a", 1.0, 1.5)
		tween.tween_callback(_on_power_off_complete)
	else:
		await get_tree().create_timer(1.5).timeout
		_on_power_off_complete()


func _animate_crt_power(from_val: float, to_val: float, duration: float) -> void:
	if not _crt_bezel: return
	var mat: ShaderMaterial = _crt_bezel.material
	if not mat: return
	var tween := create_tween()
	tween.tween_method(
		func(v: float): mat.set_shader_parameter("power_on", v),
		from_val, to_val, duration
	)


func _on_power_off_complete() -> void:
	cartridge_completed.emit()
	GlobalState.mark_cartridge_completed(cartridge_name)

	# Check for post-credits / final chapter unlock
	if GlobalState.all_cartridges_completed:
		# Transition to final chapter instead of cartridge select
		SceneTransitioner.transition_to_final_chapter()
	else:
		SceneTransitioner.transition_from_cartridge("res://scenes/cartridge_select.tscn")


# ─── Virtual methods — override in subclasses ───

func _setup_environment() -> void:
	## Override: create 3D environment nodes for this cartridge.
	pass


func _on_cartridge_start() -> void:
	## Override: called after CRT power-on, before dialogue starts.
	pass


func _on_cartridge_complete() -> void:
	## Override: called when dialogue reaches end, before power-off.
	pass


func _handle_interaction_type(itype: String, _data: Dictionary) -> void:
	## Override: handle cartridge-specific interaction types.
	match itype:
		"dream_sequence":
			_handle_dream_sequence()
		"red_flash":
			_handle_red_flash()
		"memory_text":
			_handle_memory_text(_data)
		"env_switch":
			_switch_environment(_data.get("env", ""))
		"forum_post":
			_show_forum_post(_data.get("text", ""))


# ─── Shared interaction handlers ───

func _handle_dream_sequence() -> void:
	# Mood shader shift: blue → green, vignette intensifies
	if _mood_overlay:
		var mat: ShaderMaterial = _mood_overlay.material
		if mat:
			var tween := create_tween()
			tween.tween_method(
				func(v: float): mat.set_shader_parameter("mood_level", v),
				0.0, 0.5, 1.0
			)
			tween.tween_interval(0.5)
			tween.tween_method(
				func(v: float): mat.set_shader_parameter("mood_level", v),
				0.5, 0.0, 1.0
			)


func _handle_red_flash() -> void:
	if not _transition_overlay: return
	var tween := create_tween()
	_transition_overlay.modulate = Color(1, 0.15, 0.05, 0.0)
	tween.tween_property(_transition_overlay, "modulate:a", 0.4, 0.15)
	tween.tween_property(_transition_overlay, "modulate:a", 0.0, 0.5)


func _handle_memory_text(_data: Dictionary) -> void:
	# Memory text degradation is handled by DialogueBox + PollutionSystem
	pass


func _switch_environment(env_name: String) -> void:
	## Override: switch which 3D environment nodes are visible.
	pass


func _show_forum_post(text: String) -> void:
	if _forum_overlay == null or _forum_label == null:
		DialogueManager.advance()
		return
	_forum_label.text = text
	_forum_overlay.show()
	var tween := create_tween()
	tween.tween_property(_forum_overlay, "modulate:a", 1.0, 0.2)
	tween.tween_interval(1.2)
	tween.tween_property(_forum_overlay, "modulate:a", 0.0, 0.25)
	tween.tween_callback(func():
		_forum_overlay.hide()
		DialogueManager.advance()
	)


# ─── Dialogue line interceptor — handle system interaction lines ───

func _on_dialogue_line(line: DialogueManager.DialogueLine) -> void:
	var itype := line.get_interaction_type_base()
	if itype.is_empty() or itype == "dialogue":
		return  # Let dialogue_box handle it normally

	# System interaction types that need immediate handling
	var param := line.get_interaction_param()
	var data: Dictionary = {}
	if itype == "env_switch":
		data["env"] = param
	elif itype == "keyboard_sim":
		data["text"] = line.get_text(LanguageManager.current_language)
		data["keystrokes"] = maxi(1, param.to_int())
	elif itype == "minigame_trigger":
		data["name"] = param
	elif itype == "forum_post":
		data["text"] = line.get_text(LanguageManager.current_language)
	elif itype == "click_to_walk" or itype == "climb_start":
		data["action"] = itype

	_handle_interaction_type(itype, data)

	# Auto-advance past system lines (they have no text to display)
	if line.get_text(LanguageManager.current_language).is_empty() and not line.is_choice:
		DialogueManager.advance()


# ─── Interaction type dispatch ───

func _on_dialogue_ended() -> void:
	_on_cartridge_complete()

	# Check for cigarette butt scene
	if _has_cigarette_butt and not cartridge_name.is_empty():
		GlobalState.cigarette_butt_seen[cartridge_name] = true

	# Save progress
	var save_slot := SaveSystem.get_latest_save()
	if save_slot < 0:
		save_slot = 0
	SaveSystem.save_game(save_slot)

	# Power off and return
	_power_off_sequence()


func _on_keyboard_sim_started(text: String, keystrokes: int) -> void:
	_handle_interaction_type("keyboard_sim", {"text": text, "keystrokes": keystrokes})


func _on_minigame_triggered(minigame_name: String) -> void:
	_handle_interaction_type("minigame", {"name": minigame_name})


func _on_title_card_requested(title_text: String, duration: float) -> void:
	_handle_interaction_type("title_card", {"text": title_text, "duration": duration})


func _on_credit_roll() -> void:
	_handle_interaction_type("credit_roll", {})


# ─── Helpers ───

func get_dialogue_box() -> Control:
	if _ui_layer:
		return _ui_layer.get_node_or_null("DialogueBox") as Control
	return null
