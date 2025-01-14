class Token:
    def __init__(self, kind, lexem):
        self.kind = kind
        self.lexem = lexem

class RegexParser:
    def __init__(self, string):
        self.string = string
        self.pattern = []
        self.index = 0
        self.count_cap_groups = 0
        self.in_parse_lookahead = False
        self.save_group_ids = []
        self.save_ref_ids = []

        self.rules = {}
        self.ast_tree = {}
        self.group_ids = {}
    def get_tokens(self):
        string_pattern = []
        while self.index != len(self.string):
            current = self.string[self.index]
            if 'a' <= current <= 'z':
                letters = current
                self.index+=1
                #print(self.string[next_symbol])
                '''while self.index < len(self.string) and 'a' <= self.string[self.index] <= 'z':
                    letters+=self.string[self.index]
                    self.index+=1'''
                string_pattern.append(Token('letter', letters))
            else:
                match current:
                    case '|': 
                        string_pattern.append(Token('|','|'))
                        self.index+=1
                    case '*': 
                        string_pattern.append(Token('*','*'))
                        self.index+=1
                    case '(':
                        self.index+=1
                        if self.index < len(self.string) and self.string[self.index] == '?':
                            self.index+=1
                            if self.index < len(self.string) and self.string[self.index] == ':':
                                string_pattern.append(Token('non_capturing',current))
                                self.index+=1
                            elif self.index < len(self.string) and self.string[self.index] == '=':
                                string_pattern.append(Token('lookahead',current))
                                self.index+=1
                            elif self.index < len(self.string) and self.string[self.index].isdigit():
                                number = self.string[self.index]
                                self.index+=1
                                #print(self.string[self.index])
                                while self.index < len(self.string) and self.string[self.index].isdigit():
                                    number+=self.string[self.index]
                                    self.index+=1
                                string_pattern.append(Token('referenseDigit',int(number)))
                            else:
                                return None
                        else:
                            string_pattern.append(Token('left_bracket',current))
                    case ')': 
                        string_pattern.append(Token('right_bracket',current))
                        if self.index - 1 >= 0 and self.string[self.index-1] == '(':
                            return None
                        self.index+=1
                    case _:
                        return None # unknown symbol
        
        self.pattern = string_pattern
        '''for pattern in string_pattern:
            print(pattern.kind,pattern.lexem)'''
        self.index = 0 # for parsing to start
        return string_pattern

    def base(self):
        if self.index < len(self.pattern):
            current = self.pattern[self.index]
            if current.kind == 'letter':
                self.index+=1
                return {'kind':'letter','value':current.lexem}
            if current.kind == 'referenseDigit':
                self.index+=1
                if self.index < len(self.pattern) and self.pattern[self.index].kind == 'right_bracket':
                    self.index+=1
                else:
                    return {}
                self.save_ref_ids.append(current.lexem)
                return {'kind':'referenseDigit','value':current.lexem}
            if current.kind == 'lookahead':
                if self.in_parse_lookahead:
                    return {} #error
                self.index+=1
                self.in_parse_lookahead = True
                node = self.alternation()
                self.in_parse_lookahead = False
                if self.pattern[self.index].kind == 'right_bracket':
                    self.index+=1
                else:
                    return {}
                return {'kind':'lookahead','value':node}
            if current.kind == 'left_bracket':
                if self.in_parse_lookahead:
                    return {} #error
                self.index+=1
                self.count_cap_groups+=1
                if self.count_cap_groups>9:
                    print("To many cap_groups")
                    return {}
                id_group = self.count_cap_groups
                self.save_group_ids.append(self.count_cap_groups)
                node = self.alternation()
                if self.index < len(self.pattern) and self.pattern[self.index].kind == 'right_bracket':
                    self.index+=1
                else:
                    return {}
                return {'kind':'capture_group','key':id_group,'value':node}
            if current.kind == 'non_capturing':
                self.index+=1
                node = self.alternation()
                if self.index < len(self.pattern) and self.pattern[self.index].kind == 'right_bracket':
                    self.index+=1
                else:
                    return {}
                return {'kind':'non_capturing','value':node}
            return {}
        else:
            return {}
    def repeat(self):
        node = self.base()
        if node == {}:
            return {}
        while self.index < len(self.pattern) and self.pattern[self.index].kind == '*':
            self.index+=1
            node = {'kind':'repeat','value':node}
        return node
    def concatination(self):
        nodes = []
        
        while self.index < len(self.pattern) and not (self.pattern[self.index].kind == '|' or self.pattern[self.index].kind == 'right_bracket'):
            repeat = self.repeat()
            if repeat != {}:
                nodes.append(repeat)
            else:
                return {}
        if nodes == []:
            return {}
        return {'kind': 'concatination', 'value': nodes}  if len(nodes) > 1 else nodes[0]
    def alternation(self):
        concat = self.concatination()
        if concat == {}:
            return {}
        nodes = [concat]
        while self.index < len(self.pattern) and self.pattern[self.index].kind == '|':
            self.index+=1
            if self.index >= len(self.pattern):
                return {} # end after |
            ## Two || and '' alternative
            if self.pattern[self.index].kind == '|' or self.pattern[self.index].kind == 'right_bracket':
                return {}
            concat = self.concatination()
            if not concat:
                return {}
            nodes.append(concat)
        return {'kind': 'alternative', 'value': nodes}  if len(nodes) > 1 else nodes[0]

    def parse(self):
        node = self.alternation()
        if node == {}:
            return False
        
        if self.index < len(self.pattern):
            print("LEFT SYMBOLS")
            return False
        for id in self.save_ref_ids:
            if id not in self.save_group_ids:
                print("Error: reference unknown")
                return False
        self.ast_tree = node
        #print(node)
        return True
    def print_grammar(self,grammar_rules):
        for nt in grammar_rules:
            if len(grammar_rules[nt]) == 1:
                print(nt,'->',grammar_rules[nt][0])
            else:
                print(nt,'->',' | '.join(grammar_rules[nt]))
        
    def build_grammar(self,ast,rule_name="S",index = 0):
        #ast = self.ast_tree
        
        #grammar_rules = {}
        if ast['kind'] == 'capture_group':
            # Для захватывающей группы создаем новое правило
            
            if ast['key'] not in self.group_ids.keys():
                group_rule_name = f"G{index}"
                self.group_ids[ast['key']] = group_rule_name
                index+=1
            else:
                group_rule_name = self.group_ids[ast['key']]
            
            self.rules[rule_name]=[]
            self.rules[rule_name].append(group_rule_name)
            self.build_grammar(ast['value'], group_rule_name,index)
        elif ast['kind'] == 'alternative':
            # Обрабатываем альтернативы
            alternatives = [] 
            self.rules[rule_name] = []
            for option in ast['value']:
                name = rule_name + f'_{index}'
                index += 1
                self.rules[name] = []
                alternatives.append(name)
                self.build_grammar(option,name,index)
            self.rules[rule_name].extend(alternatives)
        elif ast['kind'] == 'concatination':
            # Обрабатываем конкатенацию
            concatenation = []
            for item in ast['value']:
                name = rule_name + f'_{index}'
                index += 1
                self.rules[name] = []
                concatenation.append(name)
                self.build_grammar(item,name,index)
            self.rules[rule_name] = []
            self.rules[rule_name].append(' '.join(concatenation))
        elif ast['kind'] == 'letter':
            # Обрабатываем литерал
            self.rules[rule_name] = []
            self.rules[rule_name].append(ast['value'])
        elif ast['kind'] == 'referenseDigit':
            # Обрабатываем ссылки на цифры
            self.rules[rule_name] = []
            referenseDigit = ast['value']
            if referenseDigit not in self.group_ids:
                self.rules[f"G{index}"] = []
                self.group_ids[referenseDigit] = f"G{index}"
            self.rules[rule_name].append(self.group_ids[referenseDigit])
        elif ast['kind'] == 'repeat':
            # Обрабатываем оператор *
            self.rules[rule_name] = []
            name = rule_name + f'_{index}'
            index+=1
            self.rules[rule_name].append(' '.join([name,rule_name]))
            self.rules[rule_name].append('eps')
            self.build_grammar(ast['value'],name,index)
        elif ast['kind'] == 'lookahead':
            name = f'LOOK_{index}'
            index+=1
            self.rules[name] = []
            self.rules[rule_name] = []
            self.rules[rule_name].append(name)
            self.rules[name].append('eps')
        elif ast['kind'] == 'non_capturing':  
            self.rules[rule_name]=[]
            capturing_rule_name = f"NonCap_{index}"
            index+=1
            self.rules[rule_name].append(capturing_rule_name)
            self.build_grammar(ast['value'], capturing_rule_name,index)
        #self.print_grammar(grammar_rules) lookahead non-capturing
        return self.rules

# Пример использования
ok_patterns = [
    '((hj)|(gh))(k|(?2)|(?1))',
    '(ahg|(t))(alh|(?3))',
    '(a*(?=b)*)c*',
    '(auy|hh*|wr)*|d',
    '((aaa|ba)*ca)*',
    '(afg*|(?:(kj)*|rt))rtd',
    '(?=ab)(?=bb)bbb',
    '(tyu|fg)(?1)',
    'att(?=dfb|gh)dttt',
    '(a(?1)b|c)',
    '(?1)(first|second|third)',
    'fb**', 
]


error_patterns = [
    'agg*|bsf)df',
    '(?2)(a|(b|c)(gh)',
    '((ag)(reb)(tgsc)(dsg)((dg)f)((dfd))(fghh)(eri)(ghj)(yry))',
    '(a)(?2)',
    '(?=(dfa*))',
    'sds*(?=rt(?=rt))dfdg',
    '(?3)(ty*|op)(i*o)*',
    '(?399)(ty*|o',
    '(gh||dfb)',
    'gh||dfb)',
    '(gh<dfb)',
    'fb|*',
    ')fb|ui',
    '()',
    '(?=(?:sd))|(?=(?=df))|(?=(?=df))'
    
]
for pattern in ok_patterns:
    parser = RegexParser(pattern)
    
    print("Entered pattern: ",pattern)
    result = parser.get_tokens()
    if result:
        result = parser.parse()
        print(f"Pattern: {pattern} -> Valid: {result}")
        if result:
            grammar = parser.build_grammar(parser.ast_tree)
            parser.print_grammar(grammar)
    else:
        print('Ошибка: token()')
        print(f"Pattern: {pattern} -> Valid: False")
