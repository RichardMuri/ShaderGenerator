#!/bin/bash
set -e

seed=${1:-0}
asdl_file="data/hearthstone/python_3_7_12_asdl.txt"
vocab="data/hearthstone/vocab.bin"
train_file="data/hearthstone/train.bin"
dev_file="data/hearthstone/dev.bin"
dropout=0.3
enc_hid_size=100
src_emb_size=100
field_emb_size=100
max_epoch=100
clip_grad=5.0
batch_size=32
lr=0.003
model_file=model.hearthstone.enc${enc_hidden_size}.src${src_emb_size}.field${field_emb_size}.drop${dropout}.max_ep${max_epoch}.batch${batch_size}.lr${lr}.clip_grad${clip_grad}.bin

# echo "**** Writing results to logs/regex/${model_name}.log ****"
# mkdir -p logs/regex
# echo commit hash: `git rev-parse HEAD` > logs/regex/${model_name}.log

python -u scripts/hearthstone/train_baseline.py \
    --asdl_file ${asdl_file} \
    --train_file ${train_file} \
    --dev_file ${dev_file} \
    --vocab ${vocab} \
    --enc_hid_size ${enc_hid_size} \
    --src_emb_size ${src_emb_size} \
    --field_emb_size ${field_emb_size} \
    --dropout ${dropout} \
    --max_epoch ${max_epoch} \
    --lr ${lr} \
    --batch_size ${batch_size} \
    --clip_grad ${clip_grad} \
    --log_every 50 \
    --max_decode_step 70 \
    --max_naive_parse_depth 18 \
    --save_to checkpoints/hearthstone/${model_file} 2>&1 | tee -a logs/${model_file}.log

# . scripts/hearthstone/test_baseline.sh checkpoints/hearthstone/${model_file} 2>&1 | tee -a logs/test.${model_file}.log
