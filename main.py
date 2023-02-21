import ujson
from collections import defaultdict

from makefiles.scripts.utils import *

class BaseDataset(object):
    def __init__(self, name, dlg_format='original'):
        self.name = name
        self.dlg_format = dlg_format
    
    def process_user_uttr(self, sent):
        raise NotImplementedError
    
    def process_agent_uttr(self, sent):
        raise NotImplementedError
    
    def get_splits(self, **kwargs):
        raise NotImplementedError
    
    def get_ex_id(self, dial_id, idx):
        raise NotImplementedError
    
    def get_ontology(self, file):
        raise NotImplementedError
    
    def process_state(self, state, **kwargs):
        raise NotImplementedError
    
    def state_dict2text(self, state, filtered=()):
        keys = list(state.keys())
        keys.sort()
    
        context = []
        for key in keys:
            value = state[key]
            if value in filtered:
                continue
            if value is None:
                continue
            if value == '':
                context.append(f'{key.replace("-", " ")} = " "')
            else:
                context.append(f'{key.replace("-", " ")} = " {value} "')
            
            context.append(',')
    
        if len(context) == 0:
            return 'null'
    
        return ' '.join(context).strip(', ')

    def create_text_acts(self, acts, filtered=()):
        keys = list(acts.keys())
        keys.sort()
    
        context = []
        for key in keys:
            value = acts[key]
            if value in filtered:
                continue
            if value is None:
                continue
            if value == '':
                context.append(f'{key.replace("-", " ")} = " "')
            else:
                context.append(f'{key.replace("-", " ")} = " {value} "')
    
        if len(context) == 0:
            return 'null'
    
        return ' '.join(context)


class MultiWOZ_21(BaseDataset):
    def __init__(self, name='multiwoz2.1', dlg_format='processed'):
        super().__init__(name, dlg_format)

    def process_user_uttr(self, sent):
        return remove_extra_spaces(undo_trade_prepro(sent))

    def process_agent_uttr(self, sent):
        return remove_extra_spaces(undo_trade_prepro(sent))

    def get_splits(self):
        return [split + '_dials.json' for split in ['train', 'dev', 'test']]
    
    def get_ex_id(self, dial_id, idx):
        return f'{dial_id}/{idx}'

    def get_ontology(self, file):
        raise NotImplementedError

    def process_state(self, state, **kwargs):
        belief = {}
        for slot_value in state:
            assert slot_value['act'] == 'inform'
        
            slot, value = slot_value['slots'][0]
        
            assert isinstance(slot, str) and isinstance(value, str)
            
            # normalize so neural model can understand words better
            slot = slot.replace(' ', '-')
            slot = slot.replace('pricerange', 'price-range')
            value = fix_label_error(slot, value)
            if value == 'none':
                value = None
            if any(slot.startswith(domain) for domain in ['hospital', 'bus', 'police']):
                value = None
            
            if value:
                belief[slot] = value
        
        return belief
    
    def state_dict2text(self, slot_values, filtered=('none')):
        return super().state_dict2text(slot_values, filtered)

    def process_agent_acts(self, acts_dict, ontology=None, **kwargs):
        acts = defaultdict(dict)
        for key, value in acts_dict.items():
            assert key.count('-') == 2
            domain, intent, slot = key.split('-', 2)

            # EXPERIMENT_DOMAINS = ["hotel", "train", "restaurant", "attraction", "taxi"]

            if slot in ['none', 'nooffer', 'ref']:
                continue
            if value in ['none']:
                value = None
            # if domain not in EXPERIMENT_DOMAINS:
            #     value = None

            if value:
                # belief[domain][slot] = value
                acts[key] = value

        return acts


class MultiWOZ_24(BaseDataset):
    def __init__(self, name='multiwoz2.4', dlg_format='processed'):
        super().__init__(name, dlg_format)
    
    def process_user_uttr(self, sent):
        return remove_extra_spaces(sent)
    
    def process_agent_uttr(self, sent):
        return remove_extra_spaces(sent)
    
    def get_splits(self):
        return [split + '_dials.json' for split in ['dev', 'train', 'test']]
    
    def get_ex_id(self, dial_id, idx):
        return f'{dial_id}/{idx}'
    
    def get_ontology(self, file):
        raise NotImplementedError
    
    def process_state(self, state, **kwargs):
        belief = defaultdict(dict)
        for slot_value in state:
            assert slot_value['act'] == 'inform'
            
            assert len(slot_value['slots']) == 1
            domain_slot, value = slot_value['slots'][0]
            assert domain_slot.count('-') == 1
            domain, slot = domain_slot.split('-')
            
            assert isinstance(slot, str) and isinstance(value, str)
            
            # slot = slot.replace(' ', '-')
            
            # normalize so neural model can understand the words better
            # slot = slot.replace('pricerange', 'price-range')
            EXPERIMENT_DOMAINS = ["hotel", "train", "restaurant", "attraction", "taxi"]

            if value == 'none':
                value = None
            if domain not in EXPERIMENT_DOMAINS:
                value = None
            
            if value:
                # belief[domain][slot] = value
                belief[domain + '-' + slot] = value
        
        return belief
    
    def state_dict2text(self, state, filtered=()):
        return super().state_dict2text(state, filtered)

    def process_agent_acts(self, acts_dict, ontology=None, **kwargs):
        acts = defaultdict(dict)
        for key, value in acts_dict.items():
            assert key.count('-') == 2
            domain, intent, slot = key.split('-', 2)

            # EXPERIMENT_DOMAINS = ["hotel", "train", "restaurant", "attraction", "taxi"]
        
            if slot in ['none', 'nooffer', 'ref']:
                continue
            if value in ['none']:
                value = None
            # if domain not in EXPERIMENT_DOMAINS:
            #     value = None
        
            if value:
                # belief[domain][slot] = value
                acts[key] = value
    
        return acts


class RiSAWOZ(BaseDataset):
    def __init__(self, name='risawoz', dlg_format='processed'):
        super().__init__(name, dlg_format)
    
    def process_user_uttr(self, sent):
        return detokenize_cjk_chars(remove_extra_spaces(sent))
    
    def process_agent_uttr(self, sent):
        return detokenize_cjk_chars(remove_extra_spaces(sent))
    
    def get_splits(self):
        return [split + '.json' for split in ['dst_all_train10000', 'dst_all_dev600', 'dst_all_test600_new']]
    
    def get_ex_id(self, dial_id, idx):
        return f'{dial_id}/{idx}'
    
    def get_ontology(self, file):
        # read risawoz ontology file
        with open(file, "r") as fp_ont:
            data_ont = ujson.load(fp_ont)
        ontology = {}
        for domain, slot_values in data_ont.items():
            if domain not in ontology:
                ontology[domain] = {}
            for slot, values in slot_values.items():
                ontology[domain][slot] = set(list(map(lambda val: str(val).lower(), values)))
        return ontology
    
    def process_state(self, state, ontology=None, **kwargs):
        belief = {}
        for slot_values in state:
            for slot, value in slot_values['slots']:
                domain, slot = slot.split('-')
                if domain not in ontology:
                    print("domain (%s) is not defined" % domain)
                    continue
            
                if slot not in ontology[domain]:
                    print("slot (%s) in domain (%s) is not defined" % (slot, domain))  # bus-arriveBy not defined
                    continue
            
                value = trans_value(value).lower()
                value = detokenize_cjk_chars(value)
            
                if value not in ontology[domain][slot] and value != None:
                    print("%s: value (%s) in domain (%s) slot (%s) is not defined in ontology" % (id, value, domain, slot))
                    value = None
                
                belief[f'{str(domain)}-{str(slot)}'] = value
        
        return belief
    
    def state_dict2text(self, slot_values, filtered=('none', '未提及')):
        return super().state_dict2text(slot_values, filtered)


class CrossWOZ(BaseDataset):
    def __init__(self, name='crosswoz'):
        super().__init__(name)
        self.messages = 'messages'
        self.content = 'content'
        self.state = 'sys_state_init'
    
    def process_user_uttr(self, sent):
        return detokenize_cjk_chars(remove_extra_spaces(sent))
    
    def process_agent_uttr(self, sent):
        return detokenize_cjk_chars(remove_extra_spaces(sent))
    
    def get_splits(self):
        return [split + '.json' for split in ['train', 'val', 'test']]
    
    def get_ex_id(self, dial_id, idx):
        return f'{dial_id}/{idx}'
    
    def get_ontology(self, file):
        # read crosswoz ontology file
        with open(file, "r") as fp_ont:
            data_ont = ujson.load(fp_ont)
        ontology = {}
        facilities = []
        for domain, slot_values in data_ont.items():
            if domain not in ontology:
                ontology[domain] = {}
            for slot, values in slot_values.items():
                ontology[domain][slot] = set(map(str.lower, values))
        return ontology
    
    def process_state(self, state, ontology=None, **kwargs):
        belief = {}
        for domain, slot_val in state.items():
            for slot, value in slot_val.items():
                # skip selected results
                if isinstance(value, list):
                    continue
        
                if domain not in ontology:
                    print("domain (%s) is not defined" % domain)
                    continue
        
                # for each hotel facility we define a boolean slot
                if slot == '酒店设施':
                    for facility in value.split(','):
                        belief[f'{str(domain)}-酒店设施-{str(facility)}'] = '是的'
                else:
                    if slot not in ontology[domain]:
                        print("slot (%s) in domain (%s) is not defined" % (slot, domain))  # bus-arriveBy not defined
                        continue
            
                    value = trans_value(value).lower()
            
                    if value not in ontology[domain][slot] and value != None:
                        print("%s: value (%s) in domain (%s) slot (%s) is not defined in ontology" % (id, value, domain, slot))
                        value = None
                    
                    belief[f'{str(domain)}-{str(slot)}'] = value
            
        return belief
    
    def state_dict2text(self, slot_values, filtered=()):
        return super().state_dict2text(slot_values, ['none', '未提及'])


class CrossWOZ_EN(BaseDataset):
    def __init__(self, name='crosswoz_en'):
        super().__init__(name)
        self.messages = 'messages'
        self.content = 'content'
        self.state = 'sys_state_init'
    
    def process_user_uttr(self, sent):
        return detokenize_cjk_chars(remove_extra_spaces(sent))
    
    def process_agent_uttr(self, sent):
        return detokenize_cjk_chars(remove_extra_spaces(sent))
    
    def get_splits(self):
        return [split + '.json' for split in ['train', 'val', 'test']]
    
    def get_ex_id(self, dial_id, idx):
        return f'{dial_id}/{idx}'
    
    def get_ontology(self, file):
        # read crosswoz ontology file
        with open(file, 'r') as fp_ont:
            data_ont = ujson.load(fp_ont)
        ontology = {}
        facilities = []
        for domain_slot in data_ont:
            domain, slot = domain_slot.split('-', 1)
            if domain not in ontology:
                ontology[domain] = {}
            if slot.startswith('Hotel Facilities'):
                facilities.append(slot.split(' - ')[1].lower())
                continue
            ontology[domain][slot] = set(map(str.lower, data_ont[domain_slot]))
        ontology['Hotel']['facilities'] = facilities
        return ontology
    
    def process_state(self, state, ontology=None, **kwargs):
        belief = {}
        for domain, slots in state.items():
            for slot, value in slots.items():
        
                # skip selected results
                if isinstance(value, list):
                    continue
        
                if domain not in ontology:
                    # print("domain (%s) is not defined" % domain)
                    continue
        
                value = remove_extra_spaces(value)
        
                # for each hotel facility we define a boolean slot
                if slot == 'Hotel Facilities':
                    for facility in value.split(','):
                        if facility:
                            belief[f'{str(domain)}-facilities-{str(facility).strip().lower()}'] = 'yes'
                else:
                    if slot not in ontology[domain]:
                        # print("slot (%s) in domain (%s) is not defined" % (slot, domain))  # bus-arriveBy not defined
                        continue
            
                    value = trans_value(value).lower()
            
                    if value not in ontology[domain][slot] and value != None:
                        # print("%s: value (%s) in domain (%s) slot (%s) is not defined in ontology" % (id, value, domain, slot))
                        value = None
            
                    belief[f'{str(domain)}-{str(slot)}'] = value
        
        return belief
    
    def state_dict2text(self, slot_values, filtered=()):
        return super().state_dict2text(slot_values, ['none', '未提及'])


class MultiWOZ_ZH(BaseDataset):
    def __init__(self, name='multiwoz_zh'):
        super().__init__(name)
        self.messages = 'log'
        self.content = 'text'
        self.state = 'metadata'
    
    def process_user_uttr(self, sent):
        return detokenize_cjk_chars(remove_extra_spaces(sent))
    
    def process_agent_uttr(self, sent):
        return detokenize_cjk_chars(remove_extra_spaces(sent))
    
    def get_splits(self):
        return [split + '.json' for split in ['train', 'val', 'test']]
    
    def get_ex_id(self, dial_id, idx):
        return f'{dial_id}/{idx}'
    
    def get_ontology(self, file):
        # read multiwoz_zh ontology file
        with open(file, "r") as fp_ont:
            data_ont = ujson.load(fp_ont)
            ontology = {}
            for domain_slot in data_ont:
                domain, slot = domain_slot.split('-')
                if domain not in ontology:
                    ontology[domain] = {}
                ontology[domain][slot] = data_ont[domain_slot]
        return ontology
    
    def process_state(self, metadata, ontology=None, domain=None, **kwargs):
        belief = {}
        for domain in metadata.keys():
            for slot, value in metadata[domain]['semi'].items():
                value = value.strip()
                value = trans_value(value)
        
                if domain not in ontology:
                    # print("domain (%s) is not defined" % domain)
                    continue
        
                if slot not in ontology[domain]:
                    # print("slot (%s) in domain (%s) is not defined" % (slot, domain))  # bus-arriveBy not defined
                    continue
        
                if value not in ontology[domain][slot] and value != '未提及':
                    # print("%s: value (%s) in domain (%s) slot (%s) is not defined in ontology" % (id, value, domain, slot))
                    value = '未提及'
        
                belief[str(domain) + '-' + str(slot)] = value
    
            for slot, value in metadata[domain]['book'].items():
                if slot == 'booked':
                    continue
                if domain == '公共汽车' and slot == '人数' or domain == '列车' and slot == '票价':
                    continue  # not defined in ontology
        
                value = value.strip()
                value = trans_value(value)
        
                if str('预订' + slot) not in ontology[domain]:
                    # print("预订%s is not defined in domain %s" % (slot, domain))
                    continue
        
                if value not in ontology[domain]['预订' + slot] and value != '未提及':
                    # print("%s: value (%s) in domain (%s) slot (预订%s) is not defined in ontology" % (id, value, domain, slot))
                    value = '未提及'
        
                belief[str(domain) + '-预订' + str(slot)] = value
        
        return belief
    
    def state_dict2text(self, slot_values, filtered=()):
        return super().state_dict2text(slot_values, ['none', '未提及'])
