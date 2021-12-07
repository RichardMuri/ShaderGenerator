import sys
from common.config import *
from components.dataset import *

from grammar.grammar import Grammar

from grammar.python3.python3_transition_system import Python3TransitionSystem
from models.ASN import ASNParser
from models import nn_utils

from torch import optim
import os
from dataclasses import dataclass
import subprocess
from tqdm import tqdm

asdl_file = "torchASN/data/hearthstone/python_3_7_12_asdl.txt"
vocab = "torchASN/data/hearthstone/vocab.bin"
train_file = "torchASN/data/hearthstone/train.bin"
dev_file = "torchASN/data/hearthstone/dev.bin"
test_file = "torchASN/data/hearthstone/test.bin"
dropout = 0.3
enc_hid_size = 100
src_emb_size = 100
field_emb_size = 100
max_epoch = 100
clip_grad = 5.0
batch_size = 32
lr = 0.003
model_file = f"model.hearthstone.enc{enc_hid_size}.src{src_emb_size}.field{field_emb_size}.drop{dropout}.max_ep{max_epoch}.batch{batch_size}.lr{lr}.clip_grad{clip_grad}.bin"
save_to = "trained_models\model.hearthstone.enc100.src100.field100.drop0.3.max_ep$100.batch32.lr$0.003.clip_grad5.0.bin"
log_every = 50
run_val_after = 5
max_decode_step = 70
max_naive_parse_depth = 18
beam_size = 10


@dataclass
class Arguments:
    asdl_file: str
    vocab: str
    train_file: str
    dev_file: str
    test_file: str
    dropout: float
    enc_hid_size: int
    src_emb_size: int
    field_emb_size: int
    max_epoch: int
    clip_grad: float
    batch_size: int
    lr: float
    model_file: str
    save_to: str
    log_every: int
    run_val_after: int
    max_decode_step: int
    max_naive_parse_depth: int
    beam_size: int


args = Arguments(asdl_file=asdl_file, vocab=vocab, train_file=train_file, dev_file=dev_file, test_file=test_file, dropout=dropout, enc_hid_size=enc_hid_size, src_emb_size=src_emb_size,
                 field_emb_size=field_emb_size, max_epoch=max_epoch, clip_grad=clip_grad, batch_size=batch_size, lr=lr, model_file=model_file, save_to=save_to, log_every=log_every,
                 run_val_after=run_val_after, max_decode_step=max_decode_step, max_naive_parse_depth=max_naive_parse_depth, beam_size=beam_size)


test_set = Dataset.from_bin_file(args.test_file)
parser = ASNParser.load(args.save_to, ex_args=args)

parser.eval()
with torch.no_grad():
    parse_results = []
    i = 0
    for ex in tqdm(test_set, desc='Decoding', file=sys.stdout, total=len(test_set)):
        i = i + 1
        print(i)
        parse_results.append(parser.parse(ex))
# match_results = [ parser.transition_system.compare_ast(r, e.tgt_ast) for r, e in zip(parse_results, test_set)]
# match_acc = sum(match_results) * 1. / len(match_results)
# print("Eval Acc", match_acc)bv


def act_tree_to_ast(
    x): return parser.transition_system.build_ast_from_actions(x)


top_asts = [act_tree_to_ast(x[0].action_tree)
            if x else None for x in parse_results]
top_codes = [parser.transition_system.ast_to_surface_code(x) for x in top_asts]
# match_results = [ parser.transition_system.compare_ast(r, e.tgt_ast) for r, e in zip(top_asts, test_set)]
match_results = [" ".join(e.tgt_toks) == r for e,
                 r in zip(test_set, top_codes)]
# top_asts = [parser.transition_system]

match_acc = sum(match_results) * 1. / len(match_results)
# [print("%s\n\t==>%s\n\t==>%s" % (" ".join(e.src_toks), " ".join(e.tgt_toks), c)) for e,c in zip(test_set, top_codes)]

with open("output.txt", "w") as f:
    for c in top_codes:
        f.write(c.replace(" ", "") + "\n")

# oracle_res = []
# i = 0
# acc = 0
# for e, c in zip(test_set, top_codes):
#     gt_code = " ".join(e.tgt_toks)
#     pred_code = c
#     eq_res = check_equiv(pred_code, gt_code)
#     oracle_res.append(eq_res)
#     acc += eq_res
#     i += 1
#     # print(acc, i)
# print("String Acc", match_acc)
# print("DFA Acc", sum(oracle_res) * 1.0/len(oracle_res) )
