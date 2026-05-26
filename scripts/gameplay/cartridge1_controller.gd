extends CartridgeBaseController
## Cartridge 1: 《薯条雨&火焰&我》 — dream sequences, school, tower discovery.

# ─── Environment nodes ───
var _environments: Dictionary = {}  # env_name -> Node3D
var _current_env: String = ""
var _cigarette_butt_mesh: MeshInstance3D


func _ready() -> void:
	cartridge_name = "cartridge1"
	dialogue_csv = "res://data/dialogue/cartridge1_fries_rain.csv"
	super._ready()


func _setup_environment() -> void:
	_create_bedroom()
	_create_classroom()
	_create_school_hallway()
	_create_computer_room()
	_create_tower_distant()
	_create_dream_burning()
	_switch_environment("bedroom")


func _on_cartridge_start() -> void:
	_has_cigarette_butt = true
	GlobalState.cigarette_butt_seen[cartridge_name] = true


func _handle_interaction_type(itype: String, data: Dictionary) -> void:
	match itype:
		"dream_sequence":
			_do_dream_sequence()
		"red_flash":
			_do_red_flash()
		"env_switch":
			_switch_environment(data.get("env", ""))
		_:
			super._handle_interaction_type(itype, data)


# ─── Environment creation ───

func _create_bedroom() -> void:
	var env := Node3D.new()
	env.name = "Env_Bedroom"

	env.add_child(_make_box(Vector3(4, 0.1, 4), Vector3(0, -0.05, 0), Color(0.12, 0.1, 0.08)))
	env.add_child(_make_box(Vector3(4, 2.5, 0.1), Vector3(0, 1.25, -2), Color(0.1, 0.08, 0.07)))
	env.add_child(_make_box(Vector3(0.1, 2.5, 4), Vector3(-2, 1.25, 0), Color(0.1, 0.08, 0.07)))
	env.add_child(_make_box(Vector3(0.1, 2.5, 4), Vector3(2, 1.25, 0), Color(0.1, 0.08, 0.07)))
	env.add_child(_make_plane(Vector2(1.2, 1.0), Vector3(0, 1.8, -1.95), Color("0C1725")))
	env.add_child(_make_box(Vector3(1.8, 0.3, 2.0), Vector3(0.5, 0.1, 1.2), Color(0.15, 0.12, 0.1)))
	env.add_child(_make_box(Vector3(0.4, 0.5, 0.4), Vector3(1.2, 0.25, 0.8), Color(0.18, 0.13, 0.09)))
	env.add_child(_make_box(Vector3(0.12, 0.04, 0.12), Vector3(1.2, 0.52, 0.8), Color(0.3, 0.3, 0.3)))
	_cigarette_butt_mesh = _make_box(Vector3(0.02, 0.01, 0.06), Vector3(1.2, 0.54, 0.8), Color(0.9, 0.85, 0.7))
	_cigarette_butt_mesh.visible = false
	env.add_child(_cigarette_butt_mesh)

	env.hide()
	add_child(env)
	_environments["bedroom"] = env


func _create_classroom() -> void:
	var env := Node3D.new()
	env.name = "Env_Classroom"
	env.add_child(_make_box(Vector3(6, 0.1, 5), Vector3(0, -0.05, 0), Color(0.15, 0.14, 0.12)))
	env.add_child(_make_box(Vector3(6, 3, 0.1), Vector3(0, 1.5, -2.5), Color(0.2, 0.18, 0.15)))
	env.add_child(_make_box(Vector3(2.5, 1.2, 0.02), Vector3(0, 1.7, -2.44), Color(0.1, 0.2, 0.12)))
	for row in 2:
		for col in 2:
			env.add_child(_make_box(Vector3(0.6, 0.05, 0.4), Vector3(-0.8 + col * 1.6, 0.7, -0.5 + row * 1.2), Color(0.25, 0.2, 0.15)))
	for i in 2:
		env.add_child(_make_plane(Vector2(0.8, 1.2), Vector3(-3, 1.8, -1.0 + i * 1.5), Color("0C1725")))
	env.hide()
	add_child(env)
	_environments["classroom"] = env


func _create_school_hallway() -> void:
	var env := Node3D.new()
	env.name = "Env_SchoolHallway"
	env.add_child(_make_box(Vector3(2.5, 0.1, 8), Vector3(0, -0.05, 0), Color(0.14, 0.13, 0.11)))
	env.add_child(_make_box(Vector3(0.1, 3, 8), Vector3(-1.2, 1.5, 0), Color(0.18, 0.16, 0.13)))
	env.add_child(_make_box(Vector3(0.1, 3, 8), Vector3(1.2, 1.5, 0), Color(0.18, 0.16, 0.13)))
	for i in 4:
		env.add_child(_make_box(Vector3(0.15, 0.6, 0.3), Vector3(-1.1, 1.2, -2.5 + i * 1.5), Color(0.3, 0.28, 0.25)))
	env.hide()
	add_child(env)
	_environments["school_hallway"] = env


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
	env.hide()
	add_child(env)
	_environments["computer_room"] = env


func _create_tower_distant() -> void:
	var env := Node3D.new()
	env.name = "Env_TowerDistant"
	env.add_child(_make_box(Vector3(8, 0.1, 8), Vector3(0, -0.05, 0), Color(0.08, 0.1, 0.12)))
	var tower_mesh := CylinderMesh.new()
	tower_mesh.top_radius = 0.3
	tower_mesh.bottom_radius = 0.5
	tower_mesh.height = 8.0
	var tower := MeshInstance3D.new()
	tower.mesh = tower_mesh
	tower.position = Vector3(0, 4, -3)
	var tower_mat := StandardMaterial3D.new()
	tower_mat.albedo_color = Color(0.15, 0.15, 0.2)
	tower.material_override = tower_mat
	env.add_child(tower)
	var light_mesh := SphereMesh.new()
	light_mesh.radius = 0.15
	light_mesh.height = 0.3
	var light_node := MeshInstance3D.new()
	light_node.mesh = light_mesh
	light_node.position = Vector3(0, 8, -3)
	var light_mat := StandardMaterial3D.new()
	light_mat.albedo_color = Color("3FA943")
	light_mat.emission = Color("3FA943")
	light_mat.emission_energy = 2.0
	light_node.material_override = light_mat
	env.add_child(light_node)
	env.hide()
	add_child(env)
	_environments["tower_distant"] = env


func _create_dream_burning() -> void:
	var env := Node3D.new()
	env.name = "Env_DreamBurning"
	env.add_child(_make_box(Vector3(6, 0.05, 6), Vector3(0, -0.03, 0), Color(0.05, 0.02, 0.02)))
	env.add_child(_make_box(Vector3(2.5, 2.0, 2.0), Vector3(0, 1.0, 0), Color(0.08, 0.04, 0.02)))
	env.hide()
	add_child(env)
	_environments["dream_burning"] = env


# ─── Environment switching ───

func _switch_environment(env_name: String) -> void:
	if env_name == _current_env: return
	if _current_env != "" and _environments.has(_current_env):
		_environments[_current_env].hide()
	if _environments.has(env_name):
		_environments[env_name].show()
		_current_env = env_name
		if env_name == "bedroom" and _cigarette_butt_mesh:
			_cigarette_butt_mesh.visible = true


# ─── Effect handlers ───

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


# ─── Mesh helpers ───

func _make_box(size: Vector3, pos: Vector3, color: Color) -> MeshInstance3D:
	var mesh := BoxMesh.new()
	mesh.size = size
	var node := MeshInstance3D.new()
	node.mesh = mesh
	node.position = pos
	var mat := StandardMaterial3D.new()
	mat.albedo_color = color
	node.material_override = mat
	return node


func _make_plane(size: Vector2, pos: Vector3, color: Color) -> MeshInstance3D:
	var mesh := PlaneMesh.new()
	mesh.size = size
	var node := MeshInstance3D.new()
	node.mesh = mesh
	node.position = pos
	var mat := StandardMaterial3D.new()
	mat.albedo_color = color
	mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	node.material_override = mat
	return node
