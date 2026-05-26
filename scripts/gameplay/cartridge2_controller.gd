extends CartridgeBaseController
## Cartridge 2: 《晚饭吃什么》 — keyboard sim, fridge minigame, MacGuffin intro.

var _environments: Dictionary = {}
var _current_env: String = ""
var _cigarette_butt_mesh: MeshInstance3D

# ─── Fridge minigame state ───
var _fridge_clicks: int = 0
const FRIDGE_MAX_CLICKS := 10
var _fridge_active: bool = false
var _fridge_overlay: Control
var _fridge_status_label: Label
var _fridge_first_clothes_click: bool = true


func _ready() -> void:
	cartridge_name = "cartridge2"
	dialogue_csv = "res://data/dialogue/cartridge2_dinner.csv"
	super._ready()


func _setup_environment() -> void:
	_create_bedroom()
	_create_kitchen()
	_create_convenience_store()
	_create_black()
	_create_fridge_minigame_ui()
	_switch_environment("bedroom")


func _on_cartridge_start() -> void:
	_has_cigarette_butt = true
	GlobalState.cartridge_progress[cartridge_name] = 0


func _on_cartridge_complete() -> void:
	# Setting macguffin_name_visible is handled by GlobalState.mark_cartridge_completed
	pass


func _handle_interaction_type(itype: String, data: Dictionary) -> void:
	match itype:
		"keyboard_sim":
			pass  # handled by DialogueBox signal -> connected in base
		"minigame", "minigame_trigger":
			if data.get("name", "") == "fridge":
				_start_fridge_minigame()
		"red_flash":
			_do_red_flash()
		"env_switch":
			_switch_environment(data.get("env", ""))
		"dream_sequence":
			_do_dream_sequence()
		_:
			super._handle_interaction_type(itype, data)


# ─── Fridge minigame ───

func _start_fridge_minigame() -> void:
	_fridge_active = true
	_fridge_clicks = 0
	_fridge_first_clothes_click = true
	if _fridge_overlay:
		_fridge_overlay.show()
		_fridge_overlay.modulate.a = 0.0
		var tween := create_tween()
		tween.tween_property(_fridge_overlay, "modulate:a", 1.0, 0.25)
	_update_fridge_status("冰箱里好像什么都有。除了晚饭。")


func _create_fridge_minigame_ui() -> void:
	if not _ui_layer:
		return
	_fridge_overlay = Control.new()
	_fridge_overlay.name = "FridgeOverlay"
	_fridge_overlay.set_anchors_preset(Control.PRESET_FULL_RECT)
	_fridge_overlay.mouse_filter = Control.MOUSE_FILTER_STOP
	_fridge_overlay.hide()

	var bg := ColorRect.new()
	bg.name = "FridgeBG"
	bg.set_anchors_preset(Control.PRESET_FULL_RECT)
	bg.color = Color(0.02, 0.035, 0.04, 0.92)
	_fridge_overlay.add_child(bg)

	var title := Label.new()
	title.name = "FridgeTitle"
	title.text = "冰箱"
	title.set_anchors_preset(Control.PRESET_TOP_WIDE)
	title.offset_top = 72
	title.add_theme_font_override("font", LanguageManager.get_current_font())
	title.add_theme_font_size_override("font_size", 34)
	title.add_theme_color_override("font_color", Color("E8F8E5"))
	title.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_fridge_overlay.add_child(title)

	_fridge_status_label = Label.new()
	_fridge_status_label.name = "FridgeStatus"
	_fridge_status_label.set_anchors_preset(Control.PRESET_TOP_WIDE)
	_fridge_status_label.offset_top = 128
	_fridge_status_label.add_theme_font_override("font", LanguageManager.get_current_font())
	_fridge_status_label.add_theme_font_size_override("font_size", 20)
	_fridge_status_label.add_theme_color_override("font_color", Color("3FA943"))
	_fridge_status_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_fridge_overlay.add_child(_fridge_status_label)

	var grid := GridContainer.new()
	grid.name = "FridgeGrid"
	grid.columns = 2
	grid.anchor_left = 0.5
	grid.anchor_right = 0.5
	grid.anchor_top = 0.5
	grid.anchor_bottom = 0.5
	grid.offset_left = -280
	grid.offset_right = 280
	grid.offset_top = -130
	grid.offset_bottom = 190
	grid.add_theme_constant_override("h_separation", 24)
	grid.add_theme_constant_override("v_separation", 24)
	_fridge_overlay.add_child(grid)

	var items := [
		{"id": "can", "text": "空罐子"},
		{"id": "clothes", "text": "衣服"},
		{"id": "fruit", "text": "发霉水果"},
		{"id": "milk", "text": "开封牛奶盒"},
	]
	for item in items:
		var btn := Button.new()
		btn.custom_minimum_size = Vector2(250, 92)
		btn.text = item["text"]
		btn.add_theme_font_override("font", LanguageManager.get_current_font())
		btn.add_theme_font_size_override("font_size", 20)
		btn.add_theme_color_override("font_color", Color("E8F8E5"))
		btn.add_theme_color_override("font_hover_color", Color("3FA943"))
		btn.pressed.connect(_on_fridge_item_clicked.bind(item["id"], item["text"]))
		grid.add_child(btn)

	_ui_layer.add_child(_fridge_overlay)


func _on_fridge_item_clicked(item_id: String, item_text: String) -> void:
	if not _fridge_active:
		return
	_fridge_clicks += 1

	if item_id == "clothes" and _fridge_first_clothes_click:
		_fridge_first_clothes_click = false
		_update_fridge_status("谁会把衣服放进冰箱里面啊。")
	elif item_id == "milk":
		_update_fridge_status("闻起来像很久以前的星期二。")
	elif item_id == "fruit":
		_update_fridge_status("它已经有自己的生态系统了。")
	else:
		_update_fridge_status("%s不能当晚饭。%d/%d" % [item_text, _fridge_clicks, FRIDGE_MAX_CLICKS])

	if _fridge_clicks >= FRIDGE_MAX_CLICKS:
		_finish_fridge_minigame()


func _update_fridge_status(text: String) -> void:
	if _fridge_status_label:
		_fridge_status_label.text = text


func _finish_fridge_minigame() -> void:
	_fridge_active = false
	_update_fridge_status(LanguageManager.t("fridge_empty"))
	var tween := create_tween()
	tween.tween_interval(0.6)
	if _fridge_overlay:
		tween.tween_property(_fridge_overlay, "modulate:a", 0.0, 0.35)
		tween.tween_callback(_fridge_overlay.hide)
	tween.tween_callback(func():
		DialogueManager.advance()
	)


func _process(_delta: float) -> void:
	if not _fridge_active: return
	# Fridge minigame input handled via _unhandled_input


func _unhandled_input(event: InputEvent) -> void:
	if not _fridge_active: return
	if event is InputEventMouseButton and event.pressed and event.button_index == MOUSE_BUTTON_LEFT:
		# Overlay buttons own the minigame clicks.
		get_viewport().set_input_as_handled()


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


func _create_kitchen() -> void:
	var env := Node3D.new()
	env.name = "Env_Kitchen"
	env.add_child(_make_box(Vector3(3, 0.1, 3), Vector3(0, -0.05, 0), Color(0.18, 0.17, 0.15)))
	env.add_child(_make_box(Vector3(0.1, 2.5, 3), Vector3(-1.5, 1.25, 0), Color(0.16, 0.14, 0.12)))
	# Counter
	env.add_child(_make_box(Vector3(1.5, 0.9, 0.6), Vector3(0.5, 0.5, -0.3), Color(0.35, 0.32, 0.28)))
	# Fridge (tall box)
	var fridge := _make_box(Vector3(0.7, 1.8, 0.65), Vector3(-0.8, 0.9, -0.8), Color(0.85, 0.83, 0.8))
	env.add_child(fridge)
	# Window
	env.add_child(_make_plane(Vector2(0.8, 0.6), Vector3(0, 1.5, -1.45), Color("0C1725")))
	env.hide(); add_child(env)
	_environments["kitchen"] = env


func _create_convenience_store() -> void:
	var env := Node3D.new()
	env.name = "Env_ConvenienceStore"
	# Bright fluorescent floor
	env.add_child(_make_box(Vector3(3, 0.1, 4), Vector3(0, -0.05, 0), Color(0.25, 0.25, 0.23)))
	# Shelves
	for i in 2:
		env.add_child(_make_box(Vector3(0.3, 1.8, 3), Vector3(-0.8 + i * 1.6, 0.9, 0), Color(0.35, 0.33, 0.3)))
	# Window (looking out to dark street)
	var window_mat := StandardMaterial3D.new()
	window_mat.albedo_color = Color(0.08, 0.1, 0.15)
	window_mat.emission = Color(0.12, 0.15, 0.18)
	window_mat.emission_energy = 0.2
	var window := _make_plane(Vector2(2, 1.2), Vector3(0, 1.2, -1.9), Color.WHITE)
	window.material_override = window_mat
	env.add_child(window)
	# MacGuffinFigure: low-poly street messenger outside the bright store window.
	var mac_body := _make_box(Vector3(0.28, 0.8, 0.22), Vector3(-1.55, 0.45, -1.75), Color("27313A"))
	mac_body.name = "MacGuffinFigure"
	env.add_child(mac_body)
	var mac_head := _make_box(Vector3(0.24, 0.24, 0.24), Vector3(-1.55, 0.98, -1.75), Color("D8C2A5"))
	mac_head.name = "MacGuffinHead"
	env.add_child(mac_head)
	var cigarette := _make_box(Vector3(0.18, 0.025, 0.025), Vector3(-1.31, 0.98, -1.72), Color("F2E1B3"))
	cigarette.name = "MacGuffinCigarette"
	env.add_child(cigarette)
	env.hide(); add_child(env)
	_environments["convenience_store"] = env


func _create_black() -> void:
	var env := Node3D.new()
	env.name = "Env_Black"
	env.add_child(_make_box(Vector3(0.1, 0.1, 0.1), Vector3(0, -10, 0), Color.BLACK))
	env.hide(); add_child(env)
	_environments["black"] = env


func _switch_environment(env_name: String) -> void:
	if env_name == _current_env: return
	if _current_env != "" and _environments.has(_current_env):
		_environments[_current_env].hide()
	if _environments.has(env_name):
		_environments[env_name].show()
		_current_env = env_name
		if env_name == "bedroom" and _cigarette_butt_mesh:
			_cigarette_butt_mesh.visible = true


func _do_red_flash() -> void:
	if not _transition_overlay: return
	var tween := create_tween()
	_transition_overlay.modulate = Color(1, 0.15, 0.05, 0.0)
	tween.tween_property(_transition_overlay, "modulate:a", 0.6, 0.15)
	tween.tween_property(_transition_overlay, "modulate:a", 0.0, 0.8)


func _do_dream_sequence() -> void:
	if not _mood_overlay: return
	var mat: ShaderMaterial = _mood_overlay.material
	if not mat: return
	var tween := create_tween()
	tween.tween_method(func(v: float): mat.set_shader_parameter("mood_level", v), 0.0, 0.5, 1.0)
	tween.tween_interval(0.5)
	tween.tween_method(func(v: float): mat.set_shader_parameter("mood_level", v), 0.5, 0.0, 1.0)


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
