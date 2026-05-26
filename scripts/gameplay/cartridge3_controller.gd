extends CartridgeBaseController
## Cartridge 3: 《哈吉米南北绿豆》 — forum posts, cinema, Hajimi, connecting threads.

var _environments: Dictionary = {}
var _current_env: String = ""
var _cigarette_butt_mesh: MeshInstance3D


func _ready() -> void:
	cartridge_name = "cartridge3"
	dialogue_csv = "res://data/dialogue/cartridge3_hajimi.csv"
	super._ready()


func _setup_environment() -> void:
	_create_bedroom()
	_create_computer_room()
	_create_cinema()
	_switch_environment("bedroom")


func _on_cartridge_start() -> void:
	_has_cigarette_butt = true
	GlobalState.cartridge_progress[cartridge_name] = 0


func _handle_interaction_type(itype: String, data: Dictionary) -> void:
	match itype:
		"forum_post":
			_show_forum_overlay(data)
		"dream_sequence":
			_do_dream_sequence()
		"red_flash":
			_do_red_flash()
		"env_switch":
			_switch_environment(data.get("env", ""))
		_:
			super._handle_interaction_type(itype, data)


# ─── Forum overlay ───

func _create_forum_overlay() -> void:
	if not _ui_layer: return
	_forum_overlay = Control.new()
	_forum_overlay.name = "ForumOverlay"
	_forum_overlay.set_anchors_preset(Control.PRESET_FULL_RECT)
	_forum_overlay.modulate.a = 0.0
	_forum_overlay.mouse_filter = Control.MOUSE_FILTER_IGNORE

	var bg := ColorRect.new()
	bg.name = "ForumBG"
	bg.set_anchors_preset(Control.PRESET_FULL_RECT)
	bg.color = Color(0.05, 0.06, 0.08, 0.9)
	_forum_overlay.add_child(bg)

	var label := Label.new()
	label.name = "ForumText"
	label.set_anchors_preset(Control.PRESET_CENTER)
	label.add_theme_font_override("font", LanguageManager.get_current_font())
	label.add_theme_font_size_override("font_size", 14)
	label.add_theme_color_override("font_color", Color("35A146"))
	label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_forum_overlay.add_child(label)
	_forum_label = label

	_forum_overlay.hide()
	_ui_layer.add_child(_forum_overlay)


func _show_forum_overlay(data: Dictionary) -> void:
	if not _forum_overlay:
		DialogueManager.advance()
		return
	var text: String = data.get("text", "")
	var label := _forum_overlay.get_node_or_null("ForumText") as Label
	if label:
		label.text = "【南北绿豆 BBS】\n\n" + text

	_forum_overlay.show()
	var tween := create_tween()
	tween.tween_property(_forum_overlay, "modulate:a", 1.0, 0.3)
	tween.tween_interval(0.5)
	tween.tween_property(_forum_overlay, "modulate:a", 0.0, 0.3)
	tween.tween_callback(func():
		_forum_overlay.hide()
		DialogueManager.advance()
	)


# ─── Environments ───

func _create_bedroom() -> void:
	var env := Node3D.new()
	env.name = "Env_Bedroom"
	env.add_child(_make_box(Vector3(4, 0.1, 4), Vector3(0, -0.05, 0), Color(0.12, 0.1, 0.08)))
	env.add_child(_make_box(Vector3(4, 2.5, 0.1), Vector3(0, 1.25, -2), Color(0.1, 0.08, 0.07)))
	env.add_child(_make_box(Vector3(1.8, 0.3, 2.0), Vector3(0.5, 0.1, 1.2), Color(0.15, 0.12, 0.1)))
	env.add_child(_make_box(Vector3(0.4, 0.5, 0.4), Vector3(1.2, 0.25, 0.8), Color(0.18, 0.13, 0.09)))
	env.add_child(_make_box(Vector3(0.12, 0.04, 0.12), Vector3(1.2, 0.52, 0.8), Color(0.3, 0.3, 0.3)))
	_cigarette_butt_mesh = _make_box(Vector3(0.02, 0.01, 0.06), Vector3(1.2, 0.54, 0.8), Color(0.9, 0.85, 0.7))
	_cigarette_butt_mesh.visible = false
	env.add_child(_cigarette_butt_mesh)
	env.hide(); add_child(env)
	_environments["bedroom"] = env


func _create_computer_room() -> void:
	var env := Node3D.new()
	env.name = "Env_ComputerRoom"
	env.add_child(_make_box(Vector3(4, 0.1, 3), Vector3(0, -0.05, 0), Color(0.08, 0.08, 0.1)))
	env.add_child(_make_box(Vector3(0.1, 2.5, 3), Vector3(-2, 1.25, 0), Color(0.06, 0.06, 0.08)))
	env.add_child(_make_box(Vector3(0.8, 0.7, 0.6), Vector3(0, 0.8, -0.5), Color(0.1, 0.1, 0.1)))
	var screen := _make_plane(Vector2(0.6, 0.5), Vector3(0, 0.8, -0.19), Color("35A146"))
	var screen_mat := StandardMaterial3D.new()
	screen_mat.albedo_color = Color("35A146")
	screen_mat.emission = Color("3FA943")
	screen_mat.emission_energy = 0.3
	screen.material_override = screen_mat
	env.add_child(screen)
	env.add_child(_make_box(Vector3(1.2, 0.05, 0.6), Vector3(0, 0.45, -0.3), Color(0.2, 0.18, 0.13)))
	env.hide(); add_child(env)
	_environments["computer_room"] = env


func _create_cinema() -> void:
	var env := Node3D.new()
	env.name = "Env_Cinema"
	# Dark theater floor
	env.add_child(_make_box(Vector3(5, 0.1, 6), Vector3(0, -0.05, 0), Color(0.06, 0.04, 0.04)))
	# Screen (large glowing plane)
	var screen := _make_plane(Vector2(4, 2.2), Vector3(0, 2, -3), Color(0.9, 0.85, 0.8))
	var screen_mat := StandardMaterial3D.new()
	screen_mat.albedo_color = Color(0.15, 0.15, 0.2)
	screen_mat.emission = Color(0.2, 0.2, 0.25)
	screen_mat.emission_energy = 0.4
	screen.material_override = screen_mat
	env.add_child(screen)
	# Red velvet seats (rows of boxes)
	for row in 3:
		for col in 3:
			var seat := _make_box(Vector3(0.5, 0.4, 0.5), Vector3(-1.0 + col * 1.0, 0.2, 0.5 + row * 1.2), Color(0.5, 0.08, 0.08))
			env.add_child(seat)
	env.hide(); add_child(env)
	_environments["cinema"] = env


func _switch_environment(env_name: String) -> void:
	if env_name == _current_env: return
	if _current_env != "" and _environments.has(_current_env):
		_environments[_current_env].hide()
	if _environments.has(env_name):
		_environments[env_name].show()
		_current_env = env_name
		if env_name == "bedroom" and _cigarette_butt_mesh:
			_cigarette_butt_mesh.visible = true


func _do_dream_sequence() -> void:
	if not _mood_overlay: return
	var mat: ShaderMaterial = _mood_overlay.material
	if not mat: return
	var tween := create_tween()
	tween.tween_method(func(v: float): mat.set_shader_parameter("mood_level", v), 0.0, 0.5, 1.0)
	tween.tween_interval(0.5)
	tween.tween_method(func(v: float): mat.set_shader_parameter("mood_level", v), 0.5, 0.0, 1.0)


func _do_red_flash() -> void:
	if not _transition_overlay: return
	var tween := create_tween()
	_transition_overlay.modulate = Color(1, 0.15, 0.05, 0.0)
	tween.tween_property(_transition_overlay, "modulate:a", 0.4, 0.15)
	tween.tween_property(_transition_overlay, "modulate:a", 0.0, 0.5)


func _make_box(size: Vector3, pos: Vector3, color: Color) -> MeshInstance3D:
	var mesh := BoxMesh.new(); mesh.size = size
	var node := MeshInstance3D.new(); node.mesh = mesh; node.position = pos
	var mat := StandardMaterial3D.new(); mat.albedo_color = color
	node.material_override = mat
	return node


func _make_plane(size: Vector2, pos: Vector3, color: Color) -> MeshInstance3D:
	var mesh := PlaneMesh.new(); mesh.size = size
	var node := MeshInstance3D.new(); node.mesh = mesh; node.position = pos
	var mat := StandardMaterial3D.new(); mat.albedo_color = color
	mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	node.material_override = mat
	return node
