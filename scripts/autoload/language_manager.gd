extends Node
## Manages language switching between Chinese (zh) and Japanese (ja).

enum Language { CHINESE, JAPANESE }
var current_language: Language = Language.CHINESE

var _ui_strings: Dictionary = {}
var _dialogue_strings: Dictionary = {}

# ─── Font resources ───
var font_zh: FontFile
var font_ja: FontFile
var font_latin: FontFile
var font_pixel_default: FontFile
var font_title_sans: FontFile  # Bold sans-serif for "ΠΑΝΗΓΥΡΙΣ" title card
var font_fallback: FontFile   # Fallback for rare CJK chars not in Fusion Pixel


func _ready() -> void:
	_load_fonts()
	_load_ui_strings()
	apply_language(current_language)


func _load_fonts() -> void:
	font_zh = load("res://assets/fonts/fusion-pixel-12px-proportional-zh_hans.otf")
	font_ja = load("res://assets/fonts/fusion-pixel-12px-proportional-ja.otf")
	font_latin = load("res://assets/fonts/fusion-pixel-12px-proportional-latin.otf")
	font_pixel_default = font_zh
	# Dedicated title path for "ΠΑΝΗΓΥΡΙΣ"; replace with a true bold sans asset later.
	font_title_sans = font_latin if font_latin else font_zh
	font_fallback = font_zh


func _load_ui_strings() -> void:
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
			"insert_cartridge": "插入卡带",
			"eject_cartridge": "弹出卡带",
			"cartridge_select": "选择卡带",
			"fridge_empty": "看来是没有什么可以吃的东西了",
			"climb_rung": "点击攀爬",
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
			"new_game": "はじめる",
			"insert_cartridge": "カートリッジを入れる",
			"eject_cartridge": "カートリッジを取り出す",
			"cartridge_select": "カートリッジ選択",
			"fridge_empty": "食べ物は何もなさそうだ",
			"climb_rung": "クリックして登る",
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
	var lang_key = "zh" if current_language == Language.CHINESE else "ja"
	if _ui_strings.has(lang_key) and _ui_strings[lang_key].has(key):
		return _ui_strings[lang_key][key]
	return key


func get_current_font() -> FontFile:
	return font_pixel_default


func get_title_font() -> FontFile:
	return font_title_sans


func get_fallback_font() -> FontFile:
	return font_fallback if font_fallback else font_pixel_default


func supports_glyph(font: FontFile, char_code: int) -> bool:
	if font == null: return false
	return font.has_char(char_code)


func get_color_for_character(character_id: String) -> Color:
	match character_id:
		"emida", "エミダー", "埃弥亣":
			return Color("3FA943")  # signal green
		_:
			return Color("E8F8E5")  # pale mint for all others
