####################################################################################################################
##### translate dialogs using NMT models ###################################################################
####################################################################################################################

model_name_or_path=Helsinki-NLP/opus-mt-$(src_lang)-$(tgt_lang)
#model_name_or_path=facebook/mbart-large-50-one-to-many-mmt
#model_name_or_path=facebook/mbart-large-50-many-to-many-mmt

src_lang=
tgt_lang=
aug_lang=


$(experiment)/marian/$(tgt_lang)/unquoted-qpis-translated-uttr-direct:
	rm -rf ./$(experiment)/source/aug-$(aug_lang)/unquoted-qpis-marian/almond/
	mkdir -p ./$(experiment)/source/aug-$(aug_lang)/unquoted-qpis-marian/almond/
	ln -f ./$(experiment)/source/aug-$(aug_lang)/unquoted-qpis-marian-uttr/*.tsv ./$(experiment)/source/aug-$(aug_lang)/unquoted-qpis-marian/almond/
	if ! $(skip_translation) ; then \
		for f in $(all_names) ; do \
			if [ ! -f $(GENIENLP_EMBEDDINGS)/$(model_name_or_path)/direct/best.pth ] ; then \
				$(genienlp) train --eval_set_name eval --override_question= --train_iterations 0 --train_tasks almond_translate --train_languages $(src_lang) --train_tgt_languages $(tgt_lang) --eval_languages $(src_lang) --eval_tgt_languages $(tgt_lang) --model TransformerSeq2Seq --pretrained_model $(model_name_or_path) --save $(GENIENLP_EMBEDDINGS)/$(model_name_or_path)/direct/ --embeddings $(GENIENLP_EMBEDDINGS) --exist_ok --no_commit --preserve_case ; \
			fi ; \
			$(genienlp) predict --pred_set_name $$f --translate_no_answer  --tasks almond_translate --data ./$(experiment)/source/aug-$(aug_lang)/unquoted-qpis-marian/ --eval_dir $@/  --evaluate valid --pred_languages $(src_lang) --pred_tgt_languages $(tgt_lang) --path $(GENIENLP_EMBEDDINGS)/$(model_name_or_path)/direct/ --overwrite --silent $(default_translation_hparams) || exit 1 ; \
			mv $@/valid/almond_translate.tsv $@/$$f.tsv ; rm -rf $@/valid ; \
		done ; \
	fi
	rm -rf ./$(experiment)/source/aug-$(aug_lang)/unquoted-qpis-marian/almond/

$(experiment)/marian/$(tgt_lang)/unquoted-qpis-translated-agent-direct:
	rm -rf ./$(experiment)/source/aug-$(aug_lang)/unquoted-qpis-marian/almond/
	mkdir -p ./$(experiment)/source/aug-$(aug_lang)/unquoted-qpis-marian/almond/
	ln -f ./$(experiment)/source/aug-$(aug_lang)/unquoted-qpis-marian-agent/*.tsv ./$(experiment)/source/aug-$(aug_lang)/unquoted-qpis-marian/almond/
	if ! $(skip_translation) ; then \
		for f in $(all_names) ; do \
			if [ ! -f $(GENIENLP_EMBEDDINGS)/$(model_name_or_path)/best.pth ] ; then \
				$(genienlp) train --replace_qp --force_replace_qp --eval_set_name eval --override_question= --train_iterations 0 --train_tasks almond_translate --train_languages $(src_lang) --train_tgt_languages $(tgt_lang) --eval_languages $(src_lang) --eval_tgt_languages $(tgt_lang) --model TransformerSeq2Seq --pretrained_model $(model_name_or_path) --save $(GENIENLP_EMBEDDINGS)/$(model_name_or_path)/ --embeddings $(GENIENLP_EMBEDDINGS) --exist_ok --no_commit --preserve_case ; \
			fi ; \
			$(genienlp) predict --pred_set_name $$f --translate_no_answer  --tasks almond_translate --data ./$(experiment)/source/aug-$(aug_lang)/unquoted-qpis-marian/ --eval_dir $@/  --evaluate valid --pred_languages $(src_lang) --pred_tgt_languages $(tgt_lang) --path $(GENIENLP_EMBEDDINGS)/$(model_name_or_path)/direct/ --overwrite --silent $(default_translation_hparams) || exit 1 ; \
			mv $@/valid/almond_translate.tsv $@/$$f.tsv ; rm -rf $@/valid ; \
		done ; \
	fi
	rm -rf ./$(experiment)/source/aug-$(aug_lang)/unquoted-qpis-marian/almond/


$(experiment)/marian/$(tgt_lang)/unquoted-qpis-refined-direct: $(experiment)/marian/$(tgt_lang)/unquoted-qpis-translated-uttr-direct $(experiment)/marian/$(tgt_lang)/unquoted-qpis-translated-agent-direct
	mkdir -p $@
	# insert programs (and context)
	for f in $(all_names) ; do \
		data_size=`cat ./$(experiment)/source/aug-$(aug_lang)/unquoted-qpis-marian-slotvals/$$f.tsv | wc -l` ; \
		if [ $$f == $(train_name) ] ; then \
			num_output_per_example=$(train_output_per_example) ; \
		else \
			num_output_per_example=$(evaltest_output_per_example) ; \
		fi ; \
		paste <(awk "{for(i=0;i<$$num_output_per_example;i++)print}" <(cut -f1 ./$(experiment)/source/aug-$(aug_lang)/unquoted-qpis/$$f.tsv)) \
		 <(paste -d ' ' <(cut -f2 ./$(experiment)/source/aug-$(aug_lang)/unquoted-qpis-marian-slotvals/$$f.tsv) \
		 <(awk "{for(i=0;i<$$data_size;i++)print}" <(echo ";")) \
		 <(cut -f2 ./$(experiment)/marian/$(tgt_lang)/unquoted-qpis-translated-agent-direct/$$f.tsv)) \
		 <(cut -f2 ./$(experiment)/marian/$(tgt_lang)/unquoted-qpis-translated-uttr-direct/$$f.tsv) \
		 <(awk "{for(i=0;i<$$num_output_per_example;i++)print}" <(cut -f4 ./$(experiment)/source/aug-$(aug_lang)/unquoted-qpis/$$f.tsv)) \
		 > $@/$$f.tsv.tmp ; \
	done

	# refine sentence
	for f in $(all_names) ; do python3 $(ml_scripts)/text_edit.py --experiment $(experiment) --refine_sentence --post_process_translation --experiment $(experiment) --param_language $(tgt_lang) --num_columns 4 --input_file $@/$$f.tsv.tmp --output_file $@/$$f.tsv ; done

# 	rm -rf $@/*.tsv.tmp


$(experiment)/marian/$(tgt_lang)/unquoted-qpis-direct: $(experiment)/marian/$(tgt_lang)/unquoted-qpis-refined-direct
	mkdir -p $@
	# fix punctuation and clean dataset
	for f in $(all_names) ; do python3 $(ml_scripts)/text_edit.py --experiment $(experiment) --insert_space_quotes --num_columns 4 --input_file $</$$f.tsv --output_file $@/$$f.tsv ; done


$(experiment)/marian/$(tgt_lang)/unquoted-direct: $(experiment)/marian/$(tgt_lang)/unquoted-qpis-direct
	mkdir -p $@
	# remove quotation marks in the sentence
	for f in $(all_names) ; do python3 $(ml_scripts)/text_edit.py --experiment $(experiment) --remove_qpis --num_columns 4 --input_file $</$$f.tsv  --output_file $@/$$f.tsv  ; done

$(experiment)/marian/$(tgt_lang)/final-qpis-direct: $(experiment)/marian/$(tgt_lang)/unquoted-direct
	mkdir -p $@
	# qpis dataset
	for f in $(all_names) ; do python3 ./scripts/dialogue_edit.py --mode qpis --src_lang $(src_lang) --tgt_lang $(tgt_lang) --experiment $(experiment) --ontology $($(experiment)_ontology)/$(tgt_lang)/ontology.json --input_path $</$$f.tsv --output_path $@/$$f.tsv ; done

$(experiment)/marian/$(tgt_lang)/final-cjkspaced-direct: $(experiment)/marian/$(tgt_lang)/final-qpis-direct
	mkdir -p $@
	# remove qpis
	for f in $(all_names) ; do python3 $(ml_scripts)/text_edit.py --experiment $(experiment) --remove_qpis --num_columns 4 --input_file $</$$f.tsv  --output_file $@/$$f.tsv  ; done


$(experiment)/marian/$(tgt_lang)/final-direct: $(experiment)/marian/$(tgt_lang)/final-cjkspaced-direct
	mkdir -p $@
	# remove cjk spaces
	for f in $(all_names) ; do python3 $(ml_scripts)/text_edit.py --experiment $(experiment) --fix_spaces_cjk --translate_slot_names --translate_slot_values --experiment $(experiment) --param_language $(tgt_lang) --num_columns 4 --input_file $</$$f.tsv  --output_file $@/$$f.tsv  ; done

translate_data_direct: $(experiment)/marian/$(tgt_lang)/final-direct
	# done!
	echo $@
