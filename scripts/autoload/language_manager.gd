extends Node
## Manages language switching between Chinese (zh) and Japanese (ja).

enum Language { CHINESE, JAPANESE }
var current_language: Language = Language.CHINESE

# Loaded translation dictionaries
var _ui_strings: Dictionary = {}
var _dialogue_strings: Dictionary = {}  # keyed by dialogue id

# ─── Font resources (loaded on init) ───
var font_zh: FontFile
var font_ja: FontFile
var font_pixel_default: FontFile


func _ready() -> void:
	_load_fonts()
	_load_ui_strings()
	apply_language(current_language)


func _load_fonts() -> void:
	font_zh = load("res://assets/fonts/fusion-pixel-12px-proportional-zh_hans.otf")
	font_ja = load("res://assets/fonts/fusion-pixel-12px-proportional-ja.otf")
	font_pixel_default = font_zh  # default to Chinese


func _load_ui_strings() -> void:
	# UI strings are embedded here for simplicity; larger games use CSV.
	_ui_strings = {
		"zh": {
			"start_game": "开始游戏",
			"continue": "继续",
			"settings": "设置",
			"language": "语言",
			"save": "存档",
			"load": "读档",
			"quit": "退出",
			"back": "返回",
			"yes": "是",
			"no": "否",
			"chinese": "中文",
			"japanese": "日本語",
			"speak_clearly": "努力说清楚",
			"stay_silent": "保持沉默",
			"transmit": "发射信号",
			"dont_transmit": "不发射",
			"new_game": "新游戏",
		},
		"ja": {
			"start_game": "はじめる",
			"continue": "つづきから",
			"settings": "設定",
			"language": "言語",
			"save": "セーブ",
			"load": "ロード",
			"quit": "終了",
			"back": "もどる",
			"yes": "はい",
			"no": "いいえ",
			"chinese": "中文",
			"japanese": "日本語",
			"speak_clearly": "はっきり話す",
			"stay_silent": "沈黙を守る",
			"transmit": "信号を送信",
			"dont_transmit": "送信しない",
			"new_game": "はじめから",
		}
	}


func apply_language(lang: Language) -> void:
	current_language = lang
	match lang:
		Language.CHINESE:
			font_pixel_default = font_zh
			TranslationServer.set_locale("zh")
		Language.JAPANESE:
			font_pixel_default = font_ja
			TranslationServer.set_locale("ja")


func toggle_language() -> void:
	if current_language == Language.CHINESE:
		apply_language(Language.JAPANESE)
	else:
		apply_language(Language.CHINESE)


func t(key: String) -> String:
	## Returns a UI string in the current language.
	var lang_key = "zh" if current_language == Language.CHINESE else "ja"
	if _ui_strings.has(lang_key) and _ui_strings[lang_key].has(key):
		return _ui_strings[lang_key][key]
	return key  # fallback: show the key itself


func get_current_font() -> FontFile:
	return font_pixel_default


func get_color_for_character(character_id: String) -> Color:
	## Returns the dialogue text color for a given character.
	match character_id:
		"emida", "エミダー", "埃弥亣":
			return Color("3FA943")  # signal green
		_:
			return Color("E8F8E5")  # pale mint for all others
