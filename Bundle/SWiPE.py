from difflib import SequenceMatcher
from collections import defaultdict, Counter
import re


def tokenize(text):
    text = re.sub(r"\s{2,}", " ", text)
    text = text.replace("—", "-").replace("–", "-")
    cleaned_text = text.replace(".", " .").replace(",", " ,").replace("!", " !").replace("?", " ?").replace(";", " ;").replace(":", " :").replace("\n", " \n ").replace("'", " '").replace('"', ' " ').replace("(", " (").replace(")", " )")
    cleaned_text = re.sub(r"\s{2,}", " ", cleaned_text)
    return cleaned_text.split(" ")


def fix_punctuation(text):
    return text.replace(" .", ".").replace(" ,", ",").replace(" !", "!").replace(" ?", "?").replace(" ;", ";").replace(" :", ":").replace(" \n", "\n ").replace(" '", "'").replace(' "', '"').replace(" (", "(").replace(" )", ")")


def untokenize(tokens):
    return fix_punctuation(" ".join(tokens))


def get_edit_operations(text1, text2):
    S1 = tokenize(text1)
    S2 = tokenize(text2)

    s = SequenceMatcher(lambda x: x in ('\n',), S1, S2)
    opcodes = s.get_opcodes()
    operations = []
    for code, i1, i2, j1, j2 in opcodes: # i1i2/src, j1j2/tgt
        assert i2 - i1 == len(S1[i1:i2]), f'{i2 - i1 =} {len(S1[i1:i2]) = }'
        assert j2 - j1 == len(S2[j1:j2]), f'{j2 - j1 =} {len(S2[j1:j2]) = }'
        if code == "insert":
            operation = {"type": "insert", "insert": untokenize(S2[j1:j2])}
        if code == "delete":
            operation = {"type": "delete", "delete": untokenize(S1[i1:i2])}
        if code == "replace":
            operation = {"type": "replace", "insert": untokenize(S2[j1:j2]), "delete": untokenize(S1[i1:i2])}
        if code == "equal":
            operation = {"type": "equal", "text": untokenize(S1[i1:i2])}
        operations.append(operation)

    new_operations = []
    for old_op in operations:
        if old_op["type"] == "equal":
            new_operations.append({"type": "equal", "text": old_op["text"]})
        if "delete" in old_op:
            del_toks = split_sent_text(old_op["delete"])
            for del_tok in del_toks:
                new_operations.append({"type": "delete", "delete": del_tok})
        if "insert" in old_op:
            ins_toks = split_sent_text(old_op["insert"])
            for ins_tok in ins_toks:
                new_operations.append({"type": "insert", "insert": ins_tok})        
    return new_operations


def split_sent_text(text):
    if "." not in text:
        return [text]

    toks = [txt for txt in text.split(".")]
    N = len(toks)
    toks = [t+"." if i < N-1 else t for i, t in enumerate(toks)]

    merged_toks = []
    build_up = ""
    for tok in toks:
        # Merge if it is single letters (like U.S. )
        if len(tok) == 2 and tok[:-1].isalpha():
            build_up += tok
        else:
            if len(build_up) > 0:
                merged_toks.append(build_up)
            merged_toks.append(tok)
            build_up = ""

    if len(merged_toks) > 0 and len(merged_toks[-1].strip()) == 0:
        merged_toks = merged_toks[:-1]
    return merged_toks


def make_colored_text(text1=None, text2=None, style="shell", from_ops=None):
    assert from_ops is not None or (text1 is not None and text2 is not None)
    if from_ops is not None:
        operations = from_ops
    else:
        operations = get_edit_operations(text1, text2)
    return make_colored_text_from_operations(operations, style=style)


def  make_colored_text_from_operations(operations, style="shell"):
    colored_text = ""
    for operation in operations:
        if operation["type"] == "insert":
            colored_text += make_color(operation["insert"], "green", style=style)
        if operation["type"] == "delete":
            colored_text += make_color(operation["delete"], "red", style=style)
        if operation["type"] == "replace":
            colored_text += make_color(operation["delete"], "red", style=style) + make_color(operation["insert"], "green", style=style)
        if operation["type"] == "equal":
            colored_text += " " + operation["text"]

    lines = [line.strip() for line in colored_text.split("\n")]
    text = fix_punctuation("\n".join(lines))
    # Replace 2+ spaces by 1 space with re
    text = re.sub(r"\s{2,}", " ", text)
    return text


def make_color(text, color, style="shell"):
    assert color in ["green", "red", "blue"]
    assert style in ["shell", "xml", "html", "llm"]

    if style == "shell":
        start_green, end_green = "\033[1;32m", "\033[0m"
        start_red, end_red = "\033[1;31m", "\033[0m"
        start_blue, end_blue = "\033[1;34m", "\033[0m"
    elif style == "xml":
        start_green, end_green = " <green> ", " </green> "
        start_red, end_red = " <red> ", " </red> "
        start_blue, end_blue = " <blue> ", " </blue> "
    elif style == "html":
        start_green, end_green = " <span class='green'> ", " </span> "
        start_red, end_red = " <span class='red'> ", " </span> "
        start_blue, end_blue = " <span class='blue'> ", " </span> "
    elif style == "llm":
        start_green, end_green = " ADD ", " EADD "
        start_red, end_red = " DEL ", " EDEL "
        start_blue, end_blue = " INFO ", " EINFO "

    if color == "green":
        return start_green + text + end_green
    elif color == "red":
        return start_red + text + end_red
    elif color == "blue":
        return start_blue + text + end_blue
    

def sub_edits(edits, edit_group):
    # annotated range
    m, M = min(edit_group["opis"]), max(edit_group["opis"])
    opi_range = list(range(m, M+1))
    if opi_range[0] > 0 and edits[opi_range[0]-1]["type"] == "equal":
        opi_range = [opi_range[0]-1] + opi_range
    if opi_range[-1] < len(edits)-1 and edits[opi_range[-1]+1]["type"] == "equal":
        opi_range = opi_range + [opi_range[-1]+1]
    return [edits[opi] for opi in opi_range]

def gen_edit_group(input_text, output_text, edit_groups):
    all_edits = get_edit_operations(input_text, output_text)
    for ed_group in edit_groups:
        yield ed_group["category"], sub_edits(all_edits, ed_group)

def del_sent_ids(sample, r_sents):
    deleted = defaultdict(set)
    for cat, edits in gen_edit_group(sample["r_content"], sample["s_content"], sample["annotations"]):
        if any(e['type'] == 'delete' for e in edits) and all(e['type'] in ('delete', 'equal') for e in edits):
            text = ' '.join(e['delete'] for e in edits if e['type'] == 'delete')
            if select := set(eid for eid, s in enumerate(r_sents) if s in text):
                for eid in select:
                    deleted[eid].add(cat)
                # print("[%s] %s" % (cat.ljust(30), make_colored_text(from_ops = edits)))
    return deleted

if __name__ == "__main__":
    import json, random
    from pprint import pprint
    from nltk.tokenize import sent_tokenize
    reasons = Counter()

    # with open("SWiPE/data/swipe_test_ood.json", "r") as f:
    # with open("SWiPE/data/swipe_test_id.json", "r") as f:
    # with open("SWiPE/data/swipe_val.json", "r") as f:
    with open("SWiPE/data/swipe_train.json", "r") as f:
        data = json.load(f)

    if False:
        random.seed(239847)
        while True:
            sample = random.choice(data)
            if 'annotations' in sample:
                break
            print('No annotation found. Try another.')
        visualize_edit_groups(sample["r_content"], sample["s_content"], sample["annotations"])
    else:
        for sample in data:
            if 'annotations' not in sample:
                print('No annotation found. Try another.')
                continue
            r_sents = sent_tokenize(sample['r_content'])
            deleted = del_sent_ids(sample, r_sents)
            for cat in deleted.values():
                reasons.update(cat)
            #     print(cat, edits)
            if deleted:
                print(sample['r_page'])
                print(deleted)
                print()
                print()
                print()
        print(reasons)