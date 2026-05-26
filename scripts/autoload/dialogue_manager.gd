extends Node
## Dialogue system — parses CSV, manages dialogue queue, handles text display.
## Extended for 8-column CSV: id, character_id, emotion, text_zh, text_ja, safe_version, condition, interaction_type

# ─── Signals ───
signal dialogue_started(line: DialogueLine)
signal dialogue_advanced(line: DialogueLine)
signal dialogue_ended()
signal choice_presented(choices: Array)
signal keyboard_simulation_started(text: String, keystrokes: int)
signal minigame_triggered(minigame_name: String)
signal title_card_requested(title_text: String, duration: float)
signal credit_roll_requested()

# ─── Interaction type constants ───
const TYPE_DIALOGUE := "dialogue"
const TYPE_KEYBOARD_SIM := "keyboard_sim"
const TYPE_MINIGAME_TRIGGER := "minigame_trigger"
const TYPE_TITLE_CARD := "title_card"
const TYPE_CREDIT_ROLL := "credit_roll"
const TYPE_FORUM_POST := "forum_post"
const TYPE_DREAM_SEQUENCE := "dream_sequence"
const TYPE_RED_FLASH := "red_flash"
const TYPE_MEMORY_TEXT := "memory_text"
const TYPE_ENV_SWITCH := "env_switch"

# ─── Internal state ───
var _dialogue_queue: Array[DialogueLine] = []
var _current_index: int = 0
var _is_active: bool = false
var _current_csv: String = ""
var _all_loaded: Dictionary = {}  # csv_path -> Array[DialogueLine]


# ─── DialogueLine resource ───
class DialogueLine:
	var id: String
	var character_id: String
	var emotion: String
	var text_zh: String
	var text_ja: String
	var safe_version: String
	var condition: String = ""         # conditional gating (flag name, !flag, or || chains)
	var interaction_type: String = ""  # "dialogue"|"keyboard_sim:N"|"minigame_trigger:name"|etc.
	var is_choice: bool = false
	var choice_options: Array[Dictionary] = []
	var is_capitolo: bool = false
	var capitolo_number: int = -1
	var capitolo_subtitle_zh: String = ""
	var capitolo_subtitle_ja: String = ""

	func get_text(lang: LanguageManager.Language) -> String:
		return text_zh if lang == LanguageManager.Language.CHINESE else text_ja

	func get_character_color() -> Color:
		return LanguageManager.get_color_for_character(character_id)

	func get_interaction_type_base() -> String:
		## Returns the base interaction type without colon-separated params.
		var colon := interaction_type.find(":")
		return interaction_type.substr(0, colon) if colon >= 0 else interaction_type

	func get_interaction_param() -> String:
		## Returns the colon-separated param, or empty string.
		var colon := interaction_type.find(":")
		return interaction_type.substr(colon + 1) if colon >= 0 else ""


func load_dialogue_csv(path: String) -> void:
	if _all_loaded.has(path) and _all_loaded[path].size() > 0:
		return

	var file := FileAccess.open(path, FileAccess.READ)
	if file == null:
		push_error("DialogueManager: Cannot open file: " + path)
		return

	var lines: Array[DialogueLine] = []
	file.get_csv_line()  # skip header row

	while not file.eof_reached():
		var row := file.get_csv_line()
		if row.size() < 5: continue
		if row[0].is_empty() or row[0].begins_with("#"): continue

		var line := DialogueLine.new()
		line.id = row[0].strip_edges()
		line.character_id = row[1].strip_edges()
		line.emotion = row[2].strip_edges()
		line.text_zh = row[3].strip_edges()
		line.text_ja = row[4].strip_edges() if row.size() > 4 else ""
		line.safe_version = row[5].strip_edges() if row.size() > 5 else ""
		line.condition = row[6].strip_edges() if row.size() > 6 else ""
		line.interaction_type = row[7].strip_edges() if row.size() > 7 else ""

		# Handle capitolo markers
		if line.id.begins_with("CAPITOLO_"):
			line.is_capitolo = true
			line.capitolo_number = line.id.split("_")[1].to_int()
			line.capitolo_subtitle_zh = line.text_zh
			line.capitolo_subtitle_ja = line.text_ja
			line.character_id = "system"

		# Handle choice markers
		elif line.character_id == "CHOICE":
			line.is_choice = true
			line.choice_options = _parse_choice_options(line.text_zh, line.text_ja)

		lines.append(line)

	_all_loaded[path] = lines


func _parse_choice_options(text_zh: String, text_ja: String) -> Array[Dictionary]:
	var opts: Array[Dictionary] = []
	var zh_parts := text_zh.split("|")
	var ja_parts := text_ja.split("|")

	for i in zh_parts.size():
		var opt: Dictionary = {
			"id": "choice_%d" % i,
			"text_zh": zh_parts[i].strip_edges(),
			"text_ja": ja_parts[i].strip_edges() if i < ja_parts.size() else zh_parts[i].strip_edges(),
		}
		opts.append(opt)

	return opts


func _evaluate_condition(condition_str: String) -> bool:
	## Evaluates a simple condition string. Supports: empty (true), flag name, !flag, a || b.
	if condition_str.is_empty(): return true

	# Handle OR chains
	if "||" in condition_str:
		var parts := condition_str.split("||")
		for p in parts:
			if _evaluate_condition(p.strip_edges()):
				return true
		return false

	# Handle negation
	var negate := condition_str.begins_with("!")
	var flag := condition_str.trim_prefix("!")

	match flag:
		"macguffin_name_visible": return GlobalState.macguffin_name_visible != negate
		"cartridge2_completed": return GlobalState.is_cartridge_completed("cartridge2") != negate
		"cartridge1_completed": return GlobalState.is_cartridge_completed("cartridge1") != negate
		"cartridge3_completed": return GlobalState.is_cartridge_completed("cartridge3") != negate
		"all_cartridges_completed": return GlobalState.all_cartridges_completed != negate
		"cigarette_butt_seen_cartridge1": return GlobalState.cigarette_butt_seen.get("cartridge1", false) != negate
		"cigarette_butt_seen_cartridge2": return GlobalState.cigarette_butt_seen.get("cartridge2", false) != negate
		"cigarette_butt_seen_cartridge3": return GlobalState.cigarette_butt_seen.get("cartridge3", false) != negate

	push_warning("DialogueManager: Unknown condition flag: " + flag)
	return true  # unknown flags pass through


func get_character_display_name(char_id: String) -> String:
	## Returns conditional display name. MacGuffin name hidden if Cartridge 2 not yet played.
	if char_id == "macguffin" and not GlobalState.macguffin_name_visible:
		return "？？？"
	if char_id == "macguffin":
		return "麦高芬" if LanguageManager.current_language == LanguageManager.Language.CHINESE else "MacGuffin"
	if char_id == "emida":
		return "埃弥亣" if LanguageManager.current_language == LanguageManager.Language.CHINESE else "エミダー"
	if char_id == "player":
		return "你" if LanguageManager.current_language == LanguageManager.Language.CHINESE else "あなた"
	if char_id == "narrator" or char_id == "memory_text":
		return ""
	return char_id


func start_dialogue(csv_path: String) -> void:
	load_dialogue_csv(csv_path)
	_current_csv = csv_path

	var lines: Array = _all_loaded.get(csv_path, [])
	if lines.is_empty():
		push_error("DialogueManager: No dialogue loaded for: " + csv_path)
		return

	_dialogue_queue = lines
	_current_index = 0
	_is_active = true
	_advance()


func advance() -> void:
	if not _is_active: return
	_current_index += 1
	_advance()


func _advance() -> void:
	while _current_index < _dialogue_queue.size():
		var current_line: DialogueLine = _dialogue_queue[_current_index]

		# Skip capitolo markers silently (preserved for backward compatibility)
		if current_line.is_capitolo:
			_current_index += 1
			continue

		# Check condition — skip lines whose condition evaluates to false
		if not _evaluate_condition(current_line.condition):
			_current_index += 1
			continue

		break

	if _current_index >= _dialogue_queue.size():
		_is_active = false
		dialogue_ended.emit()
		return

	var line: DialogueLine = _dialogue_queue[_current_index]
	var itype := line.get_interaction_type_base()

	# Route by interaction type
	match itype:
		"keyboard_sim":
			var keystrokes: int = maxi(1, line.get_interaction_param().to_int())
			keyboard_simulation_started.emit(line.get_text(LanguageManager.current_language), keystrokes)
		"minigame_trigger":
			minigame_triggered.emit(line.get_interaction_param())
		"title_card":
			var duration := line.get_interaction_param().to_float()
			title_card_requested.emit(line.get_text(LanguageManager.current_language), duration if duration > 0.0 else 20.0)
		"credit_roll":
			credit_roll_requested.emit()
		_:
			# Standard dialogue, choice, forum_post, dream_sequence, env_switch, memory_text, red_flash
			if line.is_choice:
				choice_presented.emit(line.choice_options)
			else:
				dialogue_advanced.emit(line)


func get_current_line() -> DialogueLine:
	if _current_index < _dialogue_queue.size():
		return _dialogue_queue[_current_index]
	return null


func is_active() -> bool:
	return _is_active


func get_progress() -> float:
	if _dialogue_queue.size() == 0: return 1.0
	return float(_current_index) / float(_dialogue_queue.size())


func get_current_csv() -> String:
	return _current_csv


func get_polluted_text(line: DialogueLine) -> String:
	var raw := line.get_text(LanguageManager.current_language)
	var tier := GlobalState.get_pollution_tier()

	var effective_tier := tier
	if line.character_id in ["emida", "埃弥亣", "エミダー"]:
		if GlobalState.silence_affinity > 50:
			effective_tier = maxi(0, tier - 1)

	if line.character_id in ["wise_one", "wise_ones"]:
		return ""

	return PollutionSystem.corrupt_text(raw, effective_tier)
