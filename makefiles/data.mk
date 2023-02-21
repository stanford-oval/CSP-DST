aug_lang=
tgt_lang=

$(experiment)/source/input: $(dataset_folder)/$(experiment)
	mkdir -p $@

	# replace_ids for train set if original splits do not have unique ids
	for f in $(all_names) ; do \
		if ( $(replace_ids) && ! [ $$f == $(train_name) ] ); then \
			python3 $(ml_scripts)/text_edit.py --experiment $(experiment) --replace_ids --num_columns $(num_columns) --input_file $</$$f.tsv --output_file $@/$$f.tsv ; \
		elif ( $(preprocess_paraphrased) && [ $$f == $(train_name) ] ); then \
			python3 $(ml_scripts)/text_edit.py --experiment $(experiment) --preprocess_paraphrased --num_columns $(num_columns) --input_file <$/$$f.tsv --output_file $@/$$f.tsv ; \
		else \
			cp $</$$f.tsv $@/$$f.tsv ; \
		fi ; \
	done

$(experiment)/source/input-qpis: $(experiment)/source/input
	mkdir -p $@

	# qpis input data
	for f in $(all_names) ; do python3 $(ml_scripts)/dialogue_edit.py --mode qpis --src_lang $(aug_lang) --tgt_lang $(tgt_lang) --experiment $(experiment) --ontology $($(experiment)_ontology)/$(tgt_lang)/ontology.json --input_path $</$$f.tsv --output_path $@/$$f.tsv ; done


$(experiment)/source/quoted-qpis: $(experiment)/source/input-qpis
	mkdir -p $@
	# requote the input qpis data
	for f in $(all_names) ; do python3 $(ml_scripts)/dialogue_edit.py --mode requote --src_lang $(aug_lang) --tgt_lang $(tgt_lang) --experiment $(experiment) --ontology $($(experiment)_ontology)/$(tgt_lang)/ontology.json --input_path $</$$f.tsv --output_path $@/$$f.tsv ; done


$(experiment)/source/quoted: $(experiment)/source/quoted-qpis
	mkdir -p $@
	# remove qpis from quoted dataset
	for f in $(all_names) ; do python3 $(ml_scripts)/text_edit.py --experiment $(experiment) --remove_qpis --num_columns $(num_columns) --input_file $</$$f.tsv --output_file $@/$$f.tsv ; done


$(experiment)/source/quoted-uniq: $(experiment)/source/quoted
	mkdir -p $@
	# find unique sentences for train set if necessary
	for f in $(all_names) ; do \
		cp $</$$f.tsv $@/$$f.tsv; \
	done

$(experiment)/source/quoted-uniq-qpis: $(experiment)/source/quoted-qpis
	mkdir -p $@
	# find unique sentences for train set if necessary
	for f in $(all_names) ; do \
		if ( $(remove_duplicate_sents) && [ $$f == $(train_name) ] ) ; then \
			python3 $(ml_scripts)/text_edit.py --experiment $(experiment) --remove_duplicate_sents --num_columns $(num_columns) --input_file $</$$f.tsv --output_file $@/$$f.tsv ; \
		else \
			cp $</$$f.tsv $@/$$f.tsv; \
		fi ; \
	done

$(experiment)/source/aug-$(aug_lang)/unquoted-qpis: $(experiment)/source/quoted-uniq-qpis
	# augment (=unquote) qpis inputs with actual parameter values
	mkdir -p $@
	# augment dataset in target language
	for f in $(all_names) ; do \
		if ( [ $$f == $(train_name) ] ); then \
			python3 $(ml_scripts)/dialogue_edit.py --mode augment --src_lang $(aug_lang) --tgt_lang $(tgt_lang) --experiment $(experiment) --ontology $($(experiment)_ontology)/$(aug_lang)/ontology.json --input_path $</$$f.tsv --output_path $@/$$f.tsv  ; \
		else \
			python3 $(ml_scripts)/dialogue_edit.py --mode augment --src_lang $(aug_lang) --tgt_lang $(tgt_lang) --experiment $(experiment) --ontology $($(experiment)_ontology)/$(aug_lang)/ontology.json --input_path $</$$f.tsv --output_path $@/$$f.tsv  ; \
		fi ; \
	done


########################
$(experiment)/source/aug-$(aug_lang)/unquoted-qpis/$(train_name)_blowup.tsv: $(experiment)/source/quoted-uniq-qpis/$(train_name).tsv
	# augment (=unquote) qpis inputs with actual parameter values with blowup
	python3 $(ml_scripts)/dialogue_edit.py --mode augment --src_lang $(aug_lang) --tgt_lang $(tgt_lang) --experiment $(experiment) --ontology $($(experiment)_ontology)/$(aug_lang)/ontology.json --input_path $< --output_path $@

$(experiment)/source/aug-$(aug_lang)/unquoted/$(train_name)_blowup.tsv: $(experiment)/source/aug-$(aug_lang)/unquoted-qpis/$(train_name)_blowup.tsv
	# remove qpis from unquoted data
	python3 $(ml_scripts)/text_edit.py --experiment $(experiment) --remove_qpis --num_columns $(num_columns) --input_file $< --output_file $@

########################

$(experiment)/source/aug-$(aug_lang)/unquoted: $(experiment)/source/aug-$(aug_lang)/unquoted-qpis
	mkdir -p $@
	# remove qpis from unquoted data
	for f in $(all_names) ; do python3 $(ml_scripts)/text_edit.py --experiment $(experiment) --remove_qpis --num_columns $(num_columns) --input_file $</$$f.tsv --output_file $@/$$f.tsv ; done


$(experiment)/source/quoted-uniq-marian: $(experiment)/source/quoted-uniq
	mkdir -p $@
	mkdir -p $(experiment)/source/quoted-uniq-marian-tmp
	# prepare quoted data for marian translation
	for f in $(all_names) ; do python3 $(ml_scripts)/text_edit.py --experiment $(experiment) --prepare_multiwoz_for_marian --replace_ids  --num_columns $(num_columns) --input_file $</$$f.tsv --output_file $(experiment)/source/quoted-uniq-marian-tmp/$$f.tsv ; cut -f1,3 $(experiment)/source/quoted-uniq-marian-tmp/$$f.tsv > $@/$$f.tsv ; done
	rm -rf $(experiment)/source/quoted-uniq-marian-tmp

$(experiment)/source/aug-$(aug_lang)/unquoted-qpis-marian-tmp: $(experiment)/source/aug-$(aug_lang)/unquoted-qpis
	mkdir -p $@
	mkdir -p $(experiment)/source/aug-$(aug_lang)/unquoted-qpis-marian-tmp
	# prepare unquoted data for marian translation
	for f in $(all_names) ; do python3 $(ml_scripts)/text_edit.py --experiment $(experiment) --prepare_multiwoz_for_marian --replace_ids  --num_columns $(num_columns) --input_file $</$$f.tsv --output_file $@/$$f.tsv ; done

$(experiment)/source/aug-$(aug_lang)/unquoted-qpis-marian-uttr: $(experiment)/source/aug-$(aug_lang)/unquoted-qpis-marian-tmp
	mkdir -p $@
	# prepare unquoted data for marian translation
	for f in $(all_names) ; do cut -f1,4 $</$$f.tsv > $@/$$f.tsv ; done

$(experiment)/source/aug-$(aug_lang)/unquoted-qpis-marian-agent: $(experiment)/source/aug-$(aug_lang)/unquoted-qpis-marian-tmp
	mkdir -p $@
	# prepare unquoted data for marian translation
	for f in $(all_names) ; do cut -f1,3 $</$$f.tsv > $@/$$f.tsv ; done

$(experiment)/source/aug-$(aug_lang)/unquoted-qpis-marian-slotvals: $(experiment)/source/aug-$(aug_lang)/unquoted-qpis-marian-tmp
	mkdir -p $@
	# prepare unquoted data for marian translation
	for f in $(all_names) ; do cut -f1,2 $</$$f.tsv > $@/$$f.tsv ; done


$(experiment)/source/aug-$(aug_lang)/unquoted: $(experiment)/source/aug-$(aug_lang)/unquoted-qpis
	mkdir -p $@
	# remove qpis from unquoted dataset
	for f in $(all_names) ; do python3 $(ml_scripts)/text_edit.py --experiment $(experiment) --remove_qpis --num_columns $(num_columns) --input_file $</$$f.tsv --output_file $@/$$f.tsv ; done


$(experiment)/finished: $(experiment)/source/aug-$(aug_lang)/unquoted $(experiment)/source/quoted-uniq-marian $(experiment)/source/aug-$(aug_lang)/unquoted-qpis-marian-agent $(experiment)/source/aug-$(aug_lang)/unquoted-qpis-marian-uttr $(experiment)/source/aug-$(aug_lang)/unquoted-qpis-marian-slotvals
	# done!
	echo $@

process_data:
	make experiment=$(experiment) $(experiment)/finished

process_train_blowup_%:
	make experiment=$(experiment) $(experiment)/source/aug-$(aug_lang)/unquoted/$(train_name)_blowup.tsv
