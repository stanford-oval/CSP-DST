import re


GENERAL_TYPO = {
    # type
    "guesthouse": "guest house", "guesthouses": "guest house", "guest": "guest house",
    "mutiple sports": "multiple sports",
    "sports": "multiple sports", "mutliple sports": "multiple sports", "swimmingpool": "swimming pool",
    "concerthall": "concert hall",
    "concert": "concert hall", "pool": "swimming pool", "night club": "nightclub", "mus": "museum",
    "ol": "architecture",
    "colleges": "college", "coll": "college", "architectural": "architecture", "musuem": "museum", "churches": "church",
    # area
    "center": "centre", "center of town": "centre", "near city center": "centre", "in the north": "north",
    "cen": "centre", "east side": "east",
    "east area": "east", "west part of town": "west", "ce": "centre", "town center": "centre",
    "centre of cambridge": "centre",
    "city center": "centre", "the south": "south", "scentre": "centre", "town centre": "centre", "in town": "centre",
    "north part of town": "north",
    "centre of town": "centre", "cb30aq": "none",
    # price
    "mode": "moderate", "moderate -ly": "moderate", "mo": "moderate",
    # day
    "next friday": "friday", "monda": "monday",
    # parking
    "free parking": "yes",
    # internet
    "free internet": "yes",
    # star
    "4 star": "4", "4 stars": "4", "0 star rarting": "none",
    # others
    "y": "yes", "any": "dontcare", "n": "no", "does not care": "dontcare",
    "not men": "none", "not": "none", "not mentioned": "none",
    '': "none", "not mendtioned": "none",
    "3 .": "3", "does not": "no", "fun": "none", "art": "none",
    
    # new typos
    "el shaddia guesthouse": "el shaddai",
    "not given": "none",
    "thur": "thursday",
    "sundaymonday": "sunday|monday",
    "mondaythursday": "monday|thursday",
    "fridaytuesday": "friday|tuesday",
    "cheapmoderate": "cheap|moderate"
}


def fix_label_error(key, value):
    if value in GENERAL_TYPO:
        value = GENERAL_TYPO[value]
    
    # miss match slot and value
    if (key == "hotel-type" and value in ["nigh", "moderate -ly priced", "bed and breakfast", "centre", "venetian",
                                          "intern", "a cheap -er hotel"]) or \
            (key == "hotel-internet" and value == "4") or \
            (key == "hotel-price-range" and value in ["2", "100"]) or \
            (key == "attraction-type" and value in ["gastropub", "la raza", "galleria", "gallery", "science", "m"]) or \
            ('area' in key and value == "moderate") or \
            ('day' in key and value == "t"):
        return 'none'
    
    if key == "hotel-type" and value in ["hotel with free parking and free wifi", "4", "3 star hotel"]:
        return 'hotel'
    
    if key == "hotel-star" and value == "3 star hotel":
        return "3"
    
    if (key == 'hotel-book-day' or key == 'restaurant-book-day') and value == 'w':
        return 'wednesday'
    
    if 'area' in key:
        if value == 'no':
            return "north"
        elif value == "we":
            return "west"
        elif value == "cent":
            return "centre"
    
    return value


def remove_extra_spaces(sent):
    for token in ['\t', '\n', ' ']:
        sent = sent.replace(token, ' ')
    sent = re.sub(r'\s{2,}', ' ', sent)
    return sent


def undo_trade_prepro(sentence):
    sentence = re.sub(r' -(ly|s)', r'\1', sentence)
    sentence = re.sub(r'\b24:([0-9]{2})\b', r'00:\1', sentence)
    return sentence


def trans_value(value):
    trans = {
        '': 'none',
    }
    value = value.strip()
    value = trans.get(value, value)
    value = value.replace('’', "'")
    value = value.replace('‘', "'")
    return value


CJK_RANGES = [
    (ord(u"\u3300"), ord(u"\u33ff")),
    (ord(u"\ufe30"), ord(u"\ufe4f")),  # compatibility ideographs
    (ord(u"\uf900"), ord(u"\ufaff")),
    (ord(u"\U0002F800"), ord(u"\U0002fa1f")),  # compatibility ideographs
    (ord(u'\u3040'), ord(u'\u309f')),  # Japanese Hiragana
    (ord(u"\u30a0"), ord(u"\u30ff")),  # Japanese Katakana
    (ord(u"\u2e80"), ord(u"\u2eff")),  # cjk radicals supplement
    (ord(u"\u4e00"), ord(u"\u9fff")),
    (ord(u"\u3400"), ord(u"\u4dbf")),
    (ord(u"\U00020000"), ord(u"\U0002a6df")),
    (ord(u"\U0002a700"), ord(u"\U0002b73f")),
    (ord(u"\U0002b740"), ord(u"\U0002b81f")),
    (ord(u"\U0002b820"), ord(u"\U0002ceaf")),
]

CJK_ADDONS = [ord(u"\u3001"), ord('，'), ord('。'), ord('！'), ord('？')]


def is_cjk_char(cp):
    return cp in CJK_ADDONS or any([range[0] <= cp <= range[1] for range in CJK_RANGES])


def detokenize_cjk_chars(sentence):
    output = []
    i = 0
    while i < len(sentence):
        output.append(sentence[i])
        # skip space after cjk chars only if followed by another cjk char
        if (
            is_cjk_char(ord(sentence[i]))
            and i + 1 < len(sentence)
            and sentence[i + 1] == ' '
            and i + 2 < len(sentence)
            and is_cjk_char(ord(sentence[i + 2]))
        ):
            i += 2
        else:
            i += 1

    return "".join(output)

