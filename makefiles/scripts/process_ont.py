import argparse
import json
import re
import os
from collections import defaultdict

parser = argparse.ArgumentParser()

parser.add_argument('--in_file', type=str, help='input file to read from')
parser.add_argument('--out_file', type=str, help='output file to read from')
parser.add_argument('--convert_to', choices=['tsv', 'json'], help='')
parser.add_argument('--experiment', help='experiment')

args = parser.parse_args()

if not os.path.exists(os.path.dirname(args.out_file)):
    os.makedirs(os.path.dirname(args.out_file))


def clean_value(value):
    value = value.strip()
    if re.match('^\d\s\d$', value):
        value = value[0]
    return value


if args.experiment == 'multiwoz':
    if args.convert_to == 'tsv':
        with open(args.in_file, 'r') as fin:
            ontology = json.load(fin)

        with open(args.out_file, 'w') as fout:
            for key, values in ontology.items():
                for i, val in enumerate(values):
                    fout.write(key + '/' + str(i) + '\t' + val + '\n')

    elif args.convert_to == 'json':
        ontology = defaultdict(list)
        with open(args.in_file, 'r') as fin:
            for line in fin:
                parts = line.strip().split('\t')
                task_name, key, index = parts[0].split('/')
                ontology[key].append(clean_value(parts[1]))

        with open(args.out_file, 'w') as fout:
            ontology = json.dump(ontology, fout, ensure_ascii=False, indent=2)

elif args.experiment == 'risawoz':
    if args.convert_to == 'tsv':
        with open(args.in_file, 'r') as fin:
            ontology = json.load(fin)

        with open(args.out_file, 'w') as fout:
            for domain, slot_values in ontology.items():
                for slot, vals in slot_values.items():
                    for i, val in enumerate(vals):
                        if str(val):
                            fout.write(domain + '-' + slot + '/' + str(i) + '\t' + str(val) + '\n')

    elif args.convert_to == 'json':
        ontology = defaultdict(list)
        with open(args.in_file, 'r') as fin:
            for line in fin:
                parts = line.strip().split('\t')
                # 制片国家/地区
                task_name, *domain_slot, index = parts[0].split('/')
                domain_slot = '/'.join(domain_slot)
                if len(parts) > 1:
                    ontology[domain_slot].append(clean_value(parts[1]))

        processed_ontology = defaultdict(dict)
        for domain_slot, values in ontology.items():
            domain, slot = domain_slot.split('-')
            processed_ontology[domain].update({slot: values})

        with open(args.out_file, 'w') as fout:
            ontology = json.dump(processed_ontology, fout, ensure_ascii=False, indent=2)
