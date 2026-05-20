extends Node
## Audio manager — BGM, SFX, ambient channels.

enum Bus { MASTER = 0, BGM = 1, SFX = 2, AMBIENT = 3 }

var _bgm_player: AudioStreamPlayer
var _ambient_player: AudioStreamPlayer
var _sfx_players: Array[AudioStreamPlayer] = []
var _heartbeat_player: AudioStreamPlayer


func _ready() -> void:
	_setup_buses()
	_create_players()


func _setup_buses() -> void:
	# Ensure audio buses exist (created in default_bus_layout.tres or via editor)
	var master_idx = AudioServer.get_bus_index("Master")
	if master_idx == -1:
		return
	AudioServer.set_bus_volume_db(master_idx, linear_to_db(GlobalState.master_volume))


func _create_players() -> void:
	_bgm_player = AudioStreamPlayer.new()
	_bgm_player.bus = "BGM" if _bus_exists("BGM") else "Master"
	add_child(_bgm_player)

	_ambient_player = AudioStreamPlayer.new()
	_ambient_player.bus = "Ambient" if _bus_exists("Ambient") else "Master"
	add_child(_ambient_player)

	_heartbeat_player = AudioStreamPlayer.new()
	_heartbeat_player.bus = "SFX" if _bus_exists("SFX") else "Master"
	add_child(_heartbeat_player)


func _bus_exists(bus_name: String) -> bool:
	return AudioServer.get_bus_index(bus_name) != -1


func play_bgm(stream: AudioStream, fade_in: float = 1.0) -> void:
	if _bgm_player.playing:
		_bgm_player.stop()
	_bgm_player.stream = stream
	_bgm_player.volume_db = linear_to_db(0.0)
	_bgm_player.play()


func stop_bgm(fade_out: float = 2.0) -> void:
	_bgm_player.stop()


func play_ambient(stream: AudioStream) -> void:
	_ambient_player.stream = stream
	_ambient_player.play()


func stop_ambient() -> void:
	_ambient_player.stop()


func play_sfx(stream: AudioStream, volume_db: float = 0.0) -> void:
	var player = AudioStreamPlayer.new()
	player.bus = "SFX" if _bus_exists("SFX") else "Master"
	player.stream = stream
	player.volume_db = volume_db
	player.finished.connect(player.queue_free)
	add_child(player)
	player.play()
	_sfx_players.append(player)


func play_heartbeat(bpm: float = 60.0) -> void:
	# Placeholder — will be replaced with actual heartbeat audio
	pass


func stop_heartbeat() -> void:
	_heartbeat_player.stop()
