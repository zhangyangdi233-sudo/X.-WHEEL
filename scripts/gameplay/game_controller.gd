extends Node3D
## Main game controller — manages the 3D tower scene, dialogue flow, chapter sequencing.

@onready var camera: Camera3D = %GameCamera
@onready var tower_platform: Node3D = %TowerPlatform
@onready var emida_sprite: Sprite3D = %EmidaSprite
@onready var signal_light: OmniLight3D = %SignalLight
@onready var world_env: WorldEnvironment = %WorldEnvironment
@onready var ui_layer: CanvasLayer = %UILayer

# UI elements
var dialogue_box: Control
var transition_overlay: ColorRect
var capitolo_label: Label
var capitolo_sub: Label
var scanline_overlay: ColorRect
var vignette_overlay: ColorRect
var mood_overlay: ColorRect

# Chapter flow
var _current_chapter_data: String = ""
var _intercut_timer: float = 0.0
var _intercut_index: int = 0
var _is_intercutting: bool = false
var _pending_scene: String = ""
var _story_phase: int = 0
var _is_demo_complete: bool = false

enum StoryPhase {
	NONE,
	PROLOGUE,
	CHAPTER_1,
	COMPLETE,
}


func _ready() -> void:
	_create_placeholder_tower()
	_setup_ui()
	_connect_signals()
	_apply_visual_settings()

	# Start with Capitolo 0 → prologue
	await get_tree().create_timer(0.5).timeout
	_show_capitolo(0, "以太と古い画面の匂い", "以太と古い画面の匂い")
	await _wait_capitolo_done()
	_start_prologue_intercut()


func _create_placeholder_tower() -> void:
	# Tower platform floor
	var floor_mesh := BoxMesh.new()
	floor_mesh.size = Vector3(6, 0.3, 6)
	var floor := MeshInstance3D.new()
	floor.mesh = floor_mesh
	floor.position = Vector3(0, 0, 0)
	floor.name = "TowerFloor"
	var floor_mat := StandardMaterial3D.new()
	floor_mat.albedo_color = Color(0.08, 0.12, 0.18)
	floor.material_override = floor_mat
	tower_platform.add_child(floor)

	# Signal terminal (box with green glow)
	var terminal_mesh := BoxMesh.new()
	terminal_mesh.size = Vector3(1.2, 0.8, 0.6)
	var terminal := MeshInstance3D.new()
	terminal.mesh = terminal_mesh
	terminal.position = Vector3(0, 1.5, -1)
	terminal.name = "SignalTerminal"
	var terminal_mat := StandardMaterial3D.new()
	terminal_mat.albedo_color = Color(0.15, 0.15, 0.15)
	terminal_mat.emission = Color("3FA943")
	terminal_mat.emission_energy = 0.5
	terminal.material_override = terminal_mat
	tower_platform.add_child(terminal)

	# Set up sky/environment
	if world_env:
		var env := Environment.new()
		env.background_mode = Environment.BG_COLOR
		env.background_color = Color("0C1725")
		env.ambient_light_color = Color(0.08, 0.12, 0.18)
		world_env.environment = env


func _setup_ui() -> void:
	# Dialogue box
	var db_scene := load("res://scenes/ui/dialogue_box.tscn")
	dialogue_box = db_scene.instantiate()
	ui_layer.add_child(dialogue_box)

	# Transition overlay (black screen for Capitolo / intercut)
	transition_overlay = ColorRect.new()
	transition_overlay.name = "TransitionOverlay"
	transition_overlay.set_anchors_preset(Control.PRESET_FULL_RECT)
	transition_overlay.color = Color.BLACK
	transition_overlay.modulate.a = 0.0
	ui_layer.add_child(transition_overlay)

	# Capitolo labels
	capitolo_label = Label.new()
	capitolo_label.name = "CapitoloLabel"
	capitolo_label.add_theme_font_size_override("font_size", 72)
	capitolo_label.add_theme_color_override("font_color", Color.WHITE)
	capitolo_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	capitolo_label.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	capitolo_label.anchors_preset = Control.PRESET_CENTER
	capitolo_label.modulate.a = 0.0
	ui_layer.add_child(capitolo_label)

	capitolo_sub = Label.new()
	capitolo_sub.name = "CapitoloSub"
	capitolo_sub.add_theme_font_size_override("font_size", 24)
	capitolo_sub.add_theme_color_override("font_color", Color.WHITE)
	capitolo_sub.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	capitolo_sub.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	capitolo_sub.anchors_preset = Control.PRESET_CENTER
	capitolo_sub.position = Vector2(0, 80)
	capitolo_sub.modulate.a = 0.0
	ui_layer.add_child(capitolo_sub)

	# Scanline overlay
	var sl_mat := ShaderMaterial.new()
	sl_mat.shader = load("res://shaders/scanline.gdshader")
	scanline_overlay = ColorRect.new()
	scanline_overlay.name = "ScanlineOverlay"
	scanline_overlay.set_anchors_preset(Control.PRESET_FULL_RECT)
	scanline_overlay.material = sl_mat
	scanline_overlay.mouse_filter = Control.MOUSE_FILTER_IGNORE
	ui_layer.add_child(scanline_overlay)

	# Vignette overlay
	var vg_mat := ShaderMaterial.new()
	vg_mat.shader = load("res://shaders/vignette.gdshader")
	vignette_overlay = ColorRect.new()
	vignette_overlay.name = "VignetteOverlay"
	vignette_overlay.set_anchors_preset(Control.PRESET_FULL_RECT)
	vignette_overlay.material = vg_mat
	vignette_overlay.mouse_filter = Control.MOUSE_FILTER_IGNORE
	ui_layer.add_child(vignette_overlay)

	# Mood color grading overlay
	var mood_mat := ShaderMaterial.new()
	mood_mat.shader = load("res://shaders/mood_color.gdshader")
	mood_overlay = ColorRect.new()
	mood_overlay.name = "MoodOverlay"
	mood_overlay.set_anchors_preset(Control.PRESET_FULL_RECT)
	mood_overlay.material = mood_mat
	mood_overlay.mouse_filter = Control.MOUSE_FILTER_IGNORE
	ui_layer.add_child(mood_overlay)


func _connect_signals() -> void:
	if dialogue_box:
		dialogue_box.text_finished.connect(_on_text_finished)
		dialogue_box.choice_selected.connect(_on_choice_selected)


func _apply_visual_settings() -> void:
	# Set initial camera for tower scene
	camera.position = Vector3(0, 8, 15)
	camera.look_at(Vector3(0, 2, 0))

	# Signal light pulse animation
	if signal_light:
		var tween := create_tween()
		tween.set_loops()
		tween.tween_property(signal_light, "light_energy", 1.5, 2.0)
		tween.tween_property(signal_light, "light_energy", 0.5, 2.0)


func _process(delta: float) -> void:
	# Update mood shader
	var mood_mat: ShaderMaterial = mood_overlay.material
	mood_mat.set_shader_parameter("mood_level", GlobalState.mood_level)

	# Update vignette
	var vg_mat: ShaderMaterial = vignette_overlay.material
	vg_mat.set_shader_parameter("vignette_intensity", 0.2 + GlobalState.mood_level * 0.6)
	vg_mat.set_shader_parameter("red_bleed", maxf(0.0, GlobalState.mood_level - 0.7) * 3.0)

	# Apply camera shake if active
	if GlobalState.shake_intensity > 0.01:
		camera.position.x += randf_range(-GlobalState.shake_intensity * 0.01, GlobalState.shake_intensity * 0.01)
		camera.position.y += randf_range(-GlobalState.shake_intensity * 0.01, GlobalState.shake_intensity * 0.01)


func _unhandled_input(event: InputEvent) -> void:
	if not _is_demo_complete:
		return

	if event.is_action_pressed("ui_accept") or event.is_action_pressed("ui_cancel"):
		get_tree().change_scene_to_file("res://scenes/main_menu.tscn")


# ─── Capitolo cards ───

func _show_capitolo(number: int, subtitle_zh: String, subtitle_ja: String) -> void:
	var sub: String = subtitle_zh if LanguageManager.current_language == LanguageManager.Language.CHINESE else subtitle_ja

	capitolo_label.text = "Capitolo " + str(number) if number >= 0 else ""
	capitolo_sub.text = "—— " + sub + " ——"

	transition_overlay.modulate.a = 1.0
	var tween := create_tween()
	tween.tween_interval(0.5)
	tween.tween_callback(func():
		capitolo_label.modulate.a = 1.0
		capitolo_sub.modulate.a = 1.0
	)
	tween.tween_interval(2.5)
	tween.tween_property(transition_overlay, "modulate:a", 0.0, 1.0)
	tween.parallel().tween_property(capitolo_label, "modulate:a", 0.0, 1.0)
	tween.parallel().tween_property(capitolo_sub, "modulate:a", 0.0, 1.0)


func _wait_capitolo_done() -> void:
	await get_tree().create_timer(4.0).timeout


# ─── Prologue: 1999 chatroom ↔ tower intercut ───

func _start_prologue_intercut() -> void:
	_is_intercutting = true
	_intercut_index = 0
	_story_phase = StoryPhase.PROLOGUE
	DialogueManager.start_dialogue("res://data/dialogue/prologue.csv")


func _on_text_finished() -> void:
	if DialogueManager.is_active():
		return

	match _story_phase:
		StoryPhase.PROLOGUE:
			_is_intercutting = false
			_story_phase = StoryPhase.CHAPTER_1
			await get_tree().create_timer(1.0).timeout
			_show_capitolo(1, "燃えた家の匂い", "燃えた家の匂い")
			await _wait_capitolo_done()
			DialogueManager.start_dialogue("res://data/dialogue/chapter1.csv")
		StoryPhase.CHAPTER_1:
			_story_phase = StoryPhase.COMPLETE
			_show_demo_complete()


func _show_demo_complete() -> void:
	_is_demo_complete = true
	dialogue_box.hide()
	transition_overlay.color = Color.BLACK
	transition_overlay.modulate.a = 0.0
	capitolo_label.text = "未完待续"
	capitolo_sub.text = "当前版本到这里 / 按确认键返回标题"
	capitolo_label.modulate.a = 0.0
	capitolo_sub.modulate.a = 0.0

	var tween := create_tween()
	tween.tween_property(transition_overlay, "modulate:a", 1.0, 1.0)
	tween.parallel().tween_property(capitolo_label, "modulate:a", 1.0, 1.0)
	tween.parallel().tween_property(capitolo_sub, "modulate:a", 1.0, 1.0)


func _on_choice_selected(choice_id: String) -> void:
	pass  # handled by dialogue_box for flag effects


# ─── Ending logic ───

func trigger_ending() -> void:
	match GlobalState.ending_reached:
		GlobalState.Ending.TRANSMIT:
			_start_ending_transmit()
		GlobalState.Ending.SUNSET:
			_start_ending_sunset()


func _start_ending_transmit() -> void:
	# Green light engulfs the screen
	signal_light.light_energy = 10.0
	var tween := create_tween()
	tween.tween_property(transition_overlay, "modulate:a", 1.0, 1.5)
	transition_overlay.color = Color("35A146")
	tween.tween_callback(func():
		DialogueManager.start_dialogue("res://data/dialogue/ending_a.csv")
	)


func _start_ending_sunset() -> void:
	# Sunset warm light, then fade to white
	signal_light.light_color = Color.ORANGE_RED
	var tween := create_tween()
	tween.tween_property(transition_overlay, "modulate:a", 1.0, 2.0)
	transition_overlay.color = Color.WHITE
	tween.tween_callback(func():
		DialogueManager.start_dialogue("res://data/dialogue/ending_b.csv")
	)
