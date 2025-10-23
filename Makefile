.PHONY: eval fit
fit:
\tpython app/ranker/fit_index.py --fields title+ingredients --ngrams 1,2 --suffix v1
\tpython app/ranker/fit_index.py --fields title+ingredients --ngrams 1,1 --suffix uni
eval:
\tpython -m eval.evaluate_models
