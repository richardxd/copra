#!/usr/bin/env python3

import sys



root_dir = f"{__file__.split('src')[0]}"
if root_dir not in sys.path:
    sys.path.append(root_dir)
import os
import typing
from src.prompt_generator.interpreter import Grammar
from src.tools.training_data_format import TrainingDataFormat
from dataclasses import dataclass, field
from dataclasses_json import dataclass_json

class CoqGptRequestActions(object):
    RUN_TACTIC = "[RUN TACTIC]"
    GET_THMS = "[GET THMS]"
    GET_DFNS = "[GET DFNS]"

@dataclass_json
@dataclass
class CoqGptRequest(object):
    action : str = CoqGptRequestActions.RUN_TACTIC
    args: typing.List[str] = field(default_factory=list)

class CoqGPTRequestGrammar(Grammar):
    grammar = """
Prog: 
  RunTacticRequest
| GetThmsRequest
| GetDfnsRequest
| String Prog;
GetThmsRequest:
    GetThms End;
GetDfnsRequest:
    GetDfns End;
RunTacticRequest:
    RunTactic StpRequests End;
StpRequests:
  Stp String 
| Stp String StpRequests;

terminals
Stp: "[STP]";
End: "[END]";
RunTactic: "[RUN TACTIC]";
GetThms: "[GET THMS]";
GetDfns: "[GET DFNS]";
String:;
"""
    keywords = ["[STP]", "[END]", "[RUN TACTIC]", "[GET THMS]", "[GET DFNS]"]

    def before_keyword(text, pos):
        last = pos
        while last < len(text):
          while last < len(text) and text[last] != '[':
            last += 1
          if last < len(text):
              for keyword in CoqGPTRequestGrammar.keywords:
                  if text[last:].startswith(keyword):
                      return text[pos:last]
              last += 1

    def __init__(self):
        recognizers = {
            'String': CoqGPTRequestGrammar.before_keyword
        }
        super(CoqGPTRequestGrammar, self).__init__(CoqGPTRequestGrammar.grammar, CoqGPTRequestGrammar.keywords, recognizers=recognizers)

    def _parse_expr(self, nonTerminal, nodes, context):
        if nonTerminal == "GetThmsRequest":
            context.action = CoqGptRequestActions.GET_THMS
            context.args = []
        elif nonTerminal == "GetDfnsRequest":
            context.action = CoqGptRequestActions.GET_DFNS
            context.args = []
        elif nonTerminal == "RunTacticRequest":
            assert len(nodes) >= 2
            context.action = CoqGptRequestActions.RUN_TACTIC
            context.args.reverse()
        elif nonTerminal == "StpRequests":
            assert len(nodes) >= 2
            context.args.append(str(nodes[1]))
        else:
            raise Exception(f"Unknown non-terminal {nonTerminal}")
        return context
        
    def get_action(self, inp=None):
        context = CoqGptRequest()
        actions = {
            "Prog": lambda _, nodes: context,
            "GetThmsRequest": lambda _, nodes: self._parse_expr('GetThmsRequest', nodes, context),
            "GetDfnsRequest": lambda _, nodes: self._parse_expr('GetDfnsRequest', nodes, context),
            "RunTacticRequest": lambda _, nodes: self._parse_expr('RunTacticRequest', nodes, context),
            "StpRequests": lambda _, nodes: self._parse_expr('StpRequests', nodes, context),
            "String": lambda _, nodes: str(nodes) # Since this is always a string
        }
        return actions
    
    def interpret_result(self, result):
        assert isinstance(result, CoqGptRequest), f"Result must be a CoqGptRequest. Got {type(result)}"
        return result

    def get_openai_request(self, message) -> CoqGptRequest:
        result = self.run(message, None)
        return result


class CoqGptResponseActions(object):
    GLS = "[GLS]"
    RUN_TACTIC_RESULT = "[RUN TACTIC RESULT]"
    GET_THMS_RESULT = "[GET THMS RESULT]"
    GET_DFNS_RESULT = "[GET DFNS RESULT]"

@dataclass_json
@dataclass
class CoqGptResponse(object):
    action : str = CoqGptResponseActions.GLS
    success: bool = True
    message: str = ""
    training_data_format: typing.Optional[TrainingDataFormat] = None

class CoqGPTResponseGrammar(Grammar):
    grammar = """
Prog:
  GoalsResponse
| RunTacticResponse
| GetThmsResponses
| GetDfnsResponses
| String Prog;
RunTacticResponse:
  RunTacticResult Success End
| RunTacticResult Error String End;
GetThmsResponses:
  GetThmsResult ThmsResponses End;
ThmsResponses:
  Thms int ThmList {left, 2}
| Thms int ThmList ThmsResponses {left, 1};
ThmList:
  Thm String {left, 2}
| Thm String ThmList {left, 1};
GetDfnsResponses:
  GetDfnsResult DfnsResponses End;
DfnsResponses:
  Dfns int DfnList {left, 2}
| Dfns int DfnList DfnsResponses {left, 1};
DfnList:
  Dfn String {left, 2}
| Dfn String DfnList {left, 1};
GoalsResponse:
  Goals GoalResponses Stps;
GoalResponses:
  GoalResponse {left, 2}
| GoalResponse GoalResponses {left, 1};
GoalResponse:
  Goal int String Hyps int {left, 2}
|  Goal int String Hyps int HypResponses {left, 1};
HypResponses:
  HypResponse {left, 2}
| HypResponse HypResponses {left, 1};
HypResponse:
  Hyp String;


terminals
int: /\d+/;
Goals: "[GLS]";
Goal: "[GL]";
Hyps: "[HYPS]";
Hyp: "[HYP]";
Stps: "[STPS]";
Stp: "[STP]";
Dfns: "[DFNS]";
Dfn: "[DFN]";
Thms: "[THMS]";
Thm: "[THM]";
Error: "[ERROR]";
Success: "[SUCCESS]";
End: "[END]";
RunTacticResult: "[RUN TACTIC RESULT]";
GetThmsResult: "[GET THMS RESULT]";
GetDfnsResult: "[GET DFNS RESULT]";
String:;
"""
    keywords = ["[GLS]", "[GL]", "[HYPS]", "[HYP]", "[STPS]", "[STP]", "[DFNS]", "[DFN]", "[THMS]", "[THM]", "[ERROR]", "[SUCCESS]", "[END]", "[RUN TACTIC RESULT]", "[GET THMS RESULT]", "[GET DFNS RESULT]"]

    def before_keyword(text, pos):
        last = pos
        while last < len(text):
          while last < len(text) and text[last] != '[':
            last += 1
          if last < len(text):
              for keyword in CoqGPTResponseGrammar.keywords:
                  if text[last:].startswith(keyword):
                      return text[pos:last]
              last += 1

    def __init__(self):
        recognizers = {
            'String': CoqGPTResponseGrammar.before_keyword
        }
        super(CoqGPTResponseGrammar, self).__init__(CoqGPTResponseGrammar.grammar, CoqGPTResponseGrammar.keywords, recognizers=recognizers)
    
    def format_as_per_grammar(self, coq_gpt_response: CoqGptResponse) -> typing.List[str]:
        texts = []
        if coq_gpt_response.action == CoqGptResponseActions.GLS:
            lines = ["Goals to prove:"]
            for i, goal in enumerate(coq_gpt_response.training_data_format.start_goals):
                lines.append(f"[GL] {i+1}")
                lines.append(str(goal.goal))
                lines.append(f"[HYPS] {i + 1}")
                for hyp in goal.hypotheses:
                    lines.append(f"[HYP] {hyp}")
            gls_args = '\n'.join(lines)
            texts = [f"{CoqGptResponseActions.GLS}\n{gls_args}\n[END]"]
        elif coq_gpt_response.action == CoqGptResponseActions.RUN_TACTIC_RESULT:
            if coq_gpt_response.success:
                text = f"{CoqGptResponseActions.RUN_TACTIC_RESULT}[SUCCESS]\n[END]"
            else:
                text = f"{CoqGptResponseActions.RUN_TACTIC_RESULT}[ERROR]\n{coq_gpt_response.message}\n[END]"
            texts = [text] + self.format_as_per_grammar(CoqGptResponse(
                action = CoqGptResponseActions.GLS, 
                training_data_format = coq_gpt_response.training_data_format))
        elif coq_gpt_response.action == CoqGptResponseActions.GET_THMS_RESULT:
            lines = []
            for i, goal in enumerate(coq_gpt_response.training_data_format.start_goals):
                thms = goal.possible_useful_theorems_local + goal.possible_useful_theorems_external
                thms = [str(coq_gpt_response.training_data_format.all_useful_defns_theorems[thm.lemma_idx]) for thm in thms]
                lines.append(f"[THMS] {i+1}")
                lines.extend([f"[THM] {thm}" for thm in thms])
            get_thms_args = '\n'.join(lines)
            texts = [f"{CoqGptResponseActions.GET_THMS_RESULT}\n{get_thms_args}\n[END]"]
        elif coq_gpt_response.action == CoqGptResponseActions.GET_DFNS_RESULT:
            lines = []
            for i, goal in enumerate(coq_gpt_response.training_data_format.start_goals):
                dfns = goal.relevant_defns
                dfns = [str(coq_gpt_response.training_data_format.all_useful_defns_theorems[dfn.lemma_idx]) for dfn in dfns]
                lines.append(f"[DFNS] {i+1}")
                lines.extend([f"[DFN] {dfn}" for dfn in dfns])
            get_dfns_args = '\n'.join(lines)
            text = [f"{CoqGptResponseActions.GET_DFNS_RESULT}\n{get_dfns_args}\n[END]"]
        else:
            raise Exception(f"Invalid action {coq_gpt_response.action}")
        for text in texts:
            # verify that the text is valid as per grammar by compiling it
            self.compile(text)
        return texts



class GptAgentGrammar(Grammar):
    grammar = """
Prog:
  ConvStart Convs1 ConvEnd
| ConvStart Convs2 ConvEnd;
Convs1:
  Conv1
| Conv1 Conv2
| Conv1 Conv2 Convs1;
Convs2:
  Conv2
| Conv2 Conv1
| Conv2 Conv1 Convs2;
Conv1:
    '`{0}`' String;
Conv2:
    '`{1}`' String;

terminals
ConvStart: "`conv start`";
ConvEnd: "`conv end`";
String:;
"""

    def get_string_parser(keywords):
        def string_parser(keywords, text, pos):
            last = pos
            while last < len(text):
                while last < len(text) and text[last] != '`':
                    last += 1
                if last < len(text):
                    for keyword in keywords:
                        if text[last:].startswith(keyword):
                            return text[pos:last]
                    last += 1
        return lambda text, pos: string_parser(keywords, text, pos)

    def __init__(self, user_name: str = 'example_user', agent_name: str = 'example_assistant'):
        self.keywords = [f"`{user_name}`", f"`{agent_name}`", "`conv start`", "`conv end`"]
        self.user_name = user_name
        self.agent_name = agent_name
        recognizers = {
            'String': GptAgentGrammar.get_string_parser(self.keywords)
        }
        super(GptAgentGrammar, self).__init__(GptAgentGrammar.grammar.format(user_name, agent_name), self.keywords, recognizers=recognizers)
    pass

    def _parse_expr(self, nonTerminal, nodes, role, context):
        if nonTerminal == "Conv1" or nonTerminal == "Conv2":
            assert len(nodes) == 2
            context.append({
                'role': role,
                'name': str(nodes[0]).strip('`'),
                'content' : nodes[1].strip()
            })
        else:
            raise Exception(f"Unknown non-terminal {nonTerminal}")
    
    def get_action(self, inp):
        assert isinstance(inp, str), f"Input must be a string. Got {type(inp)}"
        assert inp in {"system", "user"}, f"Input must be either 'system' or 'user'. Got {inp}"
        role = inp
        context = []
        actions = {
            "Prog": lambda _, nodes: context,
            "Conv1": lambda _, nodes: self._parse_expr('Conv1', nodes, role, context),
            "Conv2": lambda _, nodes: self._parse_expr('Conv2', nodes, role, context),
            "String": lambda _, nodes: str(nodes) # Since this is always a string
        }
        return actions
    
    def interpret_result(self, result):
        assert isinstance(result, list), f"Result must be a list. Got {type(result)}"
        return result
    
    def get_openai_conv_messages(self, file_path: str, role: str = "system"):
        assert os.path.exists(file_path), f"File {file_path} does not exist"
        with open(file_path, "r") as f:
            conv = f.read()
        result = self.run(conv, role)
        return result

    def get_openai_main_message(self, file_path: str, role: str = "system"):
        with open(file_path) as f:
            main_content = f.read()
        return {
            'role': role,
            'content': main_content
        }

    def parse_openai_messages(self, messages: list, role: str = "assistant"):
        assert isinstance(messages, list), f"Messages must be a list. Got {type(messages)}"
        result = [message["content"] for message in messages if message['role'] == role]
        return result

if __name__ == "__main__":
    os.chdir(root_dir)
    grammar = GptAgentGrammar("example_user", "example_assistant")
    result = grammar.get_openai_conv_messages("data/prompts/conversation/coq-proof-agent-example.md", "system")
    print(result)  
    code = """
Please run the tactics below.
[RUN TACTIC] [STP] reflexivity.
[STP]reflexivity.
rewrite <- plus_n_O.[END]"""
    grammar = CoqGPTRequestGrammar()
    result = grammar.compile(code)
    print(result)
    run_result = grammar.run(code, None)
    print(run_result)
    result = grammar.compile(
"""
[GET THMS]
[END]""" 
    )
    print(result)
    result = grammar.compile(
"""
[GET DFNS]
[END]"""
    )
    print(result)
    grammar = CoqGPTResponseGrammar()
    result = grammar.compile("""
New goals to prove:
[GLS]
[GL] 1
n + 0 = n
[HYPS] 1
[HYP] n: nat
[GL] 2
n + 1 = n + 1
[HYPS] 1
[HYP] n: nat
[HYP] nat: Set

[STPS]
""")
    print(result)
    result = grammar.compile("""
[RUN TACTIC RESULT][SUCCESS]
[END]
""")
    print(result)
    result = grammar.compile("""
[RUN TACTIC RESULT][ERROR]
In environment
n : nat
Unable to unify "n" with "n + 0".
[END]
""")
    print(result)

    result = grammar.compile("""
[GET THMS RESULT]
[THMS] 1
[THM]plus_n_O : forall n  nat, n = n + 0
[THM]plus_O_n : forall n  nat, 0 + n = n
[THM]mult_n_O : forall n  nat, 0 = n * 0
[THM]plus_n_Sm : forall n m  nat, S (n
[THMS] 2
[THM]plus_n_O : forall n  nat, n = n + 0
[THM]plus_O_n : forall n  nat, 0 + n = n
[THM]mult_n_O : forall n  nat, 0 = n * 0
[THM]plus_n_Sm : forall n m  nat, S (n
[END]
""")
    print(result)

    result = grammar.compile("""
[GET DFNS RESULT]
[DFNS] 1
[DFN]nat: Set
[DFNS] 2
[DFN]nat: Set
[DFN]nat: Set
[END]
""")
    print(result)