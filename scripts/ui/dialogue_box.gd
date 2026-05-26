extends Control
## Dialogue box UI — typewriter effect, keyboard simulation, choices, option reduction.

signal text_finished()
signal choice_selected(choice_id: String)
signal keyboard_sim_complete()

# ─── Input mode state machine ───
enum InputMode { NORMAL, TYPING, KEYBOARD_SIM, CHOICE, MINIGAME }
var _input_mode: InputMode = InputMode.NORMAL

# ─── Nodes ───
@onready var name_label: Label = %NameLabel
@onready var text_label: RichTextLabel = %TextLabel
@onready var choice_container: VBoxContainer = %ChoiceContainer
@onready var advance_indicator: Control = %AdvanceIndicator
@onready var animation_player: AnimationPlayer = %AnimationPlayer

# ─── Typewriter state ───
var _is_typing: bool = false
var _full_text: String = ""
var _typed_count: int = 0
var _type_timer: float = 0.0
var _current_line: DialogueManager.DialogueLine = null

# ─── Keyboard simulation state ───
var _keyboard_text: String = ""
var _keyboard_revealed: int = 0
var _keyboard_presses: int = 0
var _keyboard_target_presses: int = 0
var _keyboard_target_chars: int = 0
var _cursor_blink: float = 0.0
var _cursor_visible: bool = true


func _ready() -> void:
	hide()
	choice_container.hide()
	DialogueManager.dialogue_advanced.connect(_on_dialogue_advanced)
	DialogueManager.dialogue_ended.connect(_on_dialogue_ended)
	DialogueManager.choice_presented.connect(_on_choice_presented)
	DialogueManager.keyboard_simulation_started.connect(_on_keyboard_sim_started)


func _process(delta: float) -> void:
	match _input_mode:
		InputMode.TYPING:
			_process_typing(delta)
		InputMode.KEYBOARD_SIM:
			_process_keyboard_cursor(delta)
		_:
			pass


func _process_typing(delta: float) -> void:
	_type_timer += delta
	var cps := GlobalState.text_speed_cps

	while _type_timer >= (1.0 / cps) and _typed_count < _full_text.length():
		_typed_count += 1
		_type_timer -= 1.0 / cps
		_update_text_display()

		if PollutionSystem.should_play_stutter_sfx(GlobalState.get_pollution_tier()):
			pass  # Audio hook reserved for future stutter click assets.

	if _typed_count >= _full_text.length():
		_is_typing = false
		_input_mode = InputMode.NORMAL
		advance_indicator.show()


func _process_keyboard_cursor(delta: float) -> void:
	_cursor_blink += delta
	if _cursor_blink >= 0.5:
		_cursor_blink = 0.0
		_cursor_visible = not _cursor_visible
		_update_keyboard_display()


# ─── Input dispatch ───

func _input(event: InputEvent) -> void:
	if not visible: return

	match _input_mode:
		InputMode.NORMAL:
			_handle_normal_input(event)
		InputMode.TYPING:
			_handle_typing_input(event)
		InputMode.KEYBOARD_SIM:
			_handle_keyboard_sim_input(event)
		InputMode.CHOICE:
			pass  # choices handle their own input via button signals
		InputMode.MINIGAME:
			pass  # minigame controller owns all input


func _handle_normal_input(event: InputEvent) -> void:
	if not _is_advance_event(event): return
	DialogueManager.advance()


func _handle_typing_input(event: InputEvent) -> void:
	if not _is_advance_event(event): return
	# Skip typewriter to end
	_typed_count = _full_text.length()
	_update_text_display()
	_is_typing = false
	_input_mode = InputMode.NORMAL
	advance_indicator.show()


func _handle_keyboard_sim_input(event: InputEvent) -> void:
	if not event.is_pressed(): return
	if event is InputEventKey:
		# Ignore modifier-only keypresses
		var keycode: Key = event.keycode
		if keycode in [KEY_SHIFT, KEY_CTRL, KEY_ALT, KEY_META, KEY_CAPSLOCK, KEY_NUMLOCK, KEY_SCROLLLOCK]:
			return
		if keycode == KEY_ESCAPE: return

		# Each valid keypress reveals part of the fixed line.
		if _keyboard_presses < _keyboard_target_presses:
			_keyboard_presses += 1
			var progress: float = float(_keyboard_presses) / float(_keyboard_target_presses)
			_keyboard_revealed = ceili(float(_keyboard_target_chars) * progress)
			_keyboard_revealed = mini(_keyboard_revealed, _keyboard_target_chars)
			_update_keyboard_display()
			# Audio hook reserved for future keyboard click assets.

		if _keyboard_presses >= _keyboard_target_presses:
			# Brief pause then advance
			await get_tree().create_timer(0.3).timeout
			_input_mode = InputMode.NORMAL
			advance_indicator.show()
			keyboard_sim_complete.emit()
			DialogueManager.advance()


func _is_advance_event(event: InputEvent) -> bool:
	if event.is_action_pressed("ui_accept"):
		return true
	if event is InputEventMouseButton:
		return event.button_index == MOUSE_BUTTON_LEFT and event.pressed
	return false


# ─── Dialogue signal handlers ───

func _on_dialogue_advanced(line: DialogueManager.DialogueLine) -> void:
	_current_line = line
	show()
	choice_container.hide()
	_input_mode = InputMode.NORMAL

	# System interaction lines — skip display, handled by controller interceptors
	var itype := line.get_interaction_type_base()
	if itype in ["env_switch", "forum_post", "dream_sequence", "red_flash", "click_to_walk", "climb_start"]:
		# These are handled by the cartridge/base controller's _on_dialogue_line interceptor
		return

	# Capitolo cards are handled by SceneTransitioner
	if line.is_capitolo:
		text_finished.emit()
		return

	# Use conditional character name (MacGuffin -> ???)
	name_label.text = DialogueManager.get_character_display_name(line.character_id)
	name_label.add_theme_color_override("font_color", line.get_character_color())

	# Apply pollution to text
	var text: String = DialogueManager.get_polluted_text(line)

	# Check interaction type for routing
	var itype_check := line.get_interaction_type_base()
	if itype_check == "memory_text":
		var tier := GlobalState.memory_degradation_tier
		text = PollutionSystem.degrade_memory_text(text, tier)
		GlobalState.memory_degradation_tier = mini(4, tier + 1)

	_start_typewriter(text)


func _on_dialogue_ended() -> void:
	_current_line = null
	_input_mode = InputMode.NORMAL
	hide()
	text_finished.emit()


func _on_choice_presented(choices: Array) -> void:
	_input_mode = InputMode.CHOICE
	choice_container.show()
	_clear_choices()

	for opt in choices:
		var btn := Button.new()
		var text: String = opt.get("text_zh", "") if LanguageManager.current_language == LanguageManager.Language.CHINESE else opt.get("text_ja", "")
		btn.text = text
		btn.add_theme_font_override("font", LanguageManager.get_current_font())
		btn.add_theme_color_override("font_color", Color("35A146"))
		btn.add_theme_color_override("font_hover_color", Color("3FA943"))
		btn.pressed.connect(func(): _on_choice_pressed(opt))
		choice_container.add_child(btn)


func _on_choice_pressed(opt: Dictionary) -> void:
	var choice_id := str(opt.get("id", ""))
	GlobalState.record_choice(choice_id)

	# Apply flag effects based on choice content
	var text: String = opt.get("text_zh", "")
	if "努力说清楚" in text or "はっきり話す" in text:
		GlobalState.add_self_awareness(-5.0)
	elif "保持沉默" in text or "沈黙を守る" in text:
		GlobalState.add_self_awareness(5.0)
		GlobalState.add_silence_affinity(5.0)
	elif "发射" in text or "送信" in text:
		GlobalState.add_belief(10.0)
	elif "不发射" in text or "送信しない" in text:
		GlobalState.add_self_awareness(10.0)

	# Climbing: increment response counter
	if opt.has("climb"):
		GlobalState.climb_responses = mini(GlobalState.climb_responses + 1, 3)

	choice_selected.emit(choice_id)
	choice_container.hide()
	_input_mode = InputMode.NORMAL
	DialogueManager.advance()


# ─── Keyboard simulation ───

func _on_keyboard_sim_started(text: String, keystrokes: int) -> void:
	## Enter keyboard simulation mode. Player types any key to reveal fixed text.
	show()
	choice_container.hide()
	name_label.text = "你" if LanguageManager.current_language == LanguageManager.Language.CHINESE else "あなた"
	name_label.add_theme_color_override("font_color", Color("E8F8E5"))
	_input_mode = InputMode.KEYBOARD_SIM
	_keyboard_text = text
	_keyboard_revealed = 0
	_keyboard_presses = 0
	_keyboard_target_presses = maxi(1, keystrokes)
	_keyboard_target_chars = text.length()
	_cursor_blink = 0.0
	_cursor_visible = true
	advance_indicator.hide()
	_full_text = ""  # suppress normal typewriter display
	_update_keyboard_display()


func _update_keyboard_display() -> void:
	# Show text typed so far, with spaces/underscores for remaining chars
	var displayed := _keyboard_text.substr(0, _keyboard_revealed)
	var remaining := maxi(0, _keyboard_target_chars - _keyboard_revealed)
	var blanks := ""
	for _i in remaining:
		blanks += "_"
	if _cursor_visible:
		displayed += "|"
	text_label.clear()
	text_label.append_text(displayed + blanks)


# ─── Typewriter ───

func _start_typewriter(text: String) -> void:
	_full_text = text
	_typed_count = 0
	_type_timer = 0.0
	_is_typing = true
	_input_mode = InputMode.TYPING
	advance_indicator.hide()
	_update_text_display()


func _update_text_display() -> void:
	var displayed := _full_text.substr(0, _typed_count)
	text_label.clear()
	text_label.append_text(displayed)


# ─── Option reduction (for climbing sequence) ───

func reduce_options(keep_indices: Array) -> void:
	## Removes all choice buttons except those at given indices.
	## Called during climbing: choices dwindle from multiple -> 1 -> empty.
	var children := choice_container.get_children()
	for i in children.size():
		var keep := i in keep_indices
		if children[i] is Button:
			children[i].visible = keep

	if keep_indices.is_empty():
		# No options remain — auto-advance after a brief delay
		choice_container.hide()
		_input_mode = InputMode.NORMAL
		await get_tree().create_timer(0.5).timeout
		DialogueManager.advance()


# ─── Helpers ───

func _clear_choices() -> void:
	for child in choice_container.get_children():
		child.queue_free()


func is_keyboard_mode() -> bool:
	return _input_mode == InputMode.KEYBOARD_SIM
