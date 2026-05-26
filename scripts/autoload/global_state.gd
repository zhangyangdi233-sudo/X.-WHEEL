extends Node
## Global game state — persists across scenes as an autoload singleton.

# ─── Core progression flags ───
var pollution_level: float = 0.0       # 0–100, language corruption
## DEPRECATED: var belief_level (kept for old save compatibility)
var belief_level: float = 0.0
## DEPRECATED: var self_awareness (kept for old save compatibility)
var self_awareness: float = 0.0
## DEPRECATED: var silence_affinity (kept for old save compatibility)
var silence_affinity: float = 0.0

# ─── Mood / visual state ───
var mood_level: float = 0.0            # 0.0–1.0, drives color grading shader
var is_glitching: bool = false
var shake_intensity: float = 0.0

# ─── Cartridge system (NEW) ───
var play_order: Array[String] = []             # e.g. ["cartridge2", "cartridge1"]
var current_cartridge: String = ""              # "" or "cartridge1"|"cartridge2"|"cartridge3"|"final"
var all_cartridges_completed: bool = false
var cigarette_butt_seen: Dictionary = {}        # cartridge_name -> bool
var macguffin_name_visible: bool = false        # true if Cartridge 2 has been played
var cartridge_progress: Dictionary = {}         # cartridge_name -> line_index
var climb_responses: int = 0                    # 0-3 tracking response count in final chapter
var memory_degradation_tier: int = 0            # 0-4 for structured degradation in final chapter

# ─── Chapter tracking (DEPRECATED) ───
## DEPRECATED: var current_chapter (kept for old save compatibility)
var current_chapter: String = ""
## DEPRECATED: var capitolo_seen (kept for old save compatibility)
var capitolo_seen: Dictionary = {}

# ─── Choice tracking (for ending logic) — DEPRECATED ───
## DEPRECATED: var choices_made (kept for old save compatibility)
var choices_made: Array[String] = []
## DEPRECATED: var chapters_completed (kept for old save compatibility)
var chapters_completed: Array[String] = []

# ─── Ether spice — DEPRECATED ───
## DEPRECATED: var ether_item (kept for old save compatibility)
var ether_item: String = ""
## DEPRECATED: var ether_sense (kept for old save compatibility)
var ether_sense: String = ""

# ─── Ending (DEPRECATED) ───
## DEPRECATED: enum Ending (kept for old save compatibility)
enum Ending { NONE, TRANSMIT, SUNSET }
## DEPRECATED: var ending_reached (kept for old save compatibility)
var ending_reached: Ending = Ending.NONE

# ─── Settings ───
var text_speed_cps: float = 30.0       # characters per second
var master_volume: float = 1.0
var bgm_volume: float = 1.0
var sfx_volume: float = 1.0


func reset_to_new_game() -> void:
	pollution_level = 0.0
	belief_level = 0.0
	self_awareness = 0.0
	silence_affinity = 0.0
	mood_level = 0.0
	is_glitching = false
	shake_intensity = 0.0
	# Cartridge system
	play_order.clear()
	current_cartridge = ""
	all_cartridges_completed = false
	cigarette_butt_seen.clear()
	macguffin_name_visible = false
	cartridge_progress.clear()
	climb_responses = 0
	memory_degradation_tier = 0
	# Deprecated
	current_chapter = ""
	capitolo_seen.clear()
	choices_made.clear()
	chapters_completed.clear()
	ether_item = ""
	ether_sense = ""
	ending_reached = Ending.NONE


# ─── Cartridge management ───

func mark_cartridge_completed(cartridge_name: String) -> void:
	if cartridge_name not in play_order:
		play_order.append(cartridge_name)
	if cartridge_name == "cartridge2":
		macguffin_name_visible = true
	all_cartridges_completed = (
		"cartridge1" in play_order and
		"cartridge2" in play_order and
		"cartridge3" in play_order
	)


func is_cartridge_completed(cartridge_name: String) -> bool:
	return cartridge_name in play_order


func has_played_cartridge2() -> bool:
	return is_cartridge_completed("cartridge2")


func get_completed_count() -> int:
	return play_order.size()


# ─── Deprecated helpers (kept for old save compatibility) ───

func add_belief(amount: float) -> void:
	belief_level = clampf(belief_level + amount, 0.0, 100.0)
	if amount > 0:
		add_pollution(amount * 0.5)


func add_self_awareness(amount: float) -> void:
	self_awareness = clampf(self_awareness + amount, 0.0, 100.0)


func add_silence_affinity(amount: float) -> void:
	silence_affinity = clampf(silence_affinity + amount, 0.0, 100.0)


func add_pollution(amount: float) -> void:
	pollution_level = clampf(pollution_level + amount, 0.0, 100.0)
	_update_mood()


func _update_mood() -> void:
	mood_level = clampf(pollution_level / 100.0, 0.0, 1.0)


func record_choice(choice_id: String) -> void:
	choices_made.append(choice_id)


func has_made_choice(choice_id: String) -> bool:
	return choice_id in choices_made


func get_pollution_tier() -> int:
	if pollution_level <= 20: return 0
	if pollution_level <= 40: return 1
	if pollution_level <= 60: return 2
	if pollution_level <= 80: return 3
	return 4


## DEPRECATED
func can_choose_transmit() -> bool:
	return belief_level >= self_awareness - 10.0


## DEPRECATED
func can_choose_silence() -> bool:
	return self_awareness >= belief_level - 10.0
