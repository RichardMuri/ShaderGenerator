from os.path import join
import numpy as np
import pickle
from grammar.grammar import Grammar
from components.dataset import Example
from grammar.python3.python3_transition_system import *
from datasets.utils import build_dataset_vocab
import sys
sys.path.append('.')


# from grammar.hypothesis import Hypothesis, ApplyRuleAction
# from components.action_info import get_action_infos
# from components.vocab import VocabEntry, Vocab

def elim_extraline(string: str):
    lines = string.splitlines(True)
    prev_spaces = len(lines[0]) - len(lines[0].lstrip(' '))
    spaces = 0
    index = 1
    for line in lines[1:]:
        if(line is not '\n'):
            spaces = len(line) - len(line.lstrip(' '))

        prev_empty = lines[index-1] == '\n'
        if(spaces == prev_spaces and prev_empty):
            tmp = lines.pop(index-1)
            index = index - 1
        prev_spaces = spaces
        index = index + 1

    result = "".join(lines)
    return result


def load_dataset(split, transition_system):

    prefix = 'card2code/third_party/hearthstone/'
    src_file = join(prefix, "{}_hs.in".format(split))
    tgt_file = join(prefix, "{}_hs.out".format(split))

    examples = []
    for idx, (src_line, tgt_line) in enumerate(zip(open(src_file, encoding="utf-8"), open(tgt_file, encoding="utf-8"))):
        print(idx)

        src_line = src_line.rstrip()
        tgt_line = tgt_line.rstrip()
        tgt_line = tgt_line.replace("§", "\n")

        src_toks = src_line.split()
        tgt_toks = tgt_line.split()
        tgt_ast = transition_system.surface_code_to_ast(tgt_line)

        # sanity check
        reconstructed_tgt = transition_system.ast_to_surface_code(tgt_ast)
        tgt_line = elim_extraline(tgt_line)
        reconstructed_tgt = reconstructed_tgt.replace("\n\n", "\n", 1)
        # reconstructed_tgt = reconstructed_tgt.replace("'True'", "True")
        # reconstructed_tgt = reconstructed_tgt.replace("'False'", "False")
        # print(tgt_line, reconstructed_tgt)
        # assert tgt_line.strip() == reconstructed_tgt.strip()

        tgt_action_tree = transition_system.get_action_tree(tgt_ast)

        # sanity check
        ast_from_action = transition_system.build_ast_from_actions(
            tgt_action_tree)
        assert transition_system.compare_ast(ast_from_action, tgt_ast)

        tgt_from_hyp = transition_system.ast_to_surface_code(ast_from_action)
        tgt_from_hyp = tgt_from_hyp.replace("\n\n", "\n", 1)
        tgt_from_hyp = elim_extraline(tgt_from_hyp)
        # print(tgt_line)
        # print(tgt_from_hyp)
        # assert tgt_from_hyp.strip() == tgt_line.strip()
        # sanity check
        # tgt_action_infos = get_action_infos(src_toks, tgt_actions)
        example = Example(idx=idx,
                          src_toks=src_toks,
                          tgt_actions=tgt_action_tree,
                          tgt_toks=tgt_toks,
                          tgt_ast=tgt_ast,
                          meta=None)

        examples.append(example)
    return examples


def make_dataset():

    grammar = Grammar.from_text(
        open('torchASN/data/hearthstone/python_3_7_12_asdl.txt').read())
    transition_system = Python3TransitionSystem(grammar)

    train_set = load_dataset("train", transition_system)
    dev_set = load_dataset("dev", transition_system)
    test_set = load_dataset("test", transition_system)
    # get vocab from actions
    vocab = build_dataset_vocab(train_set, transition_system, src_cutoff=2)

    # cache decision using vocab can be done in train
    pickle.dump(train_set, open('torchASN/data/hearthstone/train.bin', 'wb'))
    pickle.dump(dev_set, open('torchASN/data/hearthstone/dev.bin', 'wb'))
    pickle.dump(test_set, open('torchASN/data/hearthstone/test.bin', 'wb'))
    pickle.dump(vocab, open('torchASN/data/hearthstone/vocab.bin', 'wb'))


if __name__ == "__main__":
    make_dataset()
