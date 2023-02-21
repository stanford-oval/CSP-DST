import re
import argparse
from pprint import pprint
from collections import OrderedDict
import unicodedata


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument('--eval_set', type=str, default='eval', help='')
    parser.add_argument('--input_data', type=str, default='data/risawoz/eval.tsv', help='')
    parser.add_argument('--pred_result_file', type=str, default='data/risawoz/results/mbart_50/eval/almond_dialogue_nlu.tsv', help='')
    parser.add_argument('--pred_result_e2e_file', type=str, default='data/risawoz/results/mbart_50/eval_e2e/almond_dialogue_nlu.tsv', help='')
    parser.add_argument('--task_name', type=str, default='almond_dialogue_nlu', help='')

    args = parser.parse_args()
    
    eval_set, input_file, output_file, output_e2e_file = args.eval_set, args.input_data, args.pred_result_file, args.pred_result_e2e_file

    input_data = dict()
    with open(input_file) as fp:
        for line in fp:
            try:
                _id, context, sentence, target = line.strip().split('\t')
            except:
                print('**warning:', _id)
            input_data[_id] = (context.strip(), sentence.strip(), target.strip())

    predictions = dict()
    with open(output_file) as fp:
        for line in fp:
            _id, prediction = line.strip().split('\t')[:2]
            predictions[_id] = prediction.strip()
    
    e2e_predictions = dict()
    with open(output_e2e_file) as fp:
        for line in fp:
            _id, e2e_prediction = line.strip().split('\t')[:2]
            e2e_predictions[_id] = e2e_prediction.strip()

    ids = tuple(input_data.keys())

    first_turn_gone_wrong_pred = set()
    first_turn_gone_wrong_e2e = set()
    
    for i, pred in enumerate([predictions, e2e_predictions]):
    
        dlg_stats = {
            'total': 0,
            'ok_initial': 0,
            'ok_full': 0,
        }
        turn_stats = {
            'total': 0,
            'ok': 0,
            'ok_up_to_error': 0
        }
    
        prev_dial_idx = None
        is_ok = True
        is_ok_initial = True
        first_turn_gone_wrong = set()
        for _id in ids:
            dialogue_idx, turn = _id.split('/')
        
            if prev_dial_idx is None or prev_dial_idx != dialogue_idx:
                if prev_dial_idx is not None:
                    dlg_stats['total'] += 1
                    if is_ok:
                        dlg_stats['ok_full'] += 1
                    if is_ok_initial:
                        dlg_stats['ok_initial'] += 1
                prev_dial_idx = dialogue_idx
                is_ok = True
                is_ok_initial = True
    
            target = input_data[_id][2]
            if args.task_name:
                prediction = pred[f'{args.task_name}/' + _id]
            else:
                prediction = pred[_id]
            if prediction.startswith('$dialogue '):
                prediction = prediction[len('$dialogue '):]
            
            turn_stats['total'] += 1
            target = re.sub('\s{2,}', ' ', target)
            prediction = re.sub('\s{2,}', ' ', prediction)
            prediction = unicodedata.normalize('NFD', prediction)
            target = unicodedata.normalize('NFD', target)

            if target == prediction:
                turn_stats['ok'] += 1
                if is_ok:
                    turn_stats['ok_up_to_error'] += 1
            else:
                if is_ok:
                    first_turn_gone_wrong.add(dialogue_idx + '/' + turn)
                is_ok = False
                if turn == '0':
                    is_ok_initial = False
    
        if prev_dial_idx is not None:
            dlg_stats['total'] += 1
            if is_ok:
                dlg_stats['ok_full'] += 1
            if is_ok_initial:
                dlg_stats['ok_initial'] += 1
        
        results = OrderedDict({
            'set': eval_set,
            '# dlgs': dlg_stats['total'],
            '# turns': turn_stats['total'],
            'complete dlgs': dlg_stats['ok_full']/dlg_stats['total'] * 100,
            'first turns': dlg_stats['ok_initial']/dlg_stats['total'] * 100,
            'turn by turn': turn_stats['ok']/turn_stats['total'] * 100,
            'up to error': turn_stats['ok_up_to_error']/turn_stats['total'] * 100,
            'time to first error': turn_stats['ok_up_to_error']/dlg_stats['total'],
        })
        
        pprint(results)


if __name__ == '__main__':
    main()
