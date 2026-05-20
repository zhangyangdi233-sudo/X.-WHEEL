extends Control
## Dialogue box UI — displays character name, text with typewriter effect, and advances.

signal text_finished()
signal choice_selected(choice_id: String)

@onready var name_label: Label = %NameLabel
@onready var text_label: RichTextLabel = %TextLabel
@onready var choice_container: VBoxContainer = %ChoiceContainer
@onready var advance_indicator: Control = %AdvanceIndicator
@onready var animation_player: AnimationPlayer = %AnimationPlayer

var _is_typing: bool = false
var _full_text: String = ""
var _typed_count: int = 0
var _type_timer: float = 0.0
var _current_line: DialogueManager.DialogueLine = null


func _ready() -> void:
	hide()
	choice_container.hide()
	DialogueManager.dialogue_advanced.connect(_on_dialogue_advanced)
	DialogueManager.dialogue_ended.connect(_on_dialogue_ended)
	DialogueManager.choice_presented.connect(_on_choice_presented)


func _process(delta: float) -> void:
	if not _is_typing: return

	_type_timer += delta
	var cps := GlobalState.text_speed_cps

	while _type_timer >= (1.0 / cps) and _typed_count < _full_text.length():
		_typed_count += 1
		_type_timer -= 1.0 / cps
		_update_text_display()

		if PollutionSystem.should_play_stutter_sfx(GlobalState.get_pollution_tier()):
			pass  # TODO: Add stutter SFX when audio assets are ready

	if _typed_count >= _full_text.length():
		_is_typing = false
		advance_indicator.show()


func _input(event: InputEvent) -> void:
	if not visible: return

	var should_advance := event.is_action_pressed("ui_accept")
	if event is InputEventMouseButton:
		should_advance = should_advance or event.button_index == MOUSE_BUTTON_LEFT and event.pressed

	if should_advance:
		if _is_typing:
			# Skip to end of typewriter
			_typed_count = _full_text.length()
			_update_text_display()
			_is_typing = false
			advance_indicator.show()
		elif choice_container.visible:
			return  # choices handle their own input
		else:
			DialogueManager.advance()


func _on_dialogue_advanced(line: DialogueManager.DialogueLine) -> void:
	_current_line = line
	show()
	choice_container.hide()

	# Capitolo cards are a special scene, not a dialogue line
	if line.is_capitolo:
		text_finished.emit()
		return

	# Set character name
	name_label.text = line.character_id
	name_label.add_theme_color_override("font_color", line.get_character_color())

	# Apply pollution to the text
	var text: String = DialogueManager.get_polluted_text(line)
	_start_typewriter(text)


func _on_dialogue_ended() -> void:
	_current_line = null
	hide()
	text_finished.emit()


func _on_choice_presented(choices: Array) -> void:
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

	choice_selected.emit(choice_id)
	choice_container.hide()
	DialogueManager.advance()


func _start_typewriter(text: String) -> void:
	_full_text = text
	_typed_count = 0
	_type_timer = 0.0
	_is_typing = true
	advance_indicator.hide()
	_update_text_display()


func _update_text_display() -> void:
	var displayed := _full_text.substr(0, _typed_count)
	text_label.clear()
	text_label.append_text(displayed)


func _clear_choices() -> void:
	for child in choice_container.get_children():
		child.queue_free()
