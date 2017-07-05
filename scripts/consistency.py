import re, sys
from lxml import etree


class Construction():
    def __init__(self):
        self.name = ''
        self.illustration = ''
        self.definition_rus = ''
        self.definition_eng = ''
        self.examples = []
        self.structure = []


namespc = {"karp": "http://spraakbanken.gu.se/eng/research/infrastructure/karp/karp",
          "konst": "http://spraakbanken.gu.se/swe/resurs/konstruktikon",
          "rusfn": "http://spraakbanken.gu.se/swe/resurs/rusfn"}
const = "ADJ|ADV|INTJ|NOUN|PROPN|ADV|VERB|ADP|CCONJ|DET|NUM|PART|PRON" \
        "|SCONJ|PUNCT|X|NP|VP|AP|AdvP|PP|NumP|XP|BareCl|IndirCl|Cl|S"
morph = "Sing|Plur|Neut|Masc|Fem|1|2|3|Anim|Inan|Nom|Gen|Acc|Dat|Ins|" \
        "Loc|Voc|Par|Adn|Loc2|Acc2|Dat2|Cmp|Inf|Pres|Past|Fut|Bare|Imper2" \
        "|Imp|Perf|Part|Pass|Act|Short|Conv|DiscC|DirSpeech|PartPast|PartPres"

allowed = []
with open(sys.argv[2], "r", encoding="utf-8") as f:
    for line in f:
        row = line.strip().split('\t');
        if row[0] == 'POS': 
            allowed.append(row[1])
            allowed.append(row[1].title())
        else:
            allowed.append(row[1])
illegal = ['/', '+', '[', '[', "'", '"']


def rus(word):
    for symbol in word.lower():
        if symbol in 'абвгдеёжзийклмнопрстуфхцчшщъыьэюя-':
            return True
    return False


def tokenize(string):
    string += "#"
    tokens = []
    punctuation = []
    current_token = ""
    for symbol in string:
        if symbol.isalnum():
            current_token += symbol
        else:
            punctuation.append(symbol)
            if current_token:
                tokens.append(current_token)
            current_token = ""
    return tokens, punctuation[:-1]


def consistent_token(token, allowed_tokens):
    if rus(token):
        return True
    if token.isdigit():
        return True
    if token not in allowed_tokens:
        return False
    return True


def consistent_punct(punct, illegal_puncts):
    if punct in illegal_puncts:
        return False
    return True


def consistent(data, allowed_tokens, illegal_puncts):
    inconsistent = []
    if type(data) == str:
        tokens, puncts = tokenize(data)
        inconsistent = [t for t in tokens if not consistent_token(t, allowed_tokens)] + [p for p in puncts if not consistent_punct(p, illegal_puncts)]
    else:
        labels = []
        for label in data:
            label = tokenize(label)[0]
            for l in label:
                labels.append(l)
        inconsistent = [label for label in labels if not consistent_token(label, allowed_tokens)]
    return list(set(inconsistent))


def check_format(annotation):
    pattern = "(?:" + const + ")(.)(?:" + morph + ")(?:(.)(?:" + morph + "))*"
    result = re.findall(pattern, annotation, flags=re.IGNORECASE)
    if not result:
        return True
    for r in result:
        if not re.match("-\.*", "".join(r),):
                    return False
    return True

xml = open(sys.argv[1])
tree = etree.parse(xml)
entries = tree.xpath("/LexicalResource/Lexicon/LexicalEntry/Sense")
print("Number of constructions:\t{0}.".format(len(entries)))

constructions = []
for entry in entries:
    c = Construction()
    c.name = entry.attrib["id"].replace("konstruktikon-rus--","")
    try:
        c.illustration = entry.xpath("feat[contains(@att, 'illustration')]/@val")[0]
    except IndexError:
        c.illustration = ''
    definitions = entry.xpath("definition", namespaces=namespc)

    try:
        c.definition_rus = entry.xpath("definition", namespaces=namespc)[0]
    except IndexError:
        c.definition_rus = ''

    try:
        c.definition_eng = entry.xpath("definition[contains(@xml:lang, 'eng')]/*", namespaces=namespc)
    except IndexError:
        c.definition_eng = ''

    c.structure = entry.xpath("feat[contains(@att, 'structure')]/@val")

    c.examples = entry.xpath("karp:example", namespaces=namespc)

    constructions.append(c)

delim = '\n'

out = sys.stdout ;
for c in constructions:

    def_rus_text = " ".join([x.text for x in list(c.definition_rus) if type(x.text) == str])
    def_rus_text = re.sub("\s+", " ", def_rus_text)
    def_rus_annotation = [x.attrib["name"] for x in list(c.definition_rus) if "name" in x.attrib]

    def_eng_text = " ".join([x.text for x in list(c.definition_eng) if type(x.text) == str])
    def_eng_text = re.sub("\s+", " ", def_eng_text)
    def_eng_annotation = [x.attrib["name"] for x in list(c.definition_eng) if "name" in x.attrib]

#     print(c.name, end="\n")
    out.write(c.name + "\n")


#     Inconsistent name
    inconsistent = consistent(c.name, allowed, illegal)
    if inconsistent:
        out.write("Inconsistent tokens (name): {}.".format(", ".join(inconsistent)) + delim)
    if " " in c.name:
        out.write("Illegal backspaces (name).\n")

    format_consistent = check_format(c.name)
    if not format_consistent:
        out.write("Wrong format of annotation.\n")

    if not c.illustration:
        out.write("No illustration.\n")
    if len(c.structure) == 0:
        out.write("No structure.\n")

    if len(c.definition_rus) == 0:
        out.write("No definition (rus).\n")
    else:
        if not def_rus_annotation:
            out.write("Definition (rus) is not annotated.\n")
    if len(c.definition_eng) == 0:
        out.write("No definition (eng).\n")
    else:
        if not def_rus_annotation:
            out.write("Definition (eng) is not annotated.\n")

    def_rus_inconsistent = consistent(def_rus_annotation, allowed, illegal)
    if def_rus_inconsistent:
        out.write("Inconsistent tokens (definition rus): {}.".format(", ".join(def_rus_inconsistent)) + delim)

    def_eng_inconsistent = consistent(def_eng_annotation, allowed, illegal)
    if def_eng_inconsistent:
        out.write("Inconsistent tokens (definition eng): {}.".format(", ".join(def_eng_inconsistent)) + delim)

#     Inconsistent examples
    if len(c.examples) < 3:
        out.write("Insufficient number of examples ({} more needed).".format(3 - len(c.examples)) + delim)

    example_annotation = []
    for example in c.examples:
        for elem in example.iter():
            if "name" not in elem.attrib:
                continue
            annotation = elem.attrib["name"]
            if annotation == c.name:
                continue

            annotation = re.split("[_,?.\-|! /()]", elem.attrib["name"], flags=re.IGNORECASE)
            for an in annotation:
                    example_annotation.append(an)
    if not example_annotation:
        out.write("Examples are not annotated.\n")
    examples_inconsistent = consistent(example_annotation, allowed, illegal)
    if examples_inconsistent:
        out.write("Inconsistent tokens (examples): {}".format(", ".join(examples_inconsistent)) + delim)

    out.write("\n")

