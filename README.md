[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-green)](https://github.com/stanford-oval/csp-dst/blob/master/LICENSE)

# Contextual Semantic Parsing for Multilingual Task-Oriented Dialogues
This codebase hosts the implementation for the following paper which is published in EACL 2023.

[_Contextual Semantic Parsing for Multilingual Task-Oriented Dialogues_](https://arxiv.org/abs/2111.02574) <br/> Mehrad Moradshahi, Victoria Tsai, Giovanni Campagna, Monica S. Lam <br/>


## Abstract

In this work, we show that given a large-scale dialogue data set in one language, we can automatically produce an effective semantic parser for other languages using machine translation.
We propose automatic translation of dialogue datasets with alignment to ensure faithful translation of slot values and eliminate costly human supervision used in previous benchmarks. We also propose a new contextual semantic parsing model, which encodes the formal slots and values, and only the last agent and user utterances. 
We show that the succinct representation reduces the compounding effect of translation errors, without harming the accuracy in practice.

We evaluate our approach on several dialogue state tracking benchmarks. On RiSAWOZ, CrossWOZ, CrossWOZ-EN, and MultiWOZ-ZH datasets we improve the state of the art by 11%, 17%, 20%, and 0.3% in joint goal accuracy. We present a comprehensive error analysis for all three datasets showing erroneous annotations can lead to misguided judgments on the quality of the model.

Finally, we present RiSAWOZ English and German datasets, created using our translation methodology. On these datasets, accuracy is within 11% of the original showing that high-accuracy multilingual dialogue datasets are possible without relying on expensive human annotations.

## Quickstart


### Setup
1. Clone the repository into your desired folder:
```bash
git clone https://github.com/stanford-oval/csp-dst.git
```

2. Install genienlp library (used for translation, training, and inference):
```bash
pip3 uninstall -y genienlp
pip3 install git+https://github.com/stanford-oval/genienlp.git@wip/csp-dst
```

3. We use Convlab-2 library to access datasets (besides MultiWOZ 2.4 and RiSAWOZ) and ontology files:
```bash
git clone https://github.com/thu-coai/ConvLab-2.git
```
You may need to unzip data files provided in Convlab-2. For some datasets (e.g. CrossWOZ) you need to run a script included in the library to generate ontology files.

4. To access MultiWOZ 2.4 dataset, run:
```bash
git clone https://github.com/smartyfh/MultiWOZ2.4.git
cd MultiWOZ2.4 ; python3 create_data.py
```

5. To access RiSAWOZ, run the following command and unzip the data files within:
```bash
git clone https://github.com/terryqj0107/RiSAWOZ.git
```

### Translation
Make sure you run the following commands within CSP-DST library root directory.
1. Process and prepare the dataset into our contextual format for training/ translation (We choose RiSAWOZ as the example dataset in this guide, but it can be substituted with other supported datasets).
```bash
python3 woz_to_csp.py --input_folder ./RiSAWOZ/RiSAWOZ-data/task2-data-DST/ --output_folder dataset/risawoz/ --experiment risawoz --ontology_folder ./RiSAWOZ/RiSAWOZ-data/RiSAWOZ-Database-and-Ontology/Ontology/
```

Make sure you run the following commands within makefiles directory.
2. Prepare the dataset for translation:
```bash
cd makefiles
make -B all_names="train eval" aug_lang=zh tgt_lang=en experiment=risawoz process_data
```

3. Translate the ontology:
```bash
mkdir -p ./RiSAWOZ/RiSAWOZ-data/RiSAWOZ-Database-and-Ontology/Ontology/zh/
cp ./RiSAWOZ/RiSAWOZ-data/RiSAWOZ-Database-and-Ontology/Ontology/ontology.json ./RiSAWOZ/RiSAWOZ-data/RiSAWOZ-Database-and-Ontology/Ontology/zh/
make -B all_names="train eval" src_lang=zh tgt_lang=en experiment=risawoz translate_ontology
```

4. Translate the dataset using alignment:
```bash
make -B all_names="train eval" experiment=risawoz src_lang=zh aug_lang=en tgt_lang=en nmt_model=marian translate_data
```
The final dataset will be in `risawoz/marian/en/final` directory.


5. Translate the dataset without alignment (i.e. direct):
```bash
make -B all_names="train eval" experiment=risawoz src_lang=zh aug_lang=en tgt_lang=en nmt_model=marian translate_data_direct
```
The final dataset will be in `risawoz/marian/en/final-direct` directory.

### Training
Run the following commands within CSP-DST library root directory.
1. GenieNLP tasks assume a specific path for the dataset. To comply, first copy the dataset into `data/almond/user/`:
```bash
mkdir -p data/almond/user/
cp -r makefiles/risawoz/marian/en/final/ data/almond/user/
```

2. Train a new model:
```bash
genienlp train \
      --data data
      --save models/mbart/ \
      --train_tasks almond_dialogue_nlu \
      --train_iterations ${train_iterations} \
      --model TransformerSeq2Seq \
      --pretrained_model facebook/mbart-large-50 \
      --train_languages ${data_language} \
      --eval_languages ${data_language}  \
      --eval_set_name eval \
      --preserve_case \
      --exist_ok 
```
For a list of training options run `genienlp train -h`.

### Evaluation
1. Evaluate your trained model using gold data as context:
```bash
genienlp predict \
      --data data \
      --path models/mbart/ \
      --tasks almond_dialogue_nlu \
      --eval_dir models/mbart/pred/ \
      --evaluate valid \
      --pred_set_name eval \
      --overwrite 
```
For a list of prediction options run `genienlp predict -h`.

2. Evaluate your trained model in an end-to-end setting (i.e. using model predictions from previous turns as context):
```bash
genienlp predict \
      --data data \
      --path models/mbart/ \
      --tasks almond_dialogue_nlu \
      --eval_dir models/mbart/pred_e2e/ \
      --evaluate valid \
      --pred_set_name eval \
      --overwrite \
      --csp_feed_pred
```

3. Compute evaluation metrics (and data stats):
```bash
python3 compute_results.py \
        --eval_set eval \
        --input_data data/almond/user/eval.tsv \
        --pred_result_file models/mbart/pred/valid/almond_dialogue_nlu.tsv \
        --pred_result_e2e_file  models/mbart/pred_e2e/valid/almond_dialogue_nlu.tsv
```

The results will be printed on the terminal in a dictionary format. First and second dictionaries show `pred` and `pred_e2e` results respectively:
- **set**: the evaluation set name
- **\# dlgs**: number of dialogues in the evaluation set
- **\# turns**: number of turns in the evaluation set
- **complete dlgs**: fraction of dialogues for which all turns were predicted correctly
- **first turns**: fraction of dialogues for which first turn was predicted correctly
- **turn by turn**: fraction of turns predicted correctly (in the paper, it's referred to as *GJGA* when gold input is used during evaluation and *JGA* otherwise)
- **up to error**: accuracy up to the first incorrect prediction
- **time to first error**: average turn at which the first incorrect prediction occurs 

## Pretrained models and datasets

You can download our datasets and pretrained models from [link](https://drive.google.com/drive/folders/13NBVwd20Vah97i1Xn39TAdNFuV45m_BI?usp=sharing).
Please refer to our [paper](https://arxiv.org/pdf/2111.02574.pdf) for more details on the dataset and experiments.


## Citation
If you use our data or the software in this repository, please cite:
```
@inproceedings{moradshahi-etal-2020-localizing,
    title = "Contextual Semantic Parsing for Multilingual Task-Oriented Dialogues",
    author = "Moradshahi, Mehrad and Tsai, Victoria and Campagna, Giovanni and Lam, Monica S",
    booktitle = "Proceedings of the 2023 Conference of the European Chapter of the Association for Computational Linguistics (EACL)",
    publisher = "Association for Computational Linguistics",
}
```
