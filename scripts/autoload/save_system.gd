extends Node
## Save/load system using Godot ConfigFile.

const SAVE_DIR := "user://saves/"
const SAVE_EXT := ".cfg"
const MAX_SLOTS := 20


func _ready() -> void:
	DirAccess.make_dir_recursive_absolute(SAVE_DIR)


func save_game(slot: int) -> bool:
	if slot < 0 or slot >= MAX_SLOTS: return false

	var cfg := ConfigFile.new()
	cfg.set_value("meta", "timestamp", Time.get_datetime_string_from_system())
	cfg.set_value("meta", "chapter", GlobalState.current_chapter)

	# Persist all game state
	cfg.set_value("state", "pollution_level", GlobalState.pollution_level)
	cfg.set_value("state", "belief_level", GlobalState.belief_level)
	cfg.set_value("state", "self_awareness", GlobalState.self_awareness)
	cfg.set_value("state", "silence_affinity", GlobalState.silence_affinity)
	cfg.set_value("state", "mood_level", GlobalState.mood_level)
	cfg.set_value("state", "choices_made", GlobalState.choices_made)
	cfg.set_value("state", "chapters_completed", GlobalState.chapters_completed)
	cfg.set_value("state", "capitolo_seen", GlobalState.capitolo_seen)
	cfg.set_value("state", "ether_item", GlobalState.ether_item)
	cfg.set_value("state", "ether_sense", GlobalState.ether_sense)
	cfg.set_value("state", "ending_reached", GlobalState.ending_reached)
	cfg.set_value("settings", "text_speed", GlobalState.text_speed_cps)
	cfg.set_value("settings", "language", LanguageManager.current_language)

	var path := _slot_path(slot)
	var err := cfg.save(path)
	return err == OK


func load_game(slot: int) -> bool:
	if slot < 0 or slot >= MAX_SLOTS: return false

	var path := _slot_path(slot)
	if not FileAccess.file_exists(path): return false

	var cfg := ConfigFile.new()
	var err := cfg.load(path)
	if err != OK: return false

	GlobalState.reset_to_new_game()

	GlobalState.current_chapter = str(cfg.get_value("meta", "chapter", ""))
	GlobalState.pollution_level = float(cfg.get_value("state", "pollution_level", 0.0))
	GlobalState.belief_level = float(cfg.get_value("state", "belief_level", 0.0))
	GlobalState.self_awareness = float(cfg.get_value("state", "self_awareness", 0.0))
	GlobalState.silence_affinity = float(cfg.get_value("state", "silence_affinity", 0.0))
	GlobalState.mood_level = float(cfg.get_value("state", "mood_level", 0.0))
	GlobalState.choices_made = cfg.get_value("state", "choices_made", [])
	GlobalState.chapters_completed = cfg.get_value("state", "chapters_completed", [])
	GlobalState.capitolo_seen = cfg.get_value("state", "capitolo_seen", {})
	GlobalState.ether_item = str(cfg.get_value("state", "ether_item", ""))
	GlobalState.ether_sense = str(cfg.get_value("state", "ether_sense", ""))
	GlobalState.ending_reached = cfg.get_value("state", "ending_reached", 0)
	GlobalState.text_speed_cps = float(cfg.get_value("settings", "text_speed", 30.0))
	LanguageManager.apply_language(cfg.get_value("settings", "language", 0))

	return true


func slot_exists(slot: int) -> bool:
	return FileAccess.file_exists(_slot_path(slot))


func get_slot_info(slot: int) -> Dictionary:
	if not slot_exists(slot): return {"empty": true}

	var cfg := ConfigFile.new()
	cfg.load(_slot_path(slot))
	return {
		"empty": false,
		"timestamp": cfg.get_value("meta", "timestamp", ""),
		"chapter": cfg.get_value("meta", "chapter", ""),
	}


func delete_slot(slot: int) -> void:
	var path := _slot_path(slot)
	if FileAccess.file_exists(path):
		DirAccess.remove_absolute(path)


func _slot_path(slot: int) -> String:
	return SAVE_DIR + "save_" + str(slot).pad_zeros(2) + SAVE_EXT
