extends Node
## Language pollution system — corrupts text based on pollution tier.

# ─── Corruption symbols ───
const SYMBOLS := ["#", "@", "￥", "%", "&", "*", "※", "■", "□", "◇", "◆", "△", "▲"]
const FULLWIDTH_SYMBOLS := ["＠", "＃", "％", "＆", "＊", "＿", "ー"]

# Japanese-specific stutter sounds
const JA_STUTTERS := ["あ", "え", "う", "…", "そ、その", "えっと", "あの"]

# Chinese-specific stutter sounds
const ZH_STUTTERS := ["呃", "嗯", "…", "那、那个", "就、就", "这、这"]


func _str_to_chars(text: String) -> Array[String]:
	var chars: Array[String] = []
	for c in text:
		chars.append(c)
	return chars


func _chars_to_string(chars: Array[String]) -> String:
	var result = ""
	for c in chars:
		result += c
	return result


func corrupt_text(text: String, tier: int) -> String:
	## Corrupt the given text based on pollution tier (0-4).
	if text.is_empty(): return ""
	if tier <= 0: return text

	match tier:
		1: return _corrupt_tier_1(text)
		2: return _corrupt_tier_2(text)
		3: return _corrupt_tier_3(text)
		4: return _corrupt_tier_4(text)
	return text


func _corrupt_tier_1(text: String) -> String:
	## Replace 1-2 random characters per sentence with symbols.
	var chars := _str_to_chars(text)
	var num_to_corrupt := maxi(1, chars.size() / 8)
	for _i in num_to_corrupt:
		chars[randi() % chars.size()] = _random_symbol()
	return _chars_to_string(chars)


func _corrupt_tier_2(text: String) -> String:
	## 30-50% of characters replaced; sentences feel broken.
	var chars := _str_to_chars(text)
	var num_to_corrupt := int(chars.size() * randf_range(0.3, 0.5))
	for _i in num_to_corrupt:
		chars[randi() % chars.size()] = _random_symbol()
	return _chars_to_string(chars)


func _corrupt_tier_3(text: String) -> String:
	## Most of the sentence is garbled, only fragments remain readable.
	var chars := _str_to_chars(text)
	var result: Array[String] = []
	var corrupt_ratio := randf_range(0.6, 0.85)

	for i in chars.size():
		if randf() < corrupt_ratio:
			result.append(_random_symbol())
		else:
			result.append(chars[i])

	return _chars_to_string(result)


func _corrupt_tier_4(text: String) -> String:
	## Near-complete corruption — only stutters and broken sounds.
	var is_ja := LanguageManager.current_language == LanguageManager.Language.JAPANESE
	var stutters: Array = JA_STUTTERS if is_ja else ZH_STUTTERS

	var parts: Array[String] = []
	for _i in randi_range(2, 5):
		parts.append(stutters[randi() % stutters.size()])

	# Occasionally a real word breaks through
	if randf() < 0.15:
		var words := text.split(" ")
		if words.size() > 0:
			parts.insert(randi() % parts.size(), words[randi() % words.size()])

	return _chars_to_string(parts)


func _random_symbol() -> String:
	var all_symbols := SYMBOLS + FULLWIDTH_SYMBOLS
	return all_symbols[randi() % all_symbols.size()]


func should_play_stutter_sfx(tier: int) -> bool:
	## Whether to play a stutter sound effect with this tier.
	return tier >= 3 and randf() < 0.3


func get_stutter_audio_hint() -> String:
	## Returns a hint for what kind of stutter SFX to play.
	return "stutter_short"
