extends Node3D
## Main menu scene controller — CRT room with orbiting 3D camera.
## Supports zoom-to-desk transition for cartridge selection.

@onready var camera: Camera3D = %MenuCamera
@onready var crt_screen: MeshInstance3D = %CRTScreen
@onready var emida_sprite: Sprite3D = %EmidaSprite
@onready var room: Node3D = %Room

# UI
@onready var title_label: Label = %TitleLabel
@onready var menu_buttons: VBoxContainer = %MenuButtons
@onready var language_btn: Button = %LanguageBtn
@onready var version_label: Label = %VersionLabel

var _orbit_angle: float = 0.0
var _orbit_speed: float = 0.003  # rad/s — very slow
var _orbit_radius: float = 6.0
var _orbit_center: Vector3 = Vector3(0, 1.5, 0)
var _orbit_amplitude: float = 60.0  # degree span

var _is_zooming: bool = false
# Desk camera target — looking down at the desk/console from a low angle
const DESK_CAM_POS := Vector3(0, 1.8, 4.0)
const DESK_CAM_LOOK := Vector3(0, 1.3, -1.5)
const MENU_BGM: AudioStream = preload("res://snd/main_menu_dreamcore_loop.wav")
const START_GAME_TRANSITION: AudioStream = preload("res://snd/start_to_cartridge_transition.wav")


func _ready() -> void:
	_create_low_poly_bedroom()
	_setup_ui()
	_connect_buttons()
	_setup_crt()
	_start_menu_bgm()
	_apply_language()

	# Continue button — show if any save exists or cartridges have been played
	if menu_buttons and (not GlobalState.play_order.is_empty() or SaveSystem.get_latest_save() >= 0):
		var continue_btn := Button.new()
		continue_btn.text = LanguageManager.t("continue")
		continue_btn.add_theme_font_override("font", LanguageManager.get_current_font())
		continue_btn.pressed.connect(_on_continue_pressed)
		menu_buttons.add_child(continue_btn)
		menu_buttons.move_child(continue_btn, 0)


func _create_low_poly_bedroom() -> void:
	# Low-poly bedroom shell.
	_make_box("Floor", Vector3(8.0, 0.18, 8.0), Vector3(0, -0.09, 0), Color("07101A"))
	_make_box("BackWall", Vector3(8.0, 4.0, 0.18), Vector3(0, 2.0, -4.0), Color("10202B"))
	_make_box("LeftWall", Vector3(0.18, 4.0, 8.0), Vector3(-4.0, 2.0, 0), Color("0D1A24"))
	_make_box("RightWall", Vector3(0.18, 4.0, 8.0), Vector3(4.0, 2.0, 0), Color("0B1721"))
	_make_box("WindowFrame", Vector3(1.8, 1.25, 0.08), Vector3(-2.35, 2.25, -3.88), Color("1B3140"))
	_make_box("WindowGlass", Vector3(1.45, 0.9, 0.04), Vector3(-2.35, 2.25, -3.82), Color("172D3A"), true)

	# Bed and small lived-in props.
	_make_box("BedBase", Vector3(2.6, 0.35, 1.35), Vector3(2.2, 0.22, -2.65), Color("2A2025"))
	_make_box("BedSheet", Vector3(2.45, 0.16, 1.2), Vector3(2.2, 0.48, -2.65), Color("304C54"))
	_make_box("Pillow", Vector3(0.75, 0.18, 0.45), Vector3(1.35, 0.68, -2.9), Color("D5D0B8"))
	_make_box("Nightstand", Vector3(0.62, 0.58, 0.62), Vector3(3.45, 0.3, -2.4), Color("32251A"))
	_make_box("Ashtray", Vector3(0.26, 0.04, 0.18), Vector3(3.45, 0.62, -2.4), Color("5F6766"))
	for i in 3:
		_make_box("CigaretteButt%d" % i, Vector3(0.05, 0.025, 0.18), Vector3(3.35 + i * 0.09, 0.67, -2.39), Color("D8C99D"))

	# CRT corner, kept as first-screen signal.
	var tv_body := _make_box("CRTBody", Vector3(1.55, 1.15, 0.85), Vector3(-1.1, 1.28, -3.25), Color("111418"))
	_make_box("CRTStand", Vector3(0.72, 0.18, 0.45), Vector3(-1.1, 0.62, -3.08), Color("0A0D10"))
	if crt_screen:
		var screen_mesh := BoxMesh.new()
		screen_mesh.size = Vector3(1.16, 0.72, 0.035)
		crt_screen.mesh = screen_mesh
		crt_screen.position = Vector3(-1.1, 1.31, -2.81)
	else:
		crt_screen = _make_box("CRTScreen", Vector3(1.16, 0.72, 0.035), Vector3(-1.1, 1.31, -2.81), Color("112A18"), true)
	crt_screen.name = "CRTScreen"
	_make_box("CRTKnobA", Vector3(0.08, 0.08, 0.05), Vector3(0.56, -0.22, 0.45), Color("30363A"), false, tv_body)

	_create_desk_preview()


func _create_desk_preview() -> void:
	# Desk and 2005-ish colorful handheld console preview.
	_make_box("DeskTop", Vector3(3.75, 0.18, 2.1), Vector3(0, 0.88, -1.35), Color("4A321D"))
	_make_box("DeskLegL", Vector3(0.18, 0.9, 0.18), Vector3(-1.65, 0.42, -0.55), Color("2B1B10"))
	_make_box("DeskLegR", Vector3(0.18, 0.9, 0.18), Vector3(1.65, 0.42, -0.55), Color("2B1B10"))

	var console := Node3D.new()
	console.name = "DeskConsole"
	console.position = Vector3(0, 1.04, -1.45)
	room.add_child(console)
	_make_box("ConsoleShell", Vector3(1.75, 0.2, 0.92), Vector3.ZERO, Color("28A9D7"), false, console)
	_make_box("ConsoleScreen", Vector3(0.72, 0.035, 0.46), Vector3(0, 0.13, -0.03), Color("09241F"), true, console)
	_make_box("ConsoleSlot", Vector3(0.62, 0.045, 0.12), Vector3(0, 0.16, -0.42), Color("0A0E12"), false, console)
	_make_cylinder("DPad", 0.13, 0.04, Vector3(-0.64, 0.15, 0.1), Color("102633"), console)
	_make_cylinder("ButtonA", 0.09, 0.04, Vector3(0.58, 0.15, 0.04), Color("F04A53"), console)
	_make_cylinder("ButtonB", 0.075, 0.04, Vector3(0.76, 0.15, 0.14), Color("F3D64A"), console)

	var colors := [Color("E34B3F"), Color("3159D9"), Color("E7CF36")]
	for i in 3:
		var cart := Node3D.new()
		cart.name = "CartridgePreview%d" % (i + 1)
		cart.position = Vector3(-1.15 + i * 1.15, 1.05, -0.35)
		cart.rotation_degrees.y = -16.0 + i * 14.0
		room.add_child(cart)
		_make_box("Shell", Vector3(0.42, 0.08, 0.58), Vector3.ZERO, colors[i], false, cart)
		_make_box("Label", Vector3(0.32, 0.012, 0.28), Vector3(0, 0.052, -0.04), Color("F2E9C9"), false, cart)
		_make_box("Pins", Vector3(0.28, 0.018, 0.08), Vector3(0, 0.055, -0.26), Color("B99855"), false, cart)


func _make_box(node_name: String, size: Vector3, pos: Vector3, color: Color, unshaded: bool = false, parent: Node3D = null) -> MeshInstance3D:
	var mesh := BoxMesh.new()
	mesh.size = size
	var node := MeshInstance3D.new()
	node.name = node_name
	node.mesh = mesh
	node.position = pos
	var mat := StandardMaterial3D.new()
	mat.albedo_color = color
	if unshaded:
		mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
		mat.emission = color
		mat.emission_energy = 0.2
	node.material_override = mat
	var target_parent := parent if parent != null else room
	target_parent.add_child(node)
	return node


func _make_cylinder(node_name: String, radius: float, height: float, pos: Vector3, color: Color, parent: Node3D) -> MeshInstance3D:
	var mesh := CylinderMesh.new()
	mesh.top_radius = radius
	mesh.bottom_radius = radius
	mesh.height = height
	mesh.radial_segments = 8
	var node := MeshInstance3D.new()
	node.name = node_name
	node.mesh = mesh
	node.position = pos
	node.rotation_degrees.x = 90.0
	var mat := StandardMaterial3D.new()
	mat.albedo_color = color
	node.material_override = mat
	parent.add_child(node)
	return node


func _connect_buttons() -> void:
	if menu_buttons:
		for child in menu_buttons.get_children():
			if child is Button:
				var text: String = child.text
				if "开始" in text or "はじめる" in text or "New" in text:
					child.pressed.connect(_on_new_game_pressed)
				elif "设置" in text or "設定" in text or "Settings" in text:
					child.pressed.connect(_on_settings_pressed)

	if language_btn:
		language_btn.pressed.connect(_on_language_pressed)


func _setup_ui() -> void:
	if title_label:
		title_label.text = "X. WHEEL"
		title_label.add_theme_color_override("font_color", Color("3FA943"))

	# Style menu buttons
	for child in menu_buttons.get_children():
		if child is Button:
			child.add_theme_color_override("font_color", Color("35A146"))
			child.add_theme_color_override("font_hover_color", Color("3FA943"))
			child.add_theme_font_override("font", LanguageManager.get_current_font())


func _setup_crt() -> void:
	# Apply static/noise shader to CRT screen
	if crt_screen:
		var mat := ShaderMaterial.new()
		mat.shader = load("res://shaders/scanline.gdshader")
		crt_screen.material_override = mat


func _start_menu_bgm() -> void:
	if MENU_BGM is AudioStreamWAV:
		MENU_BGM.loop_mode = AudioStreamWAV.LOOP_FORWARD
	AudioManager.play_bgm(MENU_BGM, 2.0)


func _apply_language() -> void:
	var is_cn := LanguageManager.current_language == LanguageManager.Language.CHINESE
	if language_btn:
		language_btn.text = "日本語" if is_cn else "中文"
	if title_label:
		title_label.add_theme_font_override("font", LanguageManager.get_current_font())
	if version_label:
		version_label.text = "v0.1.0"


func _process(delta: float) -> void:
	if _is_zooming: return

	# Slow orbital camera rotation around the room
	_orbit_angle += _orbit_speed * delta
	var rad := deg_to_rad(_orbit_amplitude * 0.5)
	var current := sin(_orbit_angle) * rad

	var offset := Vector3(sin(current) * _orbit_radius, 0, cos(current) * _orbit_radius)
	camera.position = _orbit_center + offset
	camera.look_at(_orbit_center + Vector3(0, 0.5, 0))

	# CRT screen flicker
	if crt_screen and randf() < 0.01:
		var mat: ShaderMaterial = crt_screen.material_override
		if mat:
			mat.set_shader_parameter("scanline_opacity", randf_range(0.05, 0.2))


# ─── Button callbacks ───

func _on_new_game_pressed() -> void:
	GlobalState.reset_to_new_game()
	_zoom_to_desk("res://scenes/cartridge_select.tscn")


func _on_continue_pressed() -> void:
	# Load most recent save
	var latest_slot := SaveSystem.get_latest_save()
	if latest_slot >= 0:
		SaveSystem.load_game(latest_slot)
		# Determine where to go based on loaded state
		if GlobalState.play_order.is_empty():
			_zoom_to_desk("res://scenes/cartridge_select.tscn")
		elif GlobalState.current_cartridge != "" and not GlobalState.all_cartridges_completed:
			# Resume last active cartridge
			var cart_map: Dictionary = {
				"cartridge1": "res://scenes/cartridge1.tscn",
				"cartridge2": "res://scenes/cartridge2.tscn",
				"cartridge3": "res://scenes/cartridge3.tscn",
				"final": "res://scenes/final_chapter.tscn",
			}
			var scene_path: String = cart_map.get(GlobalState.current_cartridge, "res://scenes/cartridge_select.tscn")
			_zoom_to_desk(scene_path)
		else:
			_zoom_to_desk("res://scenes/cartridge_select.tscn")
	else:
		_on_new_game_pressed()


func _on_settings_pressed() -> void:
	# Placeholder — will open settings overlay
	pass


func _on_language_pressed() -> void:
	LanguageManager.toggle_language()
	_apply_language()
	_setup_ui()


func _on_quit_pressed() -> void:
	get_tree().quit()


# ─── Zoom-to-desk animation ───

func _zoom_to_desk(target_scene: String) -> void:
	if _is_zooming: return
	_is_zooming = true
	AudioManager.play_bgm_stinger(START_GAME_TRANSITION, 1.0)
	AudioManager.stop_bgm(0.8)

	# Hide menu UI
	if title_label:
		title_label.hide()
	if menu_buttons:
		for child in menu_buttons.get_children():
			child.hide()
	if crt_screen:
		crt_screen.hide()
	if emida_sprite:
		emida_sprite.hide()

	# Animate camera: move from orbital to desk view, rotating toward desk
	var start_pos := camera.global_position
	var look_dir := -camera.global_transform.basis.z
	var start_look := start_pos + look_dir * 5.0

	var tween := create_tween()
	tween.set_parallel(false)
	tween.tween_method(
		func(t: float):
			var current_pos := start_pos.lerp(DESK_CAM_POS, t)
			var current_look := start_look.lerp(DESK_CAM_LOOK, t)
			camera.global_position = current_pos
			camera.look_at(current_look),
		0.0, 1.0, 2.0
	).set_ease(Tween.EASE_IN_OUT).set_trans(Tween.TRANS_CUBIC)

	# Fade to black and transition
	tween.tween_callback(func():
		var overlay := ColorRect.new()
		overlay.set_anchors_preset(Control.PRESET_FULL_RECT)
		overlay.color = Color.BLACK
		overlay.modulate.a = 0.0
		add_child(overlay)

		var ft := create_tween()
		ft.tween_property(overlay, "modulate:a", 1.0, 0.8)
		ft.tween_callback(func():
			get_tree().change_scene_to_file(target_scene)
		)
	)


func _fade_to_scene(path: String) -> void:
	var overlay := ColorRect.new()
	overlay.set_anchors_preset(Control.PRESET_FULL_RECT)
	overlay.color = Color.BLACK
	overlay.modulate.a = 0.0
	add_child(overlay)

	var tween := create_tween()
	tween.tween_property(overlay, "modulate:a", 1.0, 1.5)
	tween.tween_callback(func():
		get_tree().change_scene_to_file(path)
	)
