# coding=utf-8
from collections import OrderedDict

import torch
import numpy as np
try:
    import cPickle as pickle
except:
    import pickle


class Dataset:
    def __init__(self, examples):
        self.examples = examples

    @property
    def all_source(self):
        return [e.src_sent for e in self.examples]

    @property
    def all_targets(self):
        return [e.tgt_code for e in self.examples]

    @staticmethod
    def from_bin_file(file_path):
        examples = pickle.load(open(file_path, 'rb'))
        return Dataset(examples)

    def __len__(self):
        return len(self.examples)

    def __iter__(self):
        return iter(self.examples)

    def batch_iter(self, batch_size, shuffle=False):
        index_arr = np.arange(len(self.examples))
        if shuffle:
            np.random.shuffle(index_arr)

        batch_num = int(np.ceil(len(self.examples) / float(batch_size)))
        for batch_id in range(batch_num):
            batch_ids = index_arr[batch_size *
                                  batch_id: batch_size * (batch_id + 1)]
            batch_examples = [self.examples[i] for i in batch_ids]
            batch_examples.sort(key=lambda e: -len(e.src_toks))

            yield batch_examples


class Example:
    def __init__(self, src_toks, tgt_toks, tgt_ast, idx=0, tgt_actions=None, meta=None):
        self.src_toks = src_toks
        self.tgt_toks = tgt_toks
        self.tgt_ast = tgt_ast
        self.tgt_actions = tgt_actions

        self.idx = idx
        self.meta = meta



def sent_lens_to_mask(lens, max_length):
    mask = [[1 if j < l else 0 for j in range(max_length)] for l in lens]
    # match device of input
    return mask

class Batch(object):
    def __init__(self, examples, grammar, vocab, train=True, cuda=False, build_all=True):
        self.examples = examples

        # self.src_sents = [e.src_sent for e in self.examples]
        # self.src_sents_len = [len(e.src_sent) for e in self.examples]

        self.grammar = grammar
        self.vocab = vocab
        self.cuda = cuda
        self.train = train
        self.build_input(build_all)

    def __len__(self):
        return len(self.examples)

    def build_input(self, build_all=True):

        sent_lens = [len(x.src_toks) for x in self.examples] if build_all else None
        max_sent_len = max(sent_lens) if build_all else 0
        sent_masks = sent_lens_to_mask(sent_lens, max_sent_len) if build_all else None
        sent = None
        if build_all:
            sents = [
                [
                    self.vocab.src_vocab[e.src_toks[i]] if i < l else self.vocab.src_vocab['<pad>']
                    for i in range(max_sent_len)
                ]
                for l, e in zip(sent_lens, self.examples)
            ]
        else:
            sent = [ex.src_toks for ex in self.examples]

        if self.cuda:
            self.sents = torch.LongTensor(sents).cuda() if build_all else sent
            self.sent_lens = torch.LongTensor(sent_lens).cuda() if build_all else None
            self.sent_masks = torch.ByteTensor(sent_masks).cuda() if build_all else None
        else:
            self.sents = torch.LongTensor(sents).cuda() if build_all else sent
            self.sent_lens = torch.LongTensor(sent_lens).cuda() if build_all else None
            self.sent_masks = torch.ByteTensor(sent_masks).cuda() if build_all else None
        if self.train:
            [self.compute_choice_index(e.tgt_actions) for e in self.examples]

    def compute_choice_index(self, node):
        if isinstance(node, list):
            for item in node:
                if item.action.action_type == "ApplyRule":
                    candidate = self.grammar.get_prods_by_type(item.action.type)
                    item.action.choice_index = candidate.index(item.action.choice)
                    [self.compute_choice_index(x) for x in item.fields]
                elif item.action.action_type == "GenToken":
                    token_vocab = self.vocab.primitive_vocabs[item.action.type]
                    item.action.choice_index = token_vocab[item.action.choice]
                elif item.action.action_type == "Reduce":
                    pass
                    # candidate = self.grammar.get_prods_by_type(item.action.type)
                    # item.action.choice_index = candidate.index(item.action.choice)
                else:
                    raise ValueError("invalid action type", item.action.action_type)
        else:
            if node.action.action_type == "ApplyRule":
                candidate = self.grammar.get_prods_by_type(node.action.type)
                node.action.choice_index = candidate.index(node.action.choice)
                [self.compute_choice_index(x) for x in node.fields]
            elif node.action.action_type == "GenToken":
                token_vocab = self.vocab.primitive_vocabs[node.action.type]
                node.action.choice_index = token_vocab[node.action.choice]
            elif node.action.action_type == "Reduce":
                pass
                # candidate = self.grammar.get_prods_by_type(node.action.type)
                # node.action.choice_index = candidate.index(node.action.choice)
            else:
                raise ValueError("invalid action type", node.action.action_type)
