extends Node3D
## Final Chapter: ΠΑΝΗΓΥΡΙΣ — linear cinematic walk, climb, fall, credits, post-credits.

enum Phase { TITLE_CARD, BEDROOM, WALKING, TOWER_BASE, CLIMBING, TOWER_TOP, FALLING, BLOOD_MEMORY, CREDITS, POST_CREDITS, DONE }

const TITLE_DURATION := 20.0
const CLIMB_TOTAL := 6

@onready var camera: Camera3D = $FinalCamera

var _phase: Phase = Phase.TITLE_CARD
var _environments: Dictionary = {}
var _current_env: String = ""
var _ui_layer: CanvasLayer
var _dialogue_box: Control
var _transition_overlay: ColorRect
var _title_label: Label
var _forum_overlay: Control
var _forum_label: Label
var _credit_roll: Control

var _walk_targets: Array[Vector3] = []
var _walk_index := 0
var _is_walking := false
var _walk_speed := 1.6
var _climb_clicks := 0


func _ready() -> void:
	_setup_ui()
	_setup_environments()
	_connect_signals()
	_switch_environment("bedroom")
	_start_title_card()


func _setup_ui() -> void:
	_ui_layer = CanvasLayer.new()
	_ui_layer.name = "UILayer"
	add_child(_ui_layer)

	_transition_overlay = ColorRect.new()
	_transition_overlay.name = "TransitionOverlay"
	_transition_overlay.set_anchors_preset(Control.PRESET_FULL_RECT)
	_transition_overlay.color = Color.BLACK
	_transition_overlay.modulate.a = 1.0
	_transition_overlay.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_ui_layer.add_child(_transition_overlay)

	_title_label = Label.new()
	_title_label.name = "TitleLabel"
	_title_label.set_anchors_preset(Control.PRESET_FULL_RECT)
	_title_label.add_theme_font_override("font", LanguageManager.get_title_font())
	_title_label.add_theme_font_size_override("font_size", 78)
	_title_label.add_theme_color_override("font_color", Color.WHITE)
	_title_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_title_label.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	_title_label.modulate.a = 0.0
	_ui_layer.add_child(_title_label)

	var db_scene := load("res://scenes/ui/dialogue_box.tscn")
	if db_scene:
		_dialogue_box = db_scene.instantiate()
		_dialogue_box.name = "DialogueBox"
		_ui_layer.add_child(_dialogue_box)

	_create_forum_overlay()


func _create_forum_overlay() -> void:
	_forum_overlay = Control.new()
	_forum_overlay.name = "ForumOverlay"
	_forum_overlay.set_anchors_preset(Control.PRESET_FULL_RECT)
	_forum_overlay.mouse_filter = Control.MOUSE_FILTER_STOP
	_forum_overlay.modulate.a = 0.0
	_forum_overlay.hide()

	var bg := ColorRect.new()
	bg.set_anchors_preset(Control.PRESET_FULL_RECT)
	bg.color = Color(0.015, 0.018, 0.024, 0.94)
	_forum_overlay.add_child(bg)

	_forum_label = Label.new()
	_forum_label.name = "ForumText"
	_forum_label.set_anchors_preset(Control.PRESET_CENTER)
	_forum_label.offset_left = -420
	_forum_label.offset_right = 420
	_forum_label.offset_top = -120
	_forum_label.offset_bottom = 160
	_forum_label.add_theme_font_override("font", LanguageManager.get_current_font())
	_forum_label.add_theme_font_size_override("font_size", 20)
	_forum_label.add_theme_color_override("font_color", Color("3FA943"))
	_forum_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_forum_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_forum_overlay.add_child(_forum_label)

	_ui_layer.add_child(_forum_overlay)


func _connect_signals() -> void:
	DialogueManager.dialogue_advanced.connect(_on_dialogue_line)
	DialogueManager.dialogue_ended.connect(_on_dialogue_ended)
	DialogueManager.title_card_requested.connect(_on_title_card_requested)
	DialogueManager.credit_roll_requested.connect(_on_credit_roll_requested)


func _start_title_card() -> void:
	_phase = Phase.TITLE_CARD
	_title_label.text = "ΠΑΝΗΓΥΡΙΣ"
	_transition_overlay.color = Color.BLACK
	_transition_overlay.modulate.a = 1.0
	_title_label.modulate.a = 0.0
	_title_label.show()

	var tween := create_tween()
	tween.tween_interval(0.4)
	tween.tween_property(_title_label, "modulate:a", 1.0, 0.6)
	tween.tween_interval(TITLE_DURATION)
	tween.tween_property(_title_label, "modulate:a", 0.0, 0.8)
	tween.tween_property(_transition_overlay, "modulate:a", 0.0, 1.0)
	tween.tween_callback(func():
		_title_label.hide()
		_phase = Phase.BEDROOM
		GlobalState.current_cartridge = "final"
		DialogueManager.start_dialogue("res://data/dialogue/final_chapter_panegyris.csv")
	)


func _on_dialogue_line(line: DialogueManager.DialogueLine) -> void:
	var itype := line.get_interaction_type_base()
	if itype.is_empty() or itype == "dialogue" or itype == "memory_text" or itype == "keyboard_sim":
		return

	match itype:
		"env_switch":
			_switch_environment(line.get_interaction_param())
			if line.get_interaction_param() == "blood":
				_show_blood_memory()
			DialogueManager.advance()
		"forum_post":
			_show_forum_overlay(line.get_text(LanguageManager.current_language))
		"click_to_walk":
			_start_walking()
		"climb_start":
			_start_climbing()
		"red_flash":
			_do_red_flash()
		"credit_roll":
			_on_credit_roll_requested()


func _on_title_card_requested(title_text: String, duration: float) -> void:
	_title_label.text = title_text
	_transition_overlay.color = Color.BLACK
	_transition_overlay.modulate.a = 1.0
	_title_label.modulate.a = 0.0
	_title_label.show()
	var tween := create_tween()
	tween.tween_property(_title_label, "modulate:a", 1.0, 0.4)
	tween.tween_interval(duration)
	tween.tween_property(_title_label, "modulate:a", 0.0, 0.5)
	tween.tween_property(_transition_overlay, "modulate:a", 0.0, 0.6)
	tween.tween_callback(func():
		_title_label.hide()
		DialogueManager.advance()
	)


func _show_forum_overlay(text: String) -> void:
	if _forum_label:
		_forum_label.text = text
	_forum_overlay.show()
	var tween := create_tween()
	tween.tween_property(_forum_overlay, "modulate:a", 1.0, 0.2)
	tween.tween_interval(1.45)
	tween.tween_property(_forum_overlay, "modulate:a", 0.0, 0.3)
	tween.tween_callback(func():
		_forum_overlay.hide()
		DialogueManager.advance()
	)


func _start_walking() -> void:
	_phase = Phase.WALKING
	_walk_targets = [
		Vector3(0.0, 1.8, 3.2),
		Vector3(0.55, 1.8, 1.2),
		Vector3(0.8, 1.7, -1.6),
	]
	_walk_index = 0
	_is_walking = true


func _start_climbing() -> void:
	_phase = Phase.CLIMBING
	_climb_clicks = 0
	GlobalState.memory_degradation_tier = 0
	DialogueManager.advance()


func _process(delta: float) -> void:
	if not _is_walking or camera == null:
		return

	if _walk_index >= _walk_targets.size():
		_is_walking = false
		_phase = Phase.TOWER_BASE
		DialogueManager.advance()
		return

	var target := _walk_targets[_walk_index]
	var to_target := target - camera.global_position
	if to_target.length() < 0.12:
		_walk_index += 1
	else:
		camera.global_position += to_target.normalized() * _walk_speed * delta
		camera.look_at(Vector3(0, 1.2, -2.2))


func _unhandled_input(event: InputEvent) -> void:
	if _phase == Phase.CLIMBING and event is InputEventMouseButton and event.pressed and event.button_index == MOUSE_BUTTON_LEFT:
		_advance_climb()


func _advance_climb() -> void:
	_climb_clicks = mini(_climb_clicks + 1, CLIMB_TOTAL)
	GlobalState.climb_responses = _climb_clicks
	GlobalState.memory_degradation_tier = mini(4, maxi(0, _climb_clicks - 1))
	var darkness := float(_climb_clicks) / float(CLIMB_TOTAL) * 0.72
	var tween := create_tween()
	_transition_overlay.color = Color.BLACK
	tween.tween_property(_transition_overlay, "modulate:a", darkness, 0.25)


func _do_red_flash() -> void:
	var tween := create_tween()
	_transition_overlay.color = Color(0.9, 0.05, 0.02)
	_transition_overlay.modulate.a = 0.0
	tween.tween_property(_transition_overlay, "modulate:a", 0.55, 0.1)
	tween.tween_property(_transition_overlay, "modulate:a", 0.0, 0.5)
	tween.tween_callback(func():
		DialogueManager.advance()
	)


func _show_blood_memory() -> void:
	_phase = Phase.BLOOD_MEMORY
	_transition_overlay.color = Color.BLACK
	_transition_overlay.modulate.a = 0.7
	var tween := create_tween()
	tween.tween_property(_transition_overlay, "modulate:a", 0.18, 2.0)


func _on_credit_roll_requested() -> void:
	_show_credits()


func _on_dialogue_ended() -> void:
	if _phase != Phase.CREDITS and _phase != Phase.POST_CREDITS and _phase != Phase.DONE:
		_show_credits()


func _show_credits() -> void:
	_phase = Phase.CREDITS
	if _dialogue_box:
		_dialogue_box.hide()
	_transition_overlay.color = Color.BLACK
	_transition_overlay.modulate.a = 1.0

	_credit_roll = Control.new()
	_credit_roll.name = "CreditRoll"
	_credit_roll.set_anchors_preset(Control.PRESET_FULL_RECT)
	_ui_layer.add_child(_credit_roll)

	var bg := ColorRect.new()
	bg.set_anchors_preset(Control.PRESET_FULL_RECT)
	bg.color = Color.BLACK
	_credit_roll.add_child(bg)

	var lines := [
		"X. WHEEL",
		"",
		"《薯条雨&火焰&我》",
		"《晚饭吃什么》",
		"《哈吉米南北绿豆》",
		"《ΠΑΝΗΓΥΡΙΣ》",
		"",
		"一个关于梦、语言、桌面游戏机和塔的故事",
		"",
		"制作",
		"X. WHEEL",
		"",
		"字体",
		"Fusion Pixel Font",
		"",
		"引擎",
		"Godot Engine 4",
		"",
		"感谢游玩。",
	]
	var label := Label.new()
	label.name = "CreditsText"
	label.set_anchors_preset(Control.PRESET_CENTER)
	label.add_theme_font_override("font", LanguageManager.get_current_font())
	label.add_theme_font_size_override("font_size", 22)
	label.add_theme_color_override("font_color", Color("3FA943"))
	label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	label.text = "\n".join(lines)
	_credit_roll.add_child(label)

	label.position = Vector2(0, 650)
	var tween := create_tween()
	tween.tween_property(label, "position", Vector2(0, -520), 18.0)
	tween.tween_callback(func():
		_credit_roll.queue_free()
		_show_post_credits()
	)


func _show_post_credits() -> void:
	_phase = Phase.POST_CREDITS
	_switch_environment("blood")
	if _dialogue_box:
		_dialogue_box.hide()

	var double := _environments["blood"].get_node_or_null("PostCreditsDouble") as Node3D
	if double:
		double.show()

	_transition_overlay.color = Color.BLACK
	_transition_overlay.modulate.a = 1.0
	camera.global_position = Vector3(0.0, 0.65, 2.1)
	camera.look_at(Vector3(0.0, 0.1, 0.0))

	var tween := create_tween()
	tween.tween_interval(0.8)
	tween.tween_property(_transition_overlay, "modulate:a", 0.25, 2.0)
	tween.tween_method(
		func(t: float):
			camera.global_position = Vector3(0.0, lerpf(0.65, 1.9, t), lerpf(2.1, 3.0, t))
			camera.look_at(Vector3(0.0, lerpf(0.1, 1.1, t), 0.0)),
		0.0, 1.0, 3.0
	)
	tween.tween_interval(1.2)
	tween.tween_property(_transition_overlay, "modulate:a", 1.0, 0.8)
	tween.tween_callback(func():
		_phase = Phase.DONE
		get_tree().change_scene_to_file("res://scenes/main_menu.tscn")
	)


func _setup_environments() -> void:
	_create_bedroom()
	_create_street()
	_create_tower_base()
	_create_tower_top()
	_create_black()
	_create_blood()


func _switch_environment(env_name: String) -> void:
	if env_name == _current_env:
		return
	if _current_env != "" and _environments.has(_current_env):
		_environments[_current_env].hide()
	if _environments.has(env_name):
		_environments[env_name].show()
		_current_env = env_name


func _create_bedroom() -> void:
	var env := Node3D.new()
	env.name = "Env_Bedroom"
	env.add_child(_make_box(Vector3(4, 0.12, 4), Vector3(0, -0.06, 0), Color("16120F")))
	env.add_child(_make_box(Vector3(4, 2.6, 0.12), Vector3(0, 1.3, -2), Color("15100E")))
	env.add_child(_make_box(Vector3(1.7, 0.22, 1.2), Vector3(0.8, 0.18, 1.1), Color("30242A")))
	env.add_child(_make_box(Vector3(1.15, 0.16, 0.7), Vector3(-0.5, 0.75, -0.8), Color("28A9D7")))
	env.add_child(_make_box(Vector3(0.52, 0.04, 0.34), Vector3(-0.5, 0.88, -0.8), Color("08251D"), true))
	for i in 3:
		env.add_child(_make_box(Vector3(0.06, 0.025, 0.2), Vector3(1.38 + i * 0.1, 0.55, 0.82), Color("D6C692")))
	env.hide()
	add_child(env)
	_environments["bedroom"] = env


func _create_street() -> void:
	var env := Node3D.new()
	env.name = "Env_Street"
	env.add_child(_make_box(Vector3(8, 0.12, 12), Vector3(0, -0.06, -2), Color("10161A")))
	for i in 5:
		env.add_child(_make_box(Vector3(1.3, 2.2 + i * 0.35, 1.0), Vector3(-3.2, 1.1 + i * 0.18, -5 + i * 2), Color("111822")))
		env.add_child(_make_box(Vector3(1.1, 1.8 + i * 0.25, 1.0), Vector3(3.1, 0.9 + i * 0.12, -4.2 + i * 2), Color("15191F")))
	env.hide()
	add_child(env)
	_environments["street"] = env


func _create_tower_base() -> void:
	var env := Node3D.new()
	env.name = "Env_TowerBase"
	env.add_child(_make_box(Vector3(6, 0.12, 6), Vector3(0, -0.06, 0), Color("0D1117")))
	var tower := _make_cylinder(0.72, 5.0, Vector3(0, 2.5, -1.0), Color("1B2028"))
	env.add_child(tower)
	var ladder := _make_box(Vector3(0.18, 4.8, 0.08), Vector3(0, 2.45, 0.15), Color("6E3D2E"))
	env.add_child(ladder)
	env.add_child(_make_box(Vector3(0.55, 0.05, 0.12), Vector3(0, 0.62, 0.24), Color("D8D2B4")))
	env.hide()
	add_child(env)
	_environments["tower_base"] = env


func _create_tower_top() -> void:
	var env := Node3D.new()
	env.name = "Env_TowerTop"
	env.add_child(_make_box(Vector3(4.0, 0.18, 4.0), Vector3(0, -0.09, 0), Color("171B23")))
	env.add_child(_make_plane(Vector2(7.0, 3.2), Vector3(0, 1.9, -2.8), Color("E8773A"), true))
	env.add_child(_make_box(Vector3(0.28, 1.2, 0.22), Vector3(-0.45, 0.6, 0.1), Color("3FA943")))
	env.add_child(_make_box(Vector3(0.28, 1.2, 0.22), Vector3(0.45, 0.6, 0.1), Color("3FA943")))
	env.hide()
	add_child(env)
	_environments["tower_top"] = env


func _create_black() -> void:
	var env := Node3D.new()
	env.name = "Env_Black"
	env.hide()
	add_child(env)
	_environments["black"] = env


func _create_blood() -> void:
	var env := Node3D.new()
	env.name = "Env_Blood"
	env.add_child(_make_box(Vector3(5.0, 0.08, 5.0), Vector3(0, -0.04, 0), Color("090909")))
	env.add_child(_make_plane(Vector2(1.55, 0.95), Vector3(0, 0.012, 0), Color("6A0505"), true))
	env.add_child(_make_box(Vector3(0.34, 0.14, 0.9), Vector3(0, 0.12, 0.1), Color("263D35")))
	var double := Node3D.new()
	double.name = "PostCreditsDouble"
	double.position = Vector3(0.0, 0.0, -0.65)
	double.hide()
	double.add_child(_make_box(Vector3(0.28, 1.0, 0.22), Vector3(0, 0.58, 0), Color("3FA943")))
	double.add_child(_make_box(Vector3(0.28, 0.28, 0.28), Vector3(0, 1.22, 0), Color("3FA943")))
	env.add_child(double)
	env.hide()
	add_child(env)
	_environments["blood"] = env


func _make_box(size: Vector3, pos: Vector3, color: Color, unshaded: bool = false) -> MeshInstance3D:
	var mesh := BoxMesh.new()
	mesh.size = size
	var node := MeshInstance3D.new()
	node.mesh = mesh
	node.position = pos
	node.material_override = _make_mat(color, unshaded)
	return node


func _make_cylinder(radius: float, height: float, pos: Vector3, color: Color) -> MeshInstance3D:
	var mesh := CylinderMesh.new()
	mesh.top_radius = radius
	mesh.bottom_radius = radius
	mesh.height = height
	mesh.radial_segments = 8
	var node := MeshInstance3D.new()
	node.mesh = mesh
	node.position = pos
	node.material_override = _make_mat(color)
	return node


func _make_plane(size: Vector2, pos: Vector3, color: Color, unshaded: bool = false) -> MeshInstance3D:
	var mesh := PlaneMesh.new()
	mesh.size = size
	var node := MeshInstance3D.new()
	node.mesh = mesh
	node.position = pos
	node.rotation_degrees.x = 90.0
	node.material_override = _make_mat(color, unshaded)
	return node


func _make_mat(color: Color, unshaded: bool = false) -> StandardMaterial3D:
	var mat := StandardMaterial3D.new()
	mat.albedo_color = color
	if unshaded:
		mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
		mat.emission = color
		mat.emission_energy = 0.45
	return mat
