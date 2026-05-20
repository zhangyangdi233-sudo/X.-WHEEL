extends Node
## Global game state — persists across scenes as an autoload singleton.

# ─── Core progression flags ───
var pollution_level: float = 0.0       # 0–100, language corruption
var belief_level: float = 0.0          # 0–100, faith in urban legends / the signal
var self_awareness: float = 0.0        # 0–100, questioning her nature as Y2K
var silence_affinity: float = 0.0      # 0–100, closeness to the Wise One path

# ─── Mood / visual state ───
var mood_level: float = 0.0            # 0.0–1.0, drives color grading shader
var is_glitching: bool = false
var shake_intensity: float = 0.0

# ─── Chapter tracking ───
var current_chapter: String = ""
var capitolo_seen: Dictionary = {}     # capitolo_name -> bool

# ─── Choice tracking (for ending logic) ───
var choices_made: Array[String] = []
var chapters_completed: Array[String] = []

# ─── Ether spice — currently held item ───
var ether_item: String = ""
var ether_sense: String = ""

# ─── Ending ───
enum Ending { NONE, TRANSMIT, SUNSET }
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
	current_chapter = ""
	capitolo_seen.clear()
	choices_made.clear()
	chapters_completed.clear()
	ether_item = ""
	ether_sense = ""
	ending_reached = Ending.NONE


func add_belief(amount: float) -> void:
	belief_level = clampf(belief_level + amount, 0.0, 100.0)
	if amount > 0:
		add_pollution(amount * 0.5)  # believing accelerates pollution


func add_self_awareness(amount: float) -> void:
	self_awareness = clampf(self_awareness + amount, 0.0, 100.0)


func add_silence_affinity(amount: float) -> void:
	silence_affinity = clampf(silence_affinity + amount, 0.0, 100.0)


func add_pollution(amount: float) -> void:
	pollution_level = clampf(pollution_level + amount, 0.0, 100.0)
	_update_mood()


func _update_mood() -> void:
	# mood_level tracks pollution + chapter progression
	mood_level = clampf(pollution_level / 100.0, 0.0, 1.0)


func record_choice(choice_id: String) -> void:
	choices_made.append(choice_id)


func has_made_choice(choice_id: String) -> bool:
	return choice_id in choices_made


func get_pollution_tier() -> int:
	## Returns 0–4 representing the pollution tier.
	if pollution_level <= 20: return 0
	if pollution_level <= 40: return 1
	if pollution_level <= 60: return 2
	if pollution_level <= 80: return 3
	return 4


func can_choose_transmit() -> bool:
	return belief_level >= self_awareness - 10.0  # close or belief > awareness


func can_choose_silence() -> bool:
	return self_awareness >= belief_level - 10.0  # close or awareness > belief
