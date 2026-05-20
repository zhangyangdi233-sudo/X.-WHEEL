extends Node3D
## Main menu scene controller — CRT room with orbiting 3D camera.

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


func _ready() -> void:
	_create_placeholder_geometry()
	_setup_ui()
	_connect_buttons()
	_setup_crt()
	_apply_language()

	if not GlobalState.capitolo_seen.is_empty():
		var continue_btn := Button.new()
		continue_btn.text = LanguageManager.t("continue")
		continue_btn.add_theme_font_override("font", LanguageManager.get_current_font())
		continue_btn.pressed.connect(_on_continue_pressed)
		menu_buttons.add_child(continue_btn)
		menu_buttons.move_child(continue_btn, 0)


func _create_placeholder_geometry() -> void:
	# Floor
	var floor_mesh := BoxMesh.new()
	floor_mesh.size = Vector3(8, 0.2, 8)
	var floor := MeshInstance3D.new()
	floor.mesh = floor_mesh
	floor.position = Vector3(0, -0.1, 0)
	var floor_mat := StandardMaterial3D.new()
	floor_mat.albedo_color = Color("0C1725")
	floor_mat.albedo_color = floor_mat.albedo_color.darkened(0.3)
	floor.material_override = floor_mat
	room.add_child(floor)

	# Back wall
	var wall_mesh := BoxMesh.new()
	wall_mesh.size = Vector3(8, 4, 0.2)
	var wall := MeshInstance3D.new()
	wall.mesh = wall_mesh
	wall.position = Vector3(0, 2, -4)
	var wall_mat := StandardMaterial3D.new()
	wall_mat.albedo_color = Color("0C1725")
	wall.material_override = wall_mat
	room.add_child(wall)

	# CRT TV (box placeholder)
	var tv_mesh := BoxMesh.new()
	tv_mesh.size = Vector3(1.6, 1.2, 0.8)
	if crt_screen == null:
		var tv := MeshInstance3D.new()
		tv.mesh = tv_mesh
		tv.position = Vector3(0, 1.2, -2.8)
		var tv_mat := StandardMaterial3D.new()
		tv_mat.albedo_color = Color(0.1, 0.1, 0.1)
		tv.material_override = tv_mat
		room.add_child(tv)
		# reassign crt_screen for shader
		crt_screen = tv


func _connect_buttons() -> void:
	for child in menu_buttons.get_children():
		if child is Button:
			var text: String = child.text
			if "开始" in text or "はじめる" in text or "New" in text:
				child.pressed.connect(_on_new_game_pressed)
			elif "设置" in text or "設定" in text or "Settings" in text:
				child.pressed.connect(_on_settings_pressed)

	language_btn.pressed.connect(_on_language_pressed)


func _setup_ui() -> void:
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


func _apply_language() -> void:
	var is_cn := LanguageManager.current_language == LanguageManager.Language.CHINESE
	language_btn.text = "日本語" if is_cn else "中文"
	title_label.add_theme_font_override("font", LanguageManager.get_current_font())
	version_label.text = "v0.1.0"


func _process(delta: float) -> void:
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
		mat.set_shader_parameter("scanline_opacity", randf_range(0.05, 0.2))


# ─── Button callbacks ───

func _on_new_game_pressed() -> void:
	GlobalState.reset_to_new_game()
	_fade_to_scene("res://scenes/game.tscn")


func _on_continue_pressed() -> void:
	# Load most recent save
	var latest_slot := -1
	for i in 20:
		if SaveSystem.slot_exists(i):
			latest_slot = i

	if latest_slot >= 0:
		SaveSystem.load_game(latest_slot)
		_fade_to_scene("res://scenes/game.tscn")
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
