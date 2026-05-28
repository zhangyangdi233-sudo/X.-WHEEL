extends Node
## Audio manager — BGM, SFX, ambient channels.

enum Bus { MASTER = 0, BGM = 1, SFX = 2, AMBIENT = 3 }

const SWITCHABLE_BGM_TRACKS := [
	preload("res://snd/dream_pop_switch_01_lucent_slaps.wav"),
	preload("res://snd/dream_pop_switch_02_soft_orbit.wav"),
	preload("res://snd/dream_pop_switch_03_afterimage_pool.wav"),
]

var _bgm_player: AudioStreamPlayer
var _bgm_stinger_player: AudioStreamPlayer
var _ambient_player: AudioStreamPlayer
var _sfx_players: Array[AudioStreamPlayer] = []
var _heartbeat_player: AudioStreamPlayer
var _switchable_track_index: int = -1


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

	_bgm_stinger_player = AudioStreamPlayer.new()
	_bgm_stinger_player.bus = "BGM" if _bus_exists("BGM") else "Master"
	add_child(_bgm_stinger_player)

	_ambient_player = AudioStreamPlayer.new()
	_ambient_player.bus = "Ambient" if _bus_exists("Ambient") else "Master"
	add_child(_ambient_player)

	_heartbeat_player = AudioStreamPlayer.new()
	_heartbeat_player.bus = "SFX" if _bus_exists("SFX") else "Master"
	add_child(_heartbeat_player)


func _bus_exists(bus_name: String) -> bool:
	return AudioServer.get_bus_index(bus_name) != -1


func _unhandled_input(event: InputEvent) -> void:
	if event.is_action_pressed("music_next"):
		next_switchable_track()
		get_viewport().set_input_as_handled()


func play_bgm(stream: AudioStream, fade_in: float = 1.0) -> void:
	if stream == null:
		return
	_prepare_loop(stream)
	if _bgm_player.playing:
		_bgm_player.stop()
	_bgm_player.stream = stream
	var target_volume_db := _volume_to_db(GlobalState.bgm_volume)
	_bgm_player.volume_db = _volume_to_db(0.001) if fade_in > 0.0 else target_volume_db
	_bgm_player.play()
	if fade_in > 0.0:
		var tween := create_tween()
		tween.tween_property(_bgm_player, "volume_db", target_volume_db, fade_in)


func play_switchable_track(index: int = 0, fade_in: float = 1.0) -> void:
	if SWITCHABLE_BGM_TRACKS.is_empty():
		return
	var normalized_index := posmod(index, SWITCHABLE_BGM_TRACKS.size())
	_switchable_track_index = normalized_index
	play_bgm(SWITCHABLE_BGM_TRACKS[normalized_index], fade_in)


func next_switchable_track() -> void:
	var next_index := 0 if _switchable_track_index < 0 else _switchable_track_index + 1
	play_switchable_track(next_index, 1.0)


func play_bgm_stinger(stream: AudioStream, volume: float = 1.0) -> void:
	if stream == null:
		return
	if _bgm_stinger_player.playing:
		_bgm_stinger_player.stop()
	_bgm_stinger_player.stream = stream
	_bgm_stinger_player.volume_db = _volume_to_db(GlobalState.bgm_volume * volume)
	_bgm_stinger_player.play()


func stop_bgm(fade_out: float = 2.0) -> void:
	if not _bgm_player.playing:
		return
	if fade_out <= 0.0:
		_bgm_player.stop()
		return
	var tween := create_tween()
	tween.tween_property(_bgm_player, "volume_db", _volume_to_db(0.001), fade_out)
	tween.tween_callback(_bgm_player.stop)


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


func _volume_to_db(volume: float) -> float:
	return linear_to_db(clampf(volume, 0.001, 1.0))


func _prepare_loop(stream: AudioStream) -> void:
	if stream is AudioStreamWAV:
		stream.loop_mode = AudioStreamWAV.LOOP_FORWARD
