####################################################################################################################
##### translate dialogs using NMT models ###################################################################
####################################################################################################################

model_name_or_path=Helsinki-NLP/opus-mt-$(src_lang)-$(tgt_lang)
#model_name_or_path=facebook/mbart-large-50-one-to-many-mmt
# model_name_or_path=facebook/mbart-large-50-many-to-many-mmt
#model_name_or_path=facebook/m2m100_418M

src_lang=
tgt_lang=
aug_lang=

nmt_model=nmt

$(experiment)/$(nmt_model)/$(tgt_lang)/unquoted-qpis-translated-uttr:
	rm -rf ./$(experiment)/source/aug-$(aug_lang)/unquoted-qpis-$(nmt_model)/almond/
	mkdir -p ./$(experiment)/source/aug-$(aug_lang)/unquoted-qpis-$(nmt_model)/almond/
	ln -f ./$(experiment)/source/aug-$(aug_lang)/unquoted-qpis-$(nmt_model)-uttr/*.tsv ./$(experiment)/source/aug-$(aug_lang)/unquoted-qpis-$(nmt_model)/almond/
	if ! $(skip_translation) ; then \
		for f in $(all_names) ; do \
			if [ ! -f $(GENIENLP_EMBEDDINGS)/$(model_name_or_path)/best.pth ] ; then \
				$(genienlp) train --replace_qp --force_replace_qp --eval_set_name eval --override_question= --train_iterations 0 --train_tasks almond_translate --train_languages $(src_lang) --train_tgt_languages $(tgt_lang) --eval_languages $(src_lang) --eval_tgt_languages $(tgt_lang) --model TransformerSeq2Seq --pretrained_model $(model_name_or_path) --save $(GENIENLP_EMBEDDINGS)/$(model_name_or_path)/ --embeddings $(GENIENLP_EMBEDDINGS) --exist_ok --skip_cache --no_commit --preserve_case ; \
			fi ; \
			$(genienlp) predict --pred_set_name $$f --translate_no_answer  --tasks almond_translate --data ./$(experiment)/source/aug-$(aug_lang)/unquoted-qpis-$(nmt_model)/ --eval_dir $@/  --evaluate valid --pred_languages $(src_lang) --pred_tgt_languages $(tgt_lang) --path $(GENIENLP_EMBEDDINGS)/$(model_name_or_path)/ --overwrite --silent $(default_translation_hparams) || exit 1 ; \
			mv $@/valid/almond_translate.tsv $@/$$f.tsv ; rm -rf $@/valid ; \
		done ; \
	fi
	rm -rf ./$(experiment)/source/aug-$(aug_lang)/unquoted-qpis-$(nmt_model)/almond/

$(experiment)/$(nmt_model)/$(tgt_lang)/unquoted-qpis-translated-agent:
	rm -rf ./$(experiment)/source/aug-$(aug_lang)/unquoted-qpis-$(nmt_model)/almond/
	mkdir -p ./$(experiment)/source/aug-$(aug_lang)/unquoted-qpis-$(nmt_model)/almond/
	ln -f ./$(experiment)/source/aug-$(aug_lang)/unquoted-qpis-$(nmt_model)-agent/*.tsv ./$(experiment)/source/aug-$(aug_lang)/unquoted-qpis-$(nmt_model)/almond/
	if ! $(skip_translation) ; then \
		for f in $(all_names) ; do \
			if [ ! -f $(GENIENLP_EMBEDDINGS)/$(model_name_or_path)/best.pth ] ; then \
				$(genienlp) train --replace_qp --force_replace_qp --eval_set_name eval --override_question= --train_iterations 0 --train_tasks almond_translate --train_languages $(src_lang) --train_tgt_languages $(tgt_lang) --eval_languages $(src_lang) --eval_tgt_languages $(tgt_lang) --model TransformerSeq2Seq --pretrained_model $(model_name_or_path) --save $(GENIENLP_EMBEDDINGS)/$(model_name_or_path)/ --embeddings $(GENIENLP_EMBEDDINGS) --exist_ok --skip_cache --no_commit --preserve_case ; \
			fi ; \
			$(genienlp) predict --pred_set_name $$f --translate_no_answer  --tasks almond_translate --data ./$(experiment)/source/aug-$(aug_lang)/unquoted-qpis-$(nmt_model)/ --eval_dir $@/  --evaluate valid --pred_languages $(src_lang) --pred_tgt_languages $(tgt_lang) --path $(GENIENLP_EMBEDDINGS)/$(model_name_or_path)/ --overwrite --silent $(default_translation_hparams) || exit 1 ; \
			mv $@/valid/almond_translate.tsv $@/$$f.tsv ; rm -rf $@/valid ; \
		done ; \
	fi
	rm -rf ./$(experiment)/source/aug-$(aug_lang)/unquoted-qpis-$(nmt_model)/almond/


$(experiment)/$(nmt_model)/$(tgt_lang)/unquoted-qpis-refined: $(experiment)/$(nmt_model)/$(tgt_lang)/unquoted-qpis-translated-uttr $(experiment)/$(nmt_model)/$(tgt_lang)/unquoted-qpis-translated-agent
	mkdir -p $@
	# insert programs (and context)
	for f in $(all_names) ; do \
		data_size=`cat ./$(experiment)/source/aug-$(aug_lang)/unquoted-qpis-$(nmt_model)-slotvals/$$f.tsv | wc -l` ; \
		if [ $$f == $(train_name) ] ; then \
			num_output_per_example=$(train_output_per_example) ; \
		else \
			num_output_per_example=$(evaltest_output_per_example) ; \
		fi ; \
		paste <(awk "{for(i=0;i<$$num_output_per_example;i++)print}" <(cut -f1 ./$(experiment)/source/aug-$(aug_lang)/unquoted-qpis/$$f.tsv)) \
		 <(paste -d ' ' <(cut -f2 ./$(experiment)/source/aug-$(aug_lang)/unquoted-qpis-$(nmt_model)-slotvals/$$f.tsv) \
		 <(awk "{for(i=0;i<$$data_size;i++)print}" <(echo ";")) \
		 <(cut -f2 ./$(experiment)/$(nmt_model)/$(tgt_lang)/unquoted-qpis-translated-agent/$$f.tsv)) \
		 <(cut -f2 ./$(experiment)/$(nmt_model)/$(tgt_lang)/unquoted-qpis-translated-uttr/$$f.tsv) \
		 <(awk "{for(i=0;i<$$num_output_per_example;i++)print}" <(cut -f4 ./$(experiment)/source/aug-$(aug_lang)/unquoted-qpis/$$f.tsv)) \
		 > $@/$$f.tsv.tmp ; \
	done

	# refine sentence
	for f in $(all_names) ; do python3 $(ml_scripts)/text_edit.py --experiment $(experiment) --refine_sentence --post_process_translation --experiment $(experiment) --param_language $(tgt_lang) --num_columns 4 --input_file $@/$$f.tsv.tmp --output_file $@/$$f.tsv ; done

	rm -rf $@/*.tsv.tmp


$(experiment)/$(nmt_model)/$(tgt_lang)/unquoted-qpis: $(experiment)/$(nmt_model)/$(tgt_lang)/unquoted-qpis-refined
	mkdir -p $@
	# fix punctuation and clean dataset
	for f in $(all_names) ; do python3 $(ml_scripts)/text_edit.py --experiment $(experiment) --insert_space_quotes --num_columns 4 --input_file $</$$f.tsv --output_file $@/$$f.tsv ; done


$(experiment)/$(nmt_model)/$(tgt_lang)/unquoted: $(experiment)/$(nmt_model)/$(tgt_lang)/unquoted-qpis
	mkdir -p $@
	# remove quotation marks in the sentence
	for f in $(all_names) ; do python3 $(ml_scripts)/text_edit.py --experiment $(experiment) --remove_qpis --num_columns 4 --input_file $</$$f.tsv  --output_file $@/$$f.tsv  ; done


$(experiment)/$(nmt_model)/$(tgt_lang)/quoted: $(experiment)/$(nmt_model)/$(tgt_lang)/unquoted
	mkdir -p $@
	# requote dataset (if successful, verifies parameters match in the sentence and in the program) (collect errors in a separate file)
	for f in $(all_names) ; do \
		if ( [ $$f == $(train_name) ] || [ $$f == "train_missed_qa" ] ); then \
			python3 $(ml_scripts)/dialogue_edit.py --mode requote --src_lang $(src_lang) --tgt_lang $(tgt_lang) --experiment $(experiment) --ontology $($(experiment)_ontology)/$(tgt_lang)/ontology.json --input_path $</$$f.tsv --output_path $@/$$f.tsv ; \
		else \
			python3 $(ml_scripts)/dialogue_edit.py --mode requote --src_lang $(src_lang) --tgt_lang $(tgt_lang) --experiment $(experiment) --ontology $($(experiment)_ontology)/$(tgt_lang)/ontology.json --input_path $</$$f.tsv --output_path $@/$$f.tsv ; \
		fi ; \
	done


$(experiment)/$(nmt_model)/$(tgt_lang)/augmented: $(experiment)/$(nmt_model)/$(tgt_lang)/quoted
	mkdir -p $@
	echo "Number of lines survived so far! :"
	for f in $(all_names) ; do echo "$$f" ; wc -l $(experiment)/$(nmt_model)/$(tgt_lang)/quoted/$$f.tsv ; done
	# augment dataset in target language
	for f in $(all_names) ; do \
		if ( [ $$f == $(train_name) ] ); then \
			python3 $(ml_scripts)/dialogue_edit.py --mode augment --src_lang $(src_lang) --tgt_lang $(tgt_lang) --experiment $(experiment) --ontology $($(experiment)_ontology)/$(tgt_lang)/ontology.json --input_path $</$$f.tsv --output_path $@/$$f.tsv ; \
		else \
			python3 $(ml_scripts)/dialogue_edit.py --mode augment --src_lang $(src_lang) --tgt_lang $(tgt_lang) --experiment $(experiment) --ontology $($(experiment)_ontology)/$(tgt_lang)/ontology.json --input_path $</$$f.tsv --output_path $@/$$f.tsv  ; \
		fi ; \
	done

$(experiment)/$(nmt_model)/$(tgt_lang)/final-qpis: $(experiment)/$(nmt_model)/$(tgt_lang)/augmented
	mkdir -p $@
	# qpis dataset
	for f in $(all_names) ; do python3 $(ml_scripts)/dialogue_edit.py --mode qpis --src_lang $(src_lang) --tgt_lang $(tgt_lang) --experiment $(experiment) --ontology $($(experiment)_ontology)/$(tgt_lang)/ontology.json --input_path $</$$f.tsv --output_path $@/$$f.tsv ; done

$(experiment)/$(nmt_model)/$(tgt_lang)/final-cjkspaced: $(experiment)/$(nmt_model)/$(tgt_lang)/final-qpis
	mkdir -p $@
	# remove qpis
	for f in $(all_names) ; do python3 $(ml_scripts)/text_edit.py --experiment $(experiment) --remove_qpis --num_columns 4 --input_file $</$$f.tsv  --output_file $@/$$f.tsv  ; done


$(experiment)/$(nmt_model)/$(tgt_lang)/final: $(experiment)/$(nmt_model)/$(tgt_lang)/final-cjkspaced
	mkdir -p $@
	# remove cjk spaces
	for f in $(all_names) ; do python3 $(ml_scripts)/text_edit.py --experiment $(experiment) --fix_spaces_cjk --translate_slot_names --experiment $(experiment) --param_language $(tgt_lang) --num_columns 4 --input_file $</$$f.tsv  --output_file $@/$$f.tsv  ; done

translate_data: $(experiment)/$(nmt_model)/$(tgt_lang)/final
	# done!
	echo $@


####################################################################################################################
####################################################################################################################

translate_ontology: $($(experiment)_ontology)/$(src_lang)/ontology.json
	python3 $(ml_scripts)/process_ont.py --convert_to tsv --experiment $(experiment) --in_file $< --out_file $($(experiment)_ontology)/$(src_lang)/ontology.tsv
	rm -rf tmp/almond/
	mkdir -p tmp/almond/
	mkdir -p $($(experiment)_ontology)/$(src_lang)
	mv $($(experiment)_ontology)/$(src_lang)/ontology.tsv tmp/almond/eval.tsv
	if ! $(skip_translation) ; then \
		for f in $(all_names) ; do \
			if [ ! -f $(GENIENLP_EMBEDDINGS)/$(model_name_or_path)/best.pth ] ; then \
				$(genienlp) train --replace_qp --force_replace_qp --eval_set_name eval --override_question= --train_iterations 0 --train_tasks almond_translate --train_languages $(src_lang) --train_tgt_languages $(tgt_lang) --eval_languages $(src_lang) --eval_tgt_languages $(tgt_lang) --model TransformerSeq2Seq --pretrained_model $(model_name_or_path) --save $(GENIENLP_EMBEDDINGS)/$(model_name_or_path)/ --embeddings $(GENIENLP_EMBEDDINGS) --exist_ok --skip_cache --no_commit --preserve_case ; \
			fi ; \
			$(genienlp) predict --pred_set_name $$f --translate_no_answer  --tasks almond_translate --data tmp/ --eval_dir tmp/  --evaluate valid --pred_languages $(src_lang) --pred_tgt_languages $(tgt_lang) --path $(GENIENLP_EMBEDDINGS)/$(model_name_or_path)/ --overwrite --silent $(default_translation_hparams) || exit 1 ; \
		done ; \
	fi
	python3 $(ml_scripts)/process_ont.py --convert_to json --experiment $(experiment) --in_file tmp/valid/almond_translate.tsv --out_file $($(experiment)_ontology)/$(tgt_lang)/ontology.json
	rm -rf tmp/almond/
	rm -rf $($(experiment)_ontology)/$(tgt_lang)/ontology.tsv

