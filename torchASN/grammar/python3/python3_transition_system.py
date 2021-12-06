# coding=utf-8

import ast

import astor
from .print_utils import double_quote_pretty_string, long_pretty_source#, ClassDefSingleLineSourceGenerator

from grammar.python3.py_asdl_helper import asdl_ast_to_python_ast, python_ast_to_asdl_ast
from grammar.python3.py_utils import tokenize_code
from grammar.transition_system import TransitionSystem, ApplyRuleAction, GenTokenAction, ReduceAction, ActionTree
from grammar.dsl_ast import AbstractSyntaxTree, RealizedField


# from common.registerable import Registrable


# @Registrable.register('python3')
class Python3TransitionSystem(TransitionSystem):
    def tokenize_code(self, code, mode=None):
        return tokenize_code(code, mode)

    def surface_code_to_ast(self, code):
        py_ast = ast.parse(code)
        return python_ast_to_asdl_ast(py_ast, self.grammar)

    def ast_to_surface_code(self, asdl_ast):
        py_ast = asdl_ast_to_python_ast(asdl_ast, self.grammar)
        code = astor.to_source(py_ast, pretty_string=double_quote_pretty_string,
                               pretty_source=long_pretty_source).strip()
        # code = astor.to_source(py_ast, pretty_string=double_quote_pretty_string,
        #                        pretty_source=long_pretty_source,
        #                        source_generator_class=ClassDefSingleLineSourceGenerator).strip()

        if code.endswith(':'):
            code += ' pass'

        # first make sure the hypothesis code is parsable by `ast`
        # sometimes, the parser generates syntactically invalid surface code:
        # e.g., slot_0.1()
        # ast.parse(code)

        return code

    def compare_ast(self, hyp_ast, ref_ast):
        hyp_code = self.ast_to_surface_code(hyp_ast)
        ref_reformatted_code = self.ast_to_surface_code(ref_ast)

        ref_code_tokens = tokenize_code(ref_reformatted_code)
        hyp_code_tokens = tokenize_code(hyp_code)

        return ref_code_tokens == hyp_code_tokens

    # def hyp_correct(self, hype, example):
    #     return self.compare_ast(hype.tree, example.tgt_ast)

    def get_primitive_field_actions(self, realized_field):
        actions = []
        if realized_field.value is not None:
            # expr -> Global(identifier* names)
            if realized_field.cardinality == 'multiple':
                field_values = realized_field.value
            else:
                field_values = [realized_field.value]

            tokens = []
            if realized_field.type.name == 'string':
                for field_val in field_values:
                    tokens.extend(field_val.split(' ') + ['</primitive>'])
            else:
                for field_val in field_values:
                    tokens.append(field_val)

            for tok in tokens:
                actions.append(GenTokenAction(tok))
        elif realized_field.type.name == 'singleton' and realized_field.value is None:
            # singleton can be None
            actions.append(GenTokenAction('None'))

        return actions

    def is_valid_hypothesis(self, hyp, **kwargs):
        try:
            hyp_code = self.ast_to_surface_code(hyp.tree)
            ast.parse(hyp_code)
            self.tokenize_code(hyp_code)
        except:
            return False
        return True

    # def get_action_tree(self, ast_tree):
    #     fields = []
    #     if ast_tree.production.type.is_primitive_type():
    #         for x in ast_node.fields:
    #     else:
    #     return self._get_action_tree(ast_tree.production.type, ast_tree)

    def _get_action_tree(self, dsl_type, ast_node):
        if dsl_type.is_primitive_type():
            # print('===================')
            # print(type(ast_node))
            # print(ast_node)
            # if ast_node is None:
            #     return ActionTree(GenTokenAction(dsl_type, None))
            # assert isinstance(ast_node, str)
            # print(ast_node, type(ast_node))
            return ActionTree(GenTokenAction(dsl_type, ast_node))

        # primitive type
        # ast_node.value
        # print(ast_node.production)
        action = ApplyRuleAction(dsl_type, ast_node.production)
        field_nodes = []
        # fields = [self._get_action_tree(x.field.type, x.value) for x in ast_node.fields]
        for field in ast_node.fields:
            if field.cardinality == 'single':
                field_nodes.append(self._get_action_tree(field.type, field.value))
            elif field.cardinality == 'optional':
                if field.value is not None:
                    field_nodes.append(self._get_action_tree(field.type, field.value))
                else:
                    # Add a ReduceAction node when Optional field is None
                    field_nodes.append(ActionTree(ReduceAction(field.type, None)))
            else:
                multi_field = []
                for val in field.value:
                    multi_field.append(self._get_action_tree(field.type, val))

                # Add a ReduceAction node if multi_field is empty
                if len(multi_field) == 0:
                    multi_field.append(ActionTree(ReduceAction(field.type, None)))
                field_nodes.append(multi_field)
        # composite type
        return ActionTree(action, field_nodes)

    def build_ast_from_actions(self, action_tree):
        if isinstance(action_tree, list):
            # print(action_tree)
            if action_tree[0].action is None:
                return None
            if isinstance(action_tree[0].action, ReduceAction):
                return []
            return [self.build_ast_from_actions(at) for at in action_tree]
        else:

            if action_tree.action is None: # TODO for now only
                return None

            # Case for ReduceAction
            if isinstance(action_tree.action, ReduceAction):
                # print('-------------')
                # print(action_tree)
                # print(action_tree.action)
                # print(action_tree.action.type)
                # print(self.grammar[action_tree.action.type])
                # print(action_tree.action.choice)
                # print('##############')
                # return AbstractSyntaxTree(production, [])
                # return AbstractSyntaxTree(action_tree.action.type, [])
                return None
                # return AbstractSyntaxTree(production, [])

            # Case for GenTokenAction
            if isinstance(action_tree.action, GenTokenAction):
                return action_tree.action.token

            # Case for ApplyRuleAction
            production = action_tree.action.production

            # print("==============================")
            # print(production)
            # print(len(action_tree.fields), len(production.constructor.fields))
            # if len(action_tree.fields) == 0:
                # return production
                # return []
                # return AbstractSyntaxTree(production, [])


            assert len(action_tree.fields) == len(production.constructor.fields)

            return AbstractSyntaxTree(production, realized_fields=[
                    RealizedField(cnstr_f, self.build_ast_from_actions(action_f))
                    for action_f, cnstr_f in zip (action_tree.fields, production.constructor.fields)
                ])

        # realized_fields = []
        # # field_name_map = {}
        # # ActionTrees have "action" and "fields" params
        # # "action" is GenTokenAction if field type is primitive, else ApplyRuleAction
        # # "fields" is a list of ActionTrees
        # for field in production.constructor.fields:
        #     field_name_map[field.name] = RealizedField(field)
        # for action_tree_node in action_tree.fields:
        #     pass

        # RealizedField have "action" and "fields" params

        # asdl_node = AbstractSyntaxTree(production, realized_fields=realized_fields)
        # return asdl_node
