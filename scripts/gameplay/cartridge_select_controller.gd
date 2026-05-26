extends Node3D
## Cartridge selection — top-down view, drag cartridges into the console.

@onready var camera: Camera3D = $DeskCamera
@onready var desk_env: Node3D = $DeskEnvironment
@onready var cartridge_label: Label = $UICanvas/CartridgeLabel
@onready var instruction_label: Label = $UICanvas/InstructionLabel

var _cartridges: Dictionary = {}
var _hovered: String = ""
var _is_animating: bool = false

var _dragging: String = ""
var _drag_offset: Vector3 = Vector3.ZERO
var _drag_plane: Plane

const CARTRIDGE_INFO := {
	"Cartridge1": {
		"scene": "res://scenes/cartridge1.tscn",
		"label_zh": "《薯条雨&火焰&我》",
		"label_ja": "《ポテトの雨と炎と私》",
	},
	"Cartridge2": {
		"scene": "res://scenes/cartridge2.tscn",
		"label_zh": "《晚饭吃什么》",
		"label_ja": "《夕飯は何を食べる》",
	},
	"Cartridge3": {
		"scene": "res://scenes/cartridge3.tscn",
		"label_zh": "《哈吉米南北绿豆》",
		"label_ja": "《ハジミ南北緑豆》",
	},
}

const CARTRIDGE_COLORS := {
	"Cartridge1": Color(0.85, 0.25, 0.2),
	"Cartridge2": Color(0.2, 0.35, 0.85),
	"Cartridge3": Color(0.85, 0.75, 0.2),
}


func _ready() -> void:
	camera.position = Vector3(0, 3.5, -1.5)
	camera.rotation_degrees = Vector3(-90, 0, 0)
	camera.current = true

	var cam_light := OmniLight3D.new()
	cam_light.name = "CameraLight"
	cam_light.light_energy = 3.0
	cam_light.light_color = Color(1.0, 0.95, 0.85)
	cam_light.omni_range = 8.0
	camera.add_child(cam_light)

	_create_console_model()
	_randomize_cartridge_positions()
	_setup_cartridges()
	_apply_language()
	_update_instruction()


func _randomize_cartridge_positions() -> void:
	var desk_y: float = 0.94 + 0.075
	var center: Vector3 = Vector3(0, desk_y, -1.5)
	var used: Array = []

	for child in desk_env.get_children():
		var child_name: String = child.name
		if child_name.begins_with("Cartridge") and child is MeshInstance3D:
			var mesh: MeshInstance3D = child
			var pos: Vector3 = _find_free_spot(center, used, 1.0, 2.0)
			pos.y = desk_y
			used.append(pos)
			mesh.position = pos


func _find_free_spot(center: Vector3, used: Array, min_dist: float, max_dist: float) -> Vector3:
	for _attempt in 50:
		var angle := randf() * TAU
		var dist := randf_range(min_dist, max_dist)
		var candidate := center + Vector3(sin(angle) * dist, 0, cos(angle) * dist)
		candidate.x = clampf(candidate.x, -2.0, 2.0)
		candidate.z = clampf(candidate.z, -3.0, 0.0)
		var too_close := false
		for p in used:
			if candidate.distance_to(p) < 0.6:
				too_close = true
				break
		if not too_close:
			return candidate
	return center + Vector3(1.5 + used.size() * 0.5, 0, 0)


func _setup_cartridges() -> void:
	for child in desk_env.get_children():
		var child_name: String = child.name
		if child_name.begins_with("Cartridge") and child is MeshInstance3D:
			var mesh: MeshInstance3D = child

			var box := BoxMesh.new()
			box.size = Vector3(0.48, 0.13, 0.68)
			mesh.mesh = box
			mesh.material_override = _make_mat(CARTRIDGE_COLORS.get(child_name, Color(0.5, 0.5, 0.5)))
			_create_cartridge_label(mesh, child_name)

			var area := Area3D.new()
			area.name = child_name + "Area"
			area.collision_layer = 1
			area.collision_mask = 0
			area.input_ray_pickable = true
			var col := CollisionShape3D.new()
			col.name = "Collision"
			var box_shape := BoxShape3D.new()
			box_shape.size = Vector3(0.5, 0.25, 0.7)
			col.shape = box_shape
			area.add_child(col)
			area.position = mesh.position
			desk_env.add_child(area)

			area.mouse_entered.connect(_on_cartridge_hovered.bind(child_name))
			area.mouse_exited.connect(_on_cartridge_unhovered.bind(child_name))

			_cartridges[child_name] = {
				"mesh": mesh,
				"area": area,
				"original_pos": mesh.position,
			}

	for cart_name in GlobalState.play_order:
		if cart_name in _cartridges:
			_cartridges[cart_name]["completed"] = true
	for cart_name in _cartridges:
		_apply_completed_visuals(cart_name)


func _create_console_model() -> void:
	if desk_env == null:
		return

	var base := desk_env.get_node_or_null("ConsoleBase") as MeshInstance3D
	if base == null:
		base = MeshInstance3D.new()
		base.name = "ConsoleBase"
		desk_env.add_child(base)
	base.position = Vector3(0, 1.14, -1.5)
	var base_mesh := BoxMesh.new()
	base_mesh.size = Vector3(2.2, 0.34, 1.28)
	base.mesh = base_mesh
	base.material_override = _make_mat(Color("28A9D7"))

	if not desk_env.has_node("ConsoleScreen"):
		_make_box_child("ConsoleScreen", Vector3(0.78, 0.035, 0.48), Vector3(0, 1.335, -1.47), Color("09241F"), true)
		_make_box_child("ConsoleSlotTrim", Vector3(0.74, 0.06, 0.16), Vector3(0, 1.36, -1.92), Color("0B1216"))
		_make_box_child("SpeakerBarA", Vector3(0.3, 0.025, 0.035), Vector3(0.76, 1.34, -1.25), Color("104C5C"))
		_make_box_child("SpeakerBarB", Vector3(0.3, 0.025, 0.035), Vector3(0.76, 1.34, -1.13), Color("104C5C"))
		_make_cylinder_child("DPad", 0.14, 0.05, Vector3(-0.77, 1.34, -1.36), Color("102633"))
		_make_cylinder_child("ButtonA", 0.09, 0.05, Vector3(0.68, 1.34, -1.62), Color("F04A53"))
		_make_cylinder_child("ButtonB", 0.075, 0.05, Vector3(0.88, 1.34, -1.5), Color("F3D64A"))

	var slot := desk_env.get_node_or_null("CartridgeSlot")
	if slot:
		slot.position = Vector3(0, 1.39, -1.92)


func _create_cartridge_label(mesh: MeshInstance3D, cart_name: String) -> void:
	if mesh.has_node("FaceLabel"):
		return

	var face := MeshInstance3D.new()
	face.name = "FaceLabel"
	var face_mesh := BoxMesh.new()
	face_mesh.size = Vector3(0.34, 0.014, 0.34)
	face.mesh = face_mesh
	face.position = Vector3(0, 0.075, -0.02)
	face.material_override = _make_mat(Color("F1E7C4"))
	mesh.add_child(face)

	var pins := MeshInstance3D.new()
	pins.name = "GoldPins"
	var pins_mesh := BoxMesh.new()
	pins_mesh.size = Vector3(0.32, 0.018, 0.08)
	pins.mesh = pins_mesh
	pins.position = Vector3(0, 0.08, -0.29)
	pins.material_override = _make_mat(Color("B99855"))
	mesh.add_child(pins)

	var label := Label3D.new()
	label.name = "TitleLabel3D"
	label.text = _get_short_label(cart_name)
	label.pixel_size = 0.018
	label.position = Vector3(0, 0.088, -0.03)
	label.rotation_degrees.x = -90.0
	label.modulate = Color("17202A")
	mesh.add_child(label)


func _get_short_label(cart_name: String) -> String:
	match cart_name:
		"Cartridge1":
			return "FRIES\nFIRE"
		"Cartridge2":
			return "DINNER"
		"Cartridge3":
			return "HAJIMI"
	return "XW"


func _apply_completed_visuals(cart_name: String) -> void:
	var data: Dictionary = _cartridges.get(cart_name, {})
	var mesh := data.get("mesh") as MeshInstance3D
	if mesh == null:
		return

	var done := bool(data.get("completed", false))
	var color: Color = CARTRIDGE_COLORS.get(cart_name, Color.GRAY)
	mesh.material_override = _make_mat(color.darkened(0.35) if done else color)
	if done and not mesh.has_node("CompletedBand"):
		var band := MeshInstance3D.new()
		band.name = "CompletedBand"
		var band_mesh := BoxMesh.new()
		band_mesh.size = Vector3(0.52, 0.02, 0.08)
		band.mesh = band_mesh
		band.position = Vector3(0, 0.095, 0.2)
		band.material_override = _make_mat(Color("3FA943"))
		mesh.add_child(band)


func _sync_cartridge_area(cart_name: String) -> void:
	var data: Dictionary = _cartridges.get(cart_name, {})
	var mesh := data.get("mesh") as MeshInstance3D
	var area := data.get("area") as Area3D
	if mesh and area:
		area.global_position = mesh.global_position


func _make_box_child(node_name: String, size: Vector3, pos: Vector3, color: Color, unshaded: bool = false) -> MeshInstance3D:
	var node := MeshInstance3D.new()
	node.name = node_name
	var mesh := BoxMesh.new()
	mesh.size = size
	node.mesh = mesh
	node.position = pos
	node.material_override = _make_mat(color, unshaded)
	desk_env.add_child(node)
	return node


func _make_cylinder_child(node_name: String, radius: float, height: float, pos: Vector3, color: Color) -> MeshInstance3D:
	var node := MeshInstance3D.new()
	node.name = node_name
	var mesh := CylinderMesh.new()
	mesh.top_radius = radius
	mesh.bottom_radius = radius
	mesh.height = height
	mesh.radial_segments = 8
	node.mesh = mesh
	node.position = pos
	node.rotation_degrees.x = 90.0
	node.material_override = _make_mat(color)
	desk_env.add_child(node)
	return node


func _make_mat(color: Color, unshaded: bool = false) -> StandardMaterial3D:
	var mat := StandardMaterial3D.new()
	mat.albedo_color = color
	if unshaded:
		mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
		mat.emission = color
		mat.emission_energy = 0.35
	return mat


func _apply_language() -> void:
	if instruction_label:
		instruction_label.text = LanguageManager.t("cartridge_select")
		instruction_label.add_theme_font_override("font", LanguageManager.get_current_font())
	if cartridge_label:
		cartridge_label.add_theme_font_override("font", LanguageManager.get_current_font())


func _update_instruction() -> void:
	if not instruction_label: return
	var is_cn := LanguageManager.current_language == LanguageManager.Language.CHINESE
	instruction_label.text = "拖拽卡带插入游戏机" if is_cn else "カートリッジをドラッグして入れる"


func _get_cartridge_label(cart_name: String) -> String:
	var is_cn := LanguageManager.current_language == LanguageManager.Language.CHINESE
	var info: Dictionary = CARTRIDGE_INFO.get(cart_name, {})
	return info.get("label_zh" if is_cn else "label_ja", cart_name)


# ─── Hover ───

func _on_cartridge_hovered(cart_name: String) -> void:
	if _is_animating or _dragging != "": return
	_hovered = cart_name
	if cartridge_label:
		cartridge_label.text = _get_cartridge_label(cart_name)
	var mesh: MeshInstance3D = _cartridges[cart_name].get("mesh")
	if mesh:
		mesh.scale = Vector3(1.1, 1.0, 1.1)


func _on_cartridge_unhovered(cart_name: String) -> void:
	if _dragging == cart_name: return
	if _hovered == cart_name:
		_hovered = ""
		if cartridge_label:
			cartridge_label.text = ""
	var mesh: MeshInstance3D = _cartridges[cart_name].get("mesh")
	if mesh:
		mesh.scale = Vector3(1.0, 1.0, 1.0)


# ─── Global input: drag start + motion + drop ───

func _input(event: InputEvent) -> void:
	if _is_animating: return

	if event is InputEventMouseButton:
		if event.button_index == MOUSE_BUTTON_LEFT:
			if event.pressed:
				_try_start_drag(event.position)
			elif _dragging != "":
				_try_drop()

	elif event is InputEventMouseMotion and _dragging != "":
		_update_drag(event.position)


func _try_start_drag(screen_pos: Vector2) -> void:
	if _dragging != "": return

	var cart_name: String = _raycast_cartridge(screen_pos)
	if cart_name == "": return

	_dragging = cart_name
	_hovered = cart_name
	var mesh: MeshInstance3D = _cartridges[cart_name].get("mesh")
	if mesh:
		mesh.scale = Vector3(1.15, 1.0, 1.15)
		_drag_plane = Plane(Vector3.UP, mesh.position.y)
		var from: Vector3 = camera.project_ray_origin(screen_pos)
		var dir: Vector3 = camera.project_ray_normal(screen_pos)
		var intersection = _drag_plane.intersects_ray(from, dir)
		if intersection != null:
			_drag_offset = mesh.global_position - intersection
	if cartridge_label:
		cartridge_label.text = _get_cartridge_label(cart_name)


func _raycast_cartridge(screen_pos: Vector2) -> String:
	var from: Vector3 = camera.project_ray_origin(screen_pos)
	var dir: Vector3 = camera.project_ray_normal(screen_pos)
	var to: Vector3 = from + dir * 100.0
	var query := PhysicsRayQueryParameters3D.create(from, to)
	query.collision_mask = 1
	query.collide_with_areas = true
	query.collide_with_bodies = false
	var result: Dictionary = get_world_3d().direct_space_state.intersect_ray(query)
	var collider = result.get("collider")
	if collider and collider is Area3D:
		var area_name: String = collider.name
		for cart_name in _cartridges:
			if area_name.begins_with(cart_name):
				return cart_name
	return ""


func _update_drag(screen_pos: Vector2) -> void:
	var from: Vector3 = camera.project_ray_origin(screen_pos)
	var dir: Vector3 = camera.project_ray_normal(screen_pos)
	var intersection = _drag_plane.intersects_ray(from, dir)
	if intersection == null: return
	var mesh: MeshInstance3D = _cartridges[_dragging].get("mesh")
	if mesh:
		mesh.global_position = intersection + _drag_offset
	_sync_cartridge_area(_dragging)


func _try_drop() -> void:
	if _dragging == "": return
	var cart_name := _dragging
	_dragging = ""
	var data: Dictionary = _cartridges.get(cart_name, {})
	var mesh: MeshInstance3D = data.get("mesh")
	if mesh == null: return

	var slot: Vector3
	if desk_env.has_node("CartridgeSlot"):
		slot = desk_env.get_node("CartridgeSlot").position
	else:
		slot = Vector3(0, 1.3, -1.2)

	if mesh.position.distance_to(slot) < 0.55:
		_select_cartridge(cart_name)
	else:
		var orig_pos: Vector3 = data.get("original_pos", mesh.position)
		var tween := create_tween()
		tween.set_ease(Tween.EASE_OUT)
		tween.set_trans(Tween.TRANS_CUBIC)
		tween.tween_property(mesh, "position", orig_pos, 0.3)
		tween.tween_callback(func(): _sync_cartridge_area(cart_name))
		mesh.scale = Vector3(1.0, 1.0, 1.0)
		_hovered = ""
		if cartridge_label:
			cartridge_label.text = ""


# ─── Insertion animation → transition ───

func _select_cartridge(cart_name: String) -> void:
	if _is_animating: return
	_is_animating = true
	if instruction_label:
		instruction_label.text = ""
	if cartridge_label:
		cartridge_label.text = ""

	var data: Dictionary = _cartridges.get(cart_name, {})
	var mesh: MeshInstance3D = data.get("mesh")
	var slot: Vector3
	if desk_env.has_node("CartridgeSlot"):
		slot = desk_env.get_node("CartridgeSlot").position
	else:
		slot = Vector3(0, 1.3, -1.2)

	var scene_path: String = CARTRIDGE_INFO.get(cart_name, {}).get("scene", "")

	if mesh:
		var tween := create_tween()
		tween.set_ease(Tween.EASE_IN_OUT)
		tween.set_trans(Tween.TRANS_CUBIC)
		tween.tween_property(mesh, "position", slot, 0.4)
		tween.parallel().tween_property(mesh, "scale", Vector3(0.6, 0.6, 0.6), 0.35)
		tween.tween_callback(func(): _sync_cartridge_area(cart_name))
		await tween.finished

	if scene_path.is_empty():
		return

	GlobalState.current_cartridge = cart_name.to_lower()

	# Direct fade-to-black + scene change
	# (cartridge scene handles its own CRT power-on fade-in)
	var overlay := ColorRect.new()
	overlay.set_anchors_preset(Control.PRESET_FULL_RECT)
	overlay.color = Color.BLACK
	overlay.modulate.a = 0.0
	overlay.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(overlay)

	var ft := create_tween()
	ft.tween_property(overlay, "modulate:a", 1.0, 0.5)
	ft.tween_callback(func():
		get_tree().change_scene_to_file(scene_path)
	)
