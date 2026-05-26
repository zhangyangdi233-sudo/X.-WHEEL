extends Node
## Language pollution system — corrupts text based on pollution tier.
## Extended with structured memory text degradation pipeline.

# ─── Corruption symbols ───
const SYMBOLS := ["#", "@", "￥", "%", "&", "*", "※", "■", "□", "◇", "◆", "△", "▲"]
const FULLWIDTH_SYMBOLS := ["＠", "＃", "％", "＆", "＊", "＿", "ー"]
const EXTENDED_SYMBOLS := ["∎", "▣", "⬚", "◈", "⌬", "⬡", "⎔", "⬢"]

# Japanese-specific stutter sounds
const JA_STUTTERS := ["あ", "え", "う", "…", "そ、その", "えっと", "あの"]

# Chinese-specific stutter sounds
const ZH_STUTTERS := ["呃", "嗯", "…", "那、那个", "就、就", "这、这"]

# ─── Script mapping for memory degradation Tier 1 ───
# Simplified → Traditional (commonly used characters)
const ZH_SIMP_TO_TRAD := {
	"国": "國", "体": "體", "学": "學", "觉": "覺", "电": "電",
	"脑": "腦", "关": "關", "门": "門", "车": "車", "马": "馬",
	"鱼": "魚", "鸟": "鳥", "龙": "龍", "风": "風", "东": "東",
	"为": "為", "时": "時", "书": "書", "见": "見", "说": "説",
	"话": "話", "过": "過", "还": "還", "对": "對", "发": "發",
	"开": "開", "红": "紅", "万": "萬", "与": "與", "个": "個",
	"没": "沒", "这": "這", "后": "後", "会": "會", "经": "經",
	"长": "長", "间": "間", "头": "頭", "实": "實", "气": "氣",
}
# Hiragana → Katakana mapping for Japanese degradation Tier 1
const JA_HIRA_TO_KATA := {
	"あ": "ア", "い": "イ", "う": "ウ", "え": "エ", "お": "オ",
	"か": "カ", "き": "キ", "く": "ク", "け": "ケ", "こ": "コ",
	"さ": "サ", "し": "シ", "す": "ス", "せ": "セ", "そ": "ソ",
	"た": "タ", "ち": "チ", "つ": "ツ", "て": "テ", "と": "ト",
	"な": "ナ", "に": "ニ", "ぬ": "ヌ", "ね": "ネ", "の": "ノ",
	"は": "ハ", "ひ": "ヒ", "ふ": "フ", "へ": "ヘ", "ほ": "ホ",
	"ま": "マ", "み": "ミ", "む": "ム", "め": "メ", "も": "モ",
	"や": "ヤ", "ゆ": "ユ", "よ": "ヨ",
	"ら": "ラ", "り": "リ", "る": "ル", "れ": "レ", "ろ": "ロ",
	"わ": "ワ", "を": "ヲ", "ん": "ン",
	"が": "ガ", "ぎ": "ギ", "ぐ": "グ", "げ": "ゲ", "ご": "ゴ",
	"ざ": "ザ", "じ": "ジ", "ず": "ズ", "ぜ": "ゼ", "ぞ": "ゾ",
	"だ": "ダ", "ぢ": "ヂ", "づ": "ヅ", "で": "デ", "ど": "ド",
	"ば": "バ", "び": "ビ", "ぶ": "ブ", "べ": "ベ", "ぼ": "ボ",
	"ぱ": "パ", "ぴ": "ピ", "ぷ": "プ", "ぺ": "ペ", "ぽ": "ポ",
}

# Rare/obscure characters for Tier 2
const ZH_RARE_CHARS := ["龘", "靐", "齉", "爨", "灪", "麤", "彠", "籲", "鬱", "钃", "鸞", "驫", "纛", "灩", "釁", "蠻"]
const JA_RARE_CHARS := ["鬱", "鸞", "驫", "鲧", "龘", "纛", "爨", "灩", "釁", "蠻", "彠", "籲", "麤", "钃", "靐", "齉"]

# ─── Degradation result cache ───
var _degrade_cache: Dictionary = {}


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


# ─── Standard corruption (NPC dialogue, unchanged from original) ───

func corrupt_text(text: String, tier: int) -> String:
	if text.is_empty(): return ""
	if tier <= 0: return text

	match tier:
		1: return _corrupt_tier_1(text)
		2: return _corrupt_tier_2(text)
		3: return _corrupt_tier_3(text)
		4: return _corrupt_tier_4(text)
	return text


func _corrupt_tier_1(text: String) -> String:
	var chars := _str_to_chars(text)
	var num_to_corrupt := maxi(1, chars.size() / 8)
	for _i in num_to_corrupt:
		chars[randi() % chars.size()] = _random_symbol()
	return _chars_to_string(chars)


func _corrupt_tier_2(text: String) -> String:
	var chars := _str_to_chars(text)
	var num_to_corrupt := int(chars.size() * randf_range(0.3, 0.5))
	for _i in num_to_corrupt:
		chars[randi() % chars.size()] = _random_symbol()
	return _chars_to_string(chars)


func _corrupt_tier_3(text: String) -> String:
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
	var is_ja := LanguageManager.current_language == LanguageManager.Language.JAPANESE
	var stutters := JA_STUTTERS if is_ja else ZH_STUTTERS
	var parts: Array[String] = []
	for _i in randi_range(2, 5):
		parts.append(stutters[randi() % stutters.size()])
	if randf() < 0.15:
		var words := text.split(" ")
		if words.size() > 0:
			parts.insert(randi() % parts.size(), words[randi() % words.size()])
	return _chars_to_string(parts)


func _random_symbol() -> String:
	var all_symbols := SYMBOLS + FULLWIDTH_SYMBOLS
	return all_symbols[randi() % all_symbols.size()]


# ─── Structured memory text degradation (NEW) ───

func degrade_memory_text(text: String, tier: int, lang: int = -1) -> String:
	## Degrades memory text through a structured pipeline. Tier 0=normal → Tier 4=all "……".
	## Uses per-language degradation paths: ZH (繁简混用) vs JA (平假/片假混用).
	if text.is_empty(): return ""
	if tier <= 0: return text
	if tier >= 4: return "…………"

	if lang < 0:
		lang = LanguageManager.current_language

	# Check cache
	var cache_key := "%s|%d|%d" % [text, tier, lang]
	if _degrade_cache.has(cache_key):
		return _degrade_cache[cache_key]

	var result: String = ""
	match tier:
		1: result = _degrade_tier_1(text, lang)
		2: result = _degrade_tier_2(text, lang)
		3: result = _degrade_tier_3(text, lang)
		_: result = text

	_degrade_cache[cache_key] = result
	return result


func _degrade_tier_1(text: String, lang: int) -> String:
	## Mix scripts: simplified→traditional (ZH) or hiragana→katakana (JA) for ~20% of chars.
	var chars := _str_to_chars(text)
	var replace_count := int(chars.size() * 0.2)

	if lang == LanguageManager.Language.JAPANESE:
		var hira_indices: Array[int] = []
		for i in chars.size():
			if chars[i] in JA_HIRA_TO_KATA:
				hira_indices.append(i)
		hira_indices.shuffle()
		for j in mini(replace_count, hira_indices.size()):
			chars[hira_indices[j]] = JA_HIRA_TO_KATA[chars[hira_indices[j]]]
	else:  # Chinese
		# Track which indices are simplified-only (don't replace already-traditional)
		var target_indices := range(chars.size())
		target_indices.shuffle()
		var replaced := 0
		for idx in target_indices:
			if replaced >= replace_count: break
			if chars[idx] in ZH_SIMP_TO_TRAD:
				chars[idx] = ZH_SIMP_TO_TRAD[chars[idx]]
				replaced += 1

	return _chars_to_string(chars)


func _degrade_tier_2(text: String, lang: int) -> String:
	## Replace ~15% of characters with rare/obscure ones.
	var chars := _str_to_chars(text)
	var replace_count := int(chars.size() * 0.15)
	var rare_pool := ZH_RARE_CHARS if lang != LanguageManager.Language.JAPANESE else JA_RARE_CHARS
	var indices := range(chars.size())
	indices.shuffle()
	for j in replace_count:
		if j >= indices.size(): break
		chars[indices[j]] = rare_pool[randi() % rare_pool.size()]

	return _chars_to_string(chars)


func _degrade_tier_3(text: String, _lang: int) -> String:
	## Insert random garbled symbols every 3-4 characters.
	var chars := _str_to_chars(text)
	var result: Array[String] = []
	var all_sym := SYMBOLS + FULLWIDTH_SYMBOLS + EXTENDED_SYMBOLS
	for i in chars.size():
		if i > 0 and (i % maxi(3, randi() % 2 + 3) == 0):
			result.append(all_sym[randi() % all_sym.size()])
		result.append(chars[i])
	return _chars_to_string(result)


func should_play_stutter_sfx(tier: int) -> bool:
	return tier >= 3 and randf() < 0.3


func get_stutter_audio_hint() -> String:
	return "stutter_short"
