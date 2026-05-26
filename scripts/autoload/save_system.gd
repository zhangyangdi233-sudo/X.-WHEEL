extends Node
## Save/load system using Godot ConfigFile. Version 2 — cartridge-aware.

const SAVE_DIR := "user://saves/"
const SAVE_EXT := ".cfg"
const MAX_SLOTS := 20
const SAVE_VERSION := 2


func _ready() -> void:
	DirAccess.make_dir_recursive_absolute(SAVE_DIR)


func save_game(slot: int) -> bool:
	if slot < 0 or slot >= MAX_SLOTS: return false

	var cfg := ConfigFile.new()
	cfg.set_value("meta", "version", SAVE_VERSION)
	cfg.set_value("meta", "timestamp", Time.get_datetime_string_from_system())
	cfg.set_value("meta", "scene", GlobalState.current_cartridge)

	# Persist all game state
	cfg.set_value("state", "pollution_level", GlobalState.pollution_level)
	cfg.set_value("state", "mood_level", GlobalState.mood_level)
	# Deprecated fields — still saved for old save compatibility
	cfg.set_value("state", "belief_level", GlobalState.belief_level)
	cfg.set_value("state", "self_awareness", GlobalState.self_awareness)
	cfg.set_value("state", "silence_affinity", GlobalState.silence_affinity)
	cfg.set_value("state", "choices_made", GlobalState.choices_made)
	cfg.set_value("state", "chapters_completed", GlobalState.chapters_completed)
	cfg.set_value("state", "capitolo_seen", GlobalState.capitolo_seen)
	cfg.set_value("state", "ether_item", GlobalState.ether_item)
	cfg.set_value("state", "ether_sense", GlobalState.ether_sense)
	cfg.set_value("state", "ending_reached", GlobalState.ending_reached)

	# New cartridge state
	cfg.set_value("cartridge", "play_order", ",".join(GlobalState.play_order))
	cfg.set_value("cartridge", "all_cartridges_completed", GlobalState.all_cartridges_completed)
	cfg.set_value("cartridge", "cigarette_butt_seen", var_to_str(GlobalState.cigarette_butt_seen))
	cfg.set_value("cartridge", "macguffin_name_visible", GlobalState.macguffin_name_visible)
	cfg.set_value("cartridge", "cartridge_progress", var_to_str(GlobalState.cartridge_progress))
	cfg.set_value("cartridge", "climb_responses", GlobalState.climb_responses)
	cfg.set_value("cartridge", "memory_degradation_tier", GlobalState.memory_degradation_tier)

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

	var version: int = cfg.get_value("meta", "version", 1)

	# Deprecated fields — always load for backward compatibility
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

	# New fields — load with defaults for old saves
	if version >= 2:
		var po_str: String = cfg.get_value("cartridge", "play_order", "")
		GlobalState.play_order.clear()
		if not po_str.is_empty():
			for cart in po_str.split(","):
				var cart_name := str(cart).strip_edges()
				if not cart_name.is_empty():
					GlobalState.play_order.append(cart_name)
		GlobalState.all_cartridges_completed = cfg.get_value("cartridge", "all_cartridges_completed", false)
		GlobalState.macguffin_name_visible = cfg.get_value("cartridge", "macguffin_name_visible", false)
		GlobalState.climb_responses = cfg.get_value("cartridge", "climb_responses", 0)
		GlobalState.memory_degradation_tier = cfg.get_value("cartridge", "memory_degradation_tier", 0)
		# Deserialize dictionaries from string
		var cbs_str: String = cfg.get_value("cartridge", "cigarette_butt_seen", "{}")
		GlobalState.cigarette_butt_seen = str_to_var(cbs_str) if not cbs_str.is_empty() else {}
		var cp_str: String = cfg.get_value("cartridge", "cartridge_progress", "{}")
		GlobalState.cartridge_progress = str_to_var(cp_str) if not cp_str.is_empty() else {}

	return true


func slot_exists(slot: int) -> bool:
	return FileAccess.file_exists(_slot_path(slot))


func get_slot_info(slot: int) -> Dictionary:
	if not slot_exists(slot): return {"empty": true}

	var cfg := ConfigFile.new()
	cfg.load(_slot_path(slot))
	var version: int = cfg.get_value("meta", "version", 1)
	var cartridges_completed: int = 0
	if version >= 2:
		var po_str: String = cfg.get_value("cartridge", "play_order", "")
		cartridges_completed = po_str.split(",").size() if not po_str.is_empty() else 0

	return {
		"empty": false,
		"timestamp": cfg.get_value("meta", "timestamp", ""),
		"scene": cfg.get_value("meta", "scene", cfg.get_value("meta", "chapter", "")),
		"cartridges_completed": cartridges_completed,
	}


func delete_slot(slot: int) -> void:
	var path := _slot_path(slot)
	if FileAccess.file_exists(path):
		DirAccess.remove_absolute(path)


func get_latest_save() -> int:
	## Returns the slot number of the most recent save, or -1 if none exist.
	var latest_slot := -1
	var latest_time := ""
	for i in MAX_SLOTS:
		if slot_exists(i):
			var info := get_slot_info(i)
			if info.get("timestamp", "") > latest_time:
				latest_time = info["timestamp"]
				latest_slot = i
	return latest_slot


func _slot_path(slot: int) -> String:
	return SAVE_DIR + "save_" + str(slot).pad_zeros(2) + SAVE_EXT
