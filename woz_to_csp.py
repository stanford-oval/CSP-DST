import argparse
import os
import sys

from main import *

DATASET_MAP = {'multiwoz2.1': 'MultiWOZ_21', 'multiwoz2.4': 'MultiWOZ_24', 'multiwoz_zh': 'MultiWOZ_ZH', 'crosswoz': 'CrossWOZ', 'crosswoz_en': 'CrossWOZ_EN', 'risawoz': 'RiSAWOZ'}

def main():
    parser = argparse.ArgumentParser()

    parser.add_argument('--input_folder', type=str, help='input file to read from')
    # mwoz2.1: ../../ConvLab-2/convlab2/dst/trade/multiwoz/data/
    # mwoz2.4: ../../MultiWOZ2.4/data/mwz2.4/
    # multiwoz_zh: ../../ConvLab-2/data/multiwoz_zh/
    # crosswoz: ../../ConvLab-2/data/crosswoz/
    # crosswoz_en: ../../ConvLab-2/data/crosswoz_en/
    # risawoz: ../../RiSAWOZ/RiSAWOZ-data/task2-data-DST/

    parser.add_argument('--output_folder', type=str, default='', help='output folder')
    parser.add_argument('--experiment', type=str, choices=['multiwoz2.1', 'multiwoz2.4', 'multiwoz_zh', 'crosswoz', 'crosswoz_en', 'risawoz'], help='')

    parser.add_argument('--ontology_folder', type=str, help='ontology folder')
    # checkout project.config for list of ontology dirs

    args = parser.parse_args()

    os.makedirs(args.output_folder, exist_ok=True)

    exp = eval(DATASET_MAP[args.experiment])()

    splits = exp.get_splits()

    ontology = None
    if args.ontology_folder:
        ontology = exp.get_ontology(os.path.join(args.ontology_folder, "ontology.json"))

    for split in splits:
        if 'train' in split:
            out_split = 'train'
        elif 'test' in split:
            out_split = 'test'
        else:
            out_split = 'eval'

        with open(args.output_folder + out_split + '.tsv', 'w') as fout:
            previous_belief = 'null'

            if exp.dlg_format == 'original':
                data = ujson.load(open(os.path.join(args.input_folder, split)))
                for dlg_id, dlg in data.items():
                    content = dlg[exp.messages]
                    turn_idx = 0
                    while turn_idx < len(content):
                        turn = content[turn_idx]
                        next_turn = dlg[exp.messages][turn_idx + 1]
                        previous_turn = None
                        if turn_idx > 0:
                            previous_turn = dlg[exp.messages][turn_idx - 1]

                        user_utterance = turn[exp.content]
                        if previous_turn:
                            sys_utterance = previous_turn[exp.content]
                        else:
                            sys_utterance = ''


                        cur_state = next_turn[exp.state]

                        new_slots = exp.process_state(cur_state, ontology=ontology)

                        user_utterance = exp.process_user_uttr(user_utterance)
                        sys_utterance = exp.process_user_uttr(sys_utterance)

                        belief_state = exp.state_dict2text(new_slots)
                        out_string = f'{dlg_id}/{int(turn_idx / 2)}\t{previous_belief} ;{" " + sys_utterance if sys_utterance else ""}\t{user_utterance}\t{belief_state}\n'

                        fout.write(out_string)
                        previous_belief = belief_state

                        turn_idx += 2

            elif exp.dlg_format == 'sgd':
                data = ujson.load(open(os.path.join(args.input_folder, split)))
                for dlg in data:
                    content = dlg['turns']
                    dlg_id = dlg['dialogue_id']
                    turn_idx = 0
                    while turn_idx < len(content):
                        turn = content[turn_idx]
                        previous_turn = None
                        if turn_idx > 0:
                            previous_turn = content[turn_idx - 1]

                        assert turn['speaker'] == 'user'
                        user_utterance = turn['utterance']
                        if previous_turn:
                            assert previous_turn['speaker'] == 'system'
                            sys_utterance = previous_turn['utterance']
                        else:
                            sys_utterance = ''

                        cur_state = turn['state']

                        new_slots = exp.process_state(cur_state, ontology=ontology)

                        user_utterance = exp.process_user_uttr(user_utterance)
                        sys_utterance = exp.process_user_uttr(sys_utterance)

                        belief_state = exp.state_dict2text(new_slots)
                        out_string = f'{dlg_id}/{int(turn_idx / 2)}\t{previous_belief} ;{" " + sys_utterance if sys_utterance else ""}\t{user_utterance}\t{belief_state}\n'

                        fout.write(out_string)
                        previous_belief = belief_state

                        turn_idx += 2


            elif exp.dlg_format == 'processed':
                data = ujson.load(open(args.input_folder + split, 'r'))
                for dlg in data:
                    dlg_id = dlg['dialogue_idx']
                    content = dlg['dialogue']
                    turn_idx = 0
                    while turn_idx < len(content):
                        turn = content[turn_idx]

                        cur_state = turn['belief_state']

                        new_slots = exp.process_state(cur_state, ontology=ontology)

                        user_utterance = exp.process_user_uttr(turn["transcript"])
                        sys_utterance = exp.process_user_uttr(turn["system_transcript"])

                        belief_state = exp.state_dict2text(new_slots)
                        out_string = f'{dlg_id}/{turn_idx}\t{previous_belief} ;{" " + sys_utterance if sys_utterance else ""}\t{user_utterance}\t{belief_state}\n'

                        fout.write(out_string)
                        previous_belief = belief_state

                        turn_idx += 1

            # star means tsv format (sumbt, etc.)
            elif exp.dlg_format == 'star':
                data = open(args.input_folder + split, 'r')
                previous_last_turn = 'False'
                for i, dlg in enumerate(data):
                    # header
                    if i == 0:
                        _, _, _, _, _, *slots_names = dlg.split('\t')
                        continue

                    dlg_id, turn_num, last_turn, sys_utterance, user_utterance, *slots_values = dlg.strip('\n').split('\t')

                    if previous_last_turn == 'True':
                        previous_belief = 'null'

                    new_slots = exp.process_state(list(zip(slots_names, slots_values)), ontology=ontology)

                    user_utterance = exp.process_user_uttr(user_utterance)
                    sys_utterance = exp.process_user_uttr(sys_utterance)

                    belief_state = exp.state_dict2text(new_slots)
                    out_string = f'{dlg_id}/{turn_num}\t{previous_belief} ;{" " + sys_utterance if sys_utterance else ""}\t{user_utterance}\t{belief_state}\n'

                    fout.write(out_string)
                    previous_belief = belief_state
                    previous_last_turn = last_turn

                    turn_idx += 1


if __name__ == '__main__':
    main()
