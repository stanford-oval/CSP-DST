import argparse
import collections
import json
import random
import re

DELIM = '\t'
DONTCARE = 'dontcare'

global_count = 0


def fresh_placeholder():
    global global_count
    retval = '@' + str(global_count)
    global_count += 1
    return retval


class TrieNode:
    def __init__(self):
        self.key = ''
        self.children = {}
    
    def insert(self, word, key, index=0):
        if index >= len(word):
            if self.key == '':
                self.key = sample_value(key, word)
            return self.key
        if word[index] not in self.children:
            self.children[word[index]] = TrieNode()
        return self.children[word[index]].insert(word, key, index + 1)
    
    def print(self, s=''):
        print('%s  key %s' % (s, self.key))
        for k in self.children:
            print('%s%s:' % (s, k))
            self.children[k].print(s + ' ')


# Assumes correct formatting
def process_line(line):
    arr = line.split(DELIM)
    ids = arr[0].split('/')
    assert len(ids), "Wrong id format: Should be ID/TURN."
    
    utt_ind = arr[1].find(';')
    assert utt_ind != -1, "Wrong format: Should be annotation ; agent_utterance."
    agent_str = arr[1][utt_ind + 1:]
    user_str = arr[2]
    
    return ids[0], ids[1], [agent_str, user_str], arr[3]


def update_entities(trie_root, ents_inter):
    entities = {}
    turn_entities = [x.strip() for x in ents_inter.split('=')]
    key = turn_entities[0]
    for substr in turn_entities[1:]:
        first_quote = substr.find('"')
        if first_quote != -1:
            end = substr.find('"', first_quote + 1) + 1
            assert end != -1, 'Mismatched quotes!'
            entity = substr[first_quote + 1:end - 2].strip()
            new_entity = trie_root.insert(entity, key)
            entities[key] = '" ' + str(new_entity) + ' "'
        else:
            dc = substr.find(DONTCARE)
            assert dc != -1, 'Invalid entity format! Should be " val " or dontcare.'
            end = dc + len(DONTCARE)
            entities[key] = DONTCARE
        
        # Next key
        key = substr[end:].strip()
    
    return entities


def replace(utterance, entities):
    confirmed = []
    matches = collections.deque([])
    match = None
    # Find matches
    for i in range(len(utterance)):
        cur_len = len(matches)
        cur_char = utterance[i].lower()
        for j in range(cur_len):
            match = matches.popleft()
            if match[1].key != '':
                # start index, replace string, original length
                confirmed.append((match[0], match[1].key, i - match[0]))
            if cur_char in match[1].children:
                matches.append((match[0], match[1].children[cur_char], i - match[0]))
        if cur_char in entities.children:
            matches.append((i, entities.children[cur_char]))
    if len(matches):
        match = matches.popleft()
        if match[1].key != '':
            # start index, replace string, original length
            confirmed.append((match[0], match[1].key, i - match[0]))

    # Check overlaps
    fully_confirmed = []
    for i in range(len(confirmed)):
        keep = True
        for j in range(len(confirmed)):
            if i == j:
                continue
            # pairwise overlap, choose longer of the two.
            if confirmed[i][0] >= confirmed[j][0] and confirmed[i][2] <= confirmed[j][2]:
                keep = False
        if keep:
            fully_confirmed.append(confirmed[i])

    # Replace
    cursor = 0
    new_utterance = ''
    for (start_ind, replace, orig_len) in confirmed:
        if mode == 'qpis':
            replace = '" ' + replace + ' "'
        new_utterance += utterance[cursor:start_ind] + str(replace)
        cursor = start_ind + orig_len
    if cursor < len(utterance) - 1:
        new_utterance += utterance[cursor:]
    return new_utterance


def is_ignore_key(key):
    # 'Best for the crowd', 'Consumption', 'Price', 'Whether the subway is directly accessible', 'Rating', 'Star rating'
    return key.rsplit(' ', 1)[1] in ['最适合人群', '消费', '价位', '是否地铁直达', '评分', '星级']


def heuristic_value(value):
    translation = {
        'en': ["a lover's date", "friends on a trip", "family kin", "cheap", "medium", "expensive", "yes", "no"],
        'zh': ["情侣约会", "朋友出游", "家庭亲子", "便宜", "中等", "偏贵", "是", "否"],
        'fa': ["قرار عاشقی", "دوستان در سفر", "خانوادگی", "ارزان", "متوسط", "گران", "بله", "نه"],
        'uk': ["Пара знайомств", "Дружба на виїзді", "Сімейний батько-дитина", "Дешево", "Середньо", "Частково дорого", "Так", "Ні"],
        'sv': ["Par dejting", "Vänner utflykt", "Familj förälder-barn", "Billigt", "Medium", "Delvis dyrt", "Ja", "Nej"],
        'fi': ["Pari Treffit", "Ystävämatkat", "Perheen vanhempi-lapsi", "Halpa", "Keskitaso", "Osittain kallis", "Kyllä", "Ei"],
        'de': ["Paar-Dating", "Freunde reisen", "Familien-Eltern", "Billig", "Mittel", "Teilweise teuer", "Ja", "Nein"]
    }
    
    ent_to_translate = translation[src_lang]
    ent_tranlation = translation[tgt_lang]
    if value in ent_to_translate:
        index = ent_to_translate.index(value)
        value = ent_tranlation[index]
    
    return value


def sample_value(key, value):
    # don't touch numbers (dates, currency value, confirmation #, etc.)
    if re.match('[0-9]*', value).group():
        return value
    
    # qpis
    if mode == 'qpis':
        return value
    
    # Requote
    elif mode == 'requote':
        if is_ignore_key(key):
            return value
        return fresh_placeholder()
    
    # Augment
    elif mode == 'augment':
        if is_ignore_key(key):
            return heuristic_value(value)
        if re.search('^[0-9]*$', value) is not None:
            return value
        ind = key.find(' ')
        assert ind != -1, "Bad slot key."
        key = key[0:ind] + '-' + key[ind + 1:]
        if key not in ontology:
            return value
        values = ontology[key]
        return values[random.randint(0, len(values) - 1)]


def format_line(line_id, turn, context, utterances, entities):
    out_str = line_id + '/' + turn + DELIM
    if context == 'null' or not context:
        out_str += "null" + " "
    else:
        for key in context:
            out_str += key + " = " + context[key] + " "
    out_str += ';'
    for utterance in utterances:
        # make sure there's one space on each side of quotation marks
        utterance = re.sub(r'\s?"\s?', r' " ', utterance)
        out_str += utterance + DELIM
    if entities:
        for key in entities:
            out_str += key + " = " + entities[key] + " "
    else:
        out_str += 'null'
    return out_str + "\n"


def main(args):
    print('Writing to file %s\n' % (args.output_path))
    
    curr_id = ''
    entities = TrieNode()
    context = 'null'
    with open(args.input_path, 'r') as data, open(args.output_path, 'w') as out:
        for line in data:
            line_id, turn, utterances, ents_inter = process_line(line)
            if line_id != curr_id:
                curr_id = line_id
                entities = TrieNode()
                context = 'null'
            
            turn_entities = update_entities(entities, ents_inter)
            new_utterances = [replace(utter, entities) for utter in utterances]
            
            out.write(format_line(line_id, turn, context, new_utterances, turn_entities))
            context = turn_entities


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--input_path', default="./data_raw", type=str)
    parser.add_argument('--output_path', default="./data_repl", type=str)
    parser.add_argument('--ontology', type=str)
    parser.add_argument('--mode', default='requote', choices=['requote', 'augment', 'qpis'], type=str)
    parser.add_argument('--experiment', default='multiwoz', choices=['multiwoz', 'multiwoz2.4', 'risawoz', 'multiwoz_zh_hum', 'sgd_nlg'],
                        type=str)
    parser.add_argument('--seed', default=123, type=int)
    parser.add_argument('--src_lang', type=str)
    parser.add_argument('--tgt_lang', type=str)
    
    args = parser.parse_args()
    
    random.seed(args.seed)
    
    global ontology
    global src_lang
    global tgt_lang
    global mode
    
    if args.ontology:
        if args.experiment == 'multiwoz2.4':
            with open(args.ontology, 'r') as fin:
                ontology = json.load(fin)
            processed_ont = {}
            for key, value in ontology.items():
                #TODO
                pass
        
        elif 'multiwoz' in args.experiment:
            with open(args.ontology, 'r') as fin:
                ontology = json.load(fin)
        elif args.experiment == 'risawoz':
            with open(args.ontology, 'r') as fin:
                ontology = json.load(fin)
                processed_ontology = {}
                for key, type_vals in ontology.items():
                    for type, values in type_vals.items():
                        processed_ontology[key + '-' + type] = values
                ontology = processed_ontology
        
        elif args.experiment == 'sgd_nlg':
            with open(args.ontology, 'r') as fin:
                ontology = json.load(fin)
                processed_ontology = {}
                for domain in ontology.keys():
                    for intent in ontology[domain].keys():
                        for slot, values in ontology[domain][intent].items():
                            processed_ontology[domain + '-' + intent + '-' + slot] = values
                
                ontology = processed_ontology
    
    src_lang = args.src_lang
    tgt_lang = args.tgt_lang
    mode = args.mode
    
    main(args)
