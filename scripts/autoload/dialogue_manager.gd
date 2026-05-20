extends Node
## Dialogue system — parses CSV, manages dialogue queue, handles text display.

# ─── Signals ───
signal dialogue_started(line: DialogueLine)
signal dialogue_advanced(line: DialogueLine)
signal dialogue_ended()
signal choice_presented(choices: Array)

# ─── Internal state ───
var _dialogue_queue: Array[DialogueLine] = []
var _current_index: int = 0
var _is_active: bool = false
var _current_csv: String = ""
var _all_loaded: Dictionary = {}  # csv_path -> Array[DialogueLine]


# ─── DialogueLine resource ───
class DialogueLine:
	var id: String
	var character_id: String     # "emida", "macguffin", "wise_one", "narrator", etc.
	var emotion: String          # sprite variant: "neutral", "distressed", "dismissive"
	var text_zh: String
	var text_ja: String
	var safe_version: String     # unpolluted version for reference
	var is_choice: bool = false
	var choice_options: Array[Dictionary] = []  # [{id, text_zh, text_ja, flag_effect}]
	var is_capitolo: bool = false
	var capitolo_number: int = -1
	var capitolo_subtitle_zh: String = ""
	var capitolo_subtitle_ja: String = ""

	func get_text(lang: LanguageManager.Language) -> String:
		return text_zh if lang == LanguageManager.Language.CHINESE else text_ja

	func get_character_color() -> Color:
		return LanguageManager.get_color_for_character(character_id)


func load_dialogue_csv(path: String) -> void:
	## Load and parse a dialogue CSV file.
	if _all_loaded.has(path) and _all_loaded[path].size() > 0:
		return  # already loaded

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
	## Parse choice options separated by | character.
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


func start_dialogue(csv_path: String) -> void:
	## Begin a dialogue sequence from a CSV file.
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
	## Advance to the next dialogue line.
	if not _is_active: return
	_current_index += 1
	_advance()


func _advance() -> void:
	while _current_index < _dialogue_queue.size() and _dialogue_queue[_current_index].is_capitolo:
		_current_index += 1

	if _current_index >= _dialogue_queue.size():
		_is_active = false
		dialogue_ended.emit()
		return

	var line: DialogueLine = _dialogue_queue[_current_index]

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


func get_polluted_text(line: DialogueLine) -> String:
	## Returns text with pollution applied based on current pollution_level.
	var raw := line.get_text(LanguageManager.current_language)
	var tier := GlobalState.get_pollution_tier()

	# Speakers other than protagonist are always affected by global pollution
	var effective_tier := tier
	if line.character_id in ["emida", "埃弥亣", "エミダー"]:
		# Protagonist is more resistant, shown by silence_affinity
		if GlobalState.silence_affinity > 50:
			effective_tier = maxi(0, tier - 1)

	# Wise ones never speak
	if line.character_id in ["wise_one", "wise_ones"]:
		return ""

	return PollutionSystem.corrupt_text(raw, effective_tier)
