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

def load_dataset(split, transition_system):

    prefix = 'card2code/third_party/hearthstone/'
    src_file = join(prefix, "{}_hs.in".format(split))
    tgt_file = join(prefix, "{}_hs.out".format(split))

    examples = []
    for idx, (src_line, tgt_line) in enumerate(zip(open(src_file), open(tgt_file))):
        print(idx)

        src_line = src_line.rstrip()
        tgt_line = tgt_line.rstrip()
        tgt_line = tgt_line.replace("§", "\n")

        src_toks = src_line.split()
        tgt_toks = tgt_line.split()
        tgt_ast = transition_system.surface_code_to_ast(tgt_line)

        # sanity check
        reconstructed_tgt = transition_system.ast_to_surface_code(tgt_ast)
        reconstructed_tgt = reconstructed_tgt.replace("\n\n", "\n", 1)
        print(tgt_line, reconstructed_tgt)
        assert tgt_line == reconstructed_tgt

        tgt_action_tree = transition_system.get_action_tree(tgt_ast)

        # sanity check
        ast_from_action = transition_system.build_ast_from_actions(
            tgt_action_tree)
        assert transition_system.compare_ast(ast_from_action, tgt_ast)

        tgt_from_hyp = transition_system.ast_to_surface_code(ast_from_action)
        assert tgt_from_hyp == tgt_line
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
