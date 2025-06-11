# exemple

```bash
cd jobmarket_ml
python src/jobmarket_ml/train_grid_search.py --nrows_offers 5 --nrows_candidates 5 --cv_folds 2 --test
```

```bash
python src/jobmarket_ml/train_random_search.py --nrows_offers 10 --nrows_candidates 5 --cv_folds 3 --n_iter 5 --test
```

```bash
python src/jobmarket_ml/predict.py \
  --run_id ec4659a135614e89a1dad4112651a118 \
  --candidate_text "Développeur Python avec 5 ans d'expérience en développement web, spécialisé en Django et Flask. Compétences en SQL, Git et méthodologies agiles." \
  --top_k 3 \
  --nrows_offers 10
```
