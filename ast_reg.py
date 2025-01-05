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
    def get_tokens(self):
        string_pattern = []
        while self.index != len(self.string):
            current = self.string[self.index]
            if 'a' <= current <= 'z':
                letters = current
                self.index+=1
                #print(self.string[next_symbol])
                while self.index < len(self.string) and 'a' <= self.string[self.index] <= 'z':
                    letters+=self.string[self.index]
                    self.index+=1
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
                save = self.in_parse_lookahead
                self.in_parse_lookahead = True
                node = self.alternation()
                self.in_parse_lookahead = save
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
                self.save_group_ids.append(self.count_cap_groups)
                node = self.alternation()
                if self.index < len(self.pattern) and self.pattern[self.index].kind == 'right_bracket':
                    self.index+=1
                else:
                    return {}
                return {'kind':'capture_group','key':self.count_cap_groups,'value':node}
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
        return True
       

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
    
]
for pattern in error_patterns:
    parser = RegexParser(pattern)
    
    print(pattern)
    result = parser.get_tokens()
    if result:
        result = parser.parse()
        print(f"Pattern: {pattern} -> Valid: {result}")
    else:
        print('Ошибка: token()')
        print(f"Pattern: {pattern} -> Valid: False")
