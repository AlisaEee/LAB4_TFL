# Определяем класс Token
struct Token
    kind::String
    lexem::String
end

# Определяем класс RegexParser
mutable struct RegexParser
    string::String
    pattern::Vector{Token}
    index::Int
    count_cap_groups::Int
    in_parse_lookahead::Bool
    save_group_ids::Vector{Int}
    save_ref_ids::Vector{Int}
    rules::Dict{String, Vector{String}}
    ast_tree::Dict{String, Any}
    group_ids::Dict{Int, String}

    function RegexParser(string::String)
        new(string, Token[], 1, 0, false, Int[], Int[], Dict(), Dict(), Dict())
    end
end

# Функция для получения токенов
function get_tokens(parser::RegexParser)
    string_pattern = Token[]
    while parser.index <= length(parser.string)
        current = parser.string[parser.index]
        if 'a' <= current <= 'z'
            push!(string_pattern, Token("letter", string(current)))
            parser.index += 1
        else
            if current == '|'
                push!(string_pattern, Token("|", "|"))
                parser.index += 1
            elseif current == '*'
                push!(string_pattern, Token("*", "*"))
                parser.index += 1
            elseif current == '('
                parser.index += 1
                if parser.index <= length(parser.string) && parser.string[parser.index] == '?'
                    parser.index += 1
                    if parser.index <= length(parser.string) && parser.string[parser.index] == ':'
                        push!(string_pattern, Token("non_capturing", string(current)))
                        parser.index += 1
                    elseif parser.index <= length(parser.string) && parser.string[parser.index] == '='
                        push!(string_pattern, Token("lookahead", string(current)))
                        parser.index += 1
                    elseif parser.index <= length(parser.string) && isdigit(parser.string[parser.index])
                        number = ""
                        while parser.index <= length(parser.string) && isdigit(parser.string[parser.index])
                            number *= parser.string[parser.index]
                            parser.index += 1
                        end
                        push!(string_pattern, Token("referenseDigit", string(number)))
                    else
                        return false
                    end
                else
                    push!(string_pattern, Token("left_bracket", string(current)))
                end
            elseif current == ')'
                push!(string_pattern, Token("right_bracket", string(current)))
               
                if parser.index - 1 >= 1 && parser.string[parser.index - 1] == '('
                    return false
                end 
                parser.index += 1
            else
                return false # unknown symbol
            end
        end
    end

    parser.pattern = string_pattern
    parser.index = 1 # for parsing to start
    return true
end

# Функция для базового разбора
function base(parser::RegexParser)
    if parser.index <= length(parser.pattern)
        current = parser.pattern[parser.index]
        if current.kind == "letter"
            parser.index += 1
            return Dict("kind" => "letter", "value" => current.lexem)
        elseif current.kind == "referenseDigit"
            parser.index += 1
            if parser.index <= length(parser.pattern) && parser.pattern[parser.index].kind == "right_bracket"
                parser.index += 1
            else
                return Dict()
            end
            push!(parser.save_ref_ids, parse(Int, current.lexem))
            return Dict("kind" => "referenseDigit", "value" => parse(Int, current.lexem))
        elseif current.kind == "lookahead"
            if parser.in_parse_lookahead
                return Dict() # error
            end
            parser.index += 1
            parser.in_parse_lookahead = true
            node = alternation(parser)
            parser.in_parse_lookahead = false
            if parser.index <= length(parser.pattern) && parser.pattern[parser.index].kind == "right_bracket"
                parser.index += 1
            else
                return Dict()
            end
            return Dict("kind" => "lookahead", "value" => node)
        elseif current.kind == "left_bracket"
            if parser.in_parse_lookahead
                return Dict() # error
            end
            parser.index += 1
            parser.count_cap_groups += 1
            if parser.count_cap_groups > 9
                println("Too many cap_groups")
                return Dict()
            end
            id_group = parser.count_cap_groups
            push!(parser.save_group_ids, parser.count_cap_groups)
            node = alternation(parser)
            if parser.index <= length(parser.pattern) && parser.pattern[parser.index].kind == "right_bracket"
                parser.index += 1
            else
                return Dict()
            end
            return Dict("kind" => "capture_group", "key" => id_group, "value" => node)
        elseif current.kind == "non_capturing"
            parser.index += 1
            node = alternation(parser)
            if parser.index <= length(parser.pattern) && parser.pattern[parser.index].kind == "right_bracket"
                parser.index += 1
            else
                return Dict()
            end
            return Dict("kind" => "non_capturing", "value" => node)
        end
    end
    return Dict()
end

# Функция для разбора повторений
function repeat(parser::RegexParser)
    node = base(parser)
    if isempty(node)
        return Dict()
    end
    while parser.index <= length(parser.pattern) && parser.pattern[parser.index].kind == "*"
        parser.index += 1
        node = Dict("kind" => "repeat", "value" => node)
    end
    return node
end

# Функция для разбора конкатенации
function concatination(parser::RegexParser)
    nodes = Any[]
    while parser.index <= length(parser.pattern) && !(parser.pattern[parser.index].kind == "|" || parser.pattern[parser.index].kind == "right_bracket")
        repeat_node = repeat(parser)
        if !isempty(repeat_node)
            push!(nodes, repeat_node)
        else
            return Dict()
        end
    end
    if isempty(nodes)
        return Dict()
    end
    if length(nodes) > 1
        return Dict("kind" => "concatination", "value" => nodes)
    else
        return nodes[1]
    end
end

# Функция для разбора альтернатив
function alternation(parser::RegexParser)
    concat = concatination(parser)
    if isempty(concat)
        return Dict()
    end
    nodes = Any[concat]
    while parser.index <= length(parser.pattern) && parser.pattern[parser.index].kind == "|"
        parser.index += 1
        if parser.index > length(parser.pattern)
            return Dict() # end after |
        end
        if parser.pattern[parser.index].kind == "|" || parser.pattern[parser.index].kind == "right_bracket"
            return Dict()
        end
        concat = concatination(parser)
        if isempty(concat)
            return Dict()
        end
        push!(nodes, concat)
    end
    if length(nodes) > 1
        return Dict("kind" => "alternative", "value" => nodes)
    else
        return nodes[1]
    end
end

# Функция для разбора всего выражения
function parseRg(parser::RegexParser)
    node = alternation(parser)
    if isempty(node)
        return false
    end

    if parser.index <= length(parser.pattern)
        println("LEFT SYMBOLS")
        return false
    end
    for id in parser.save_ref_ids
        if !(id in parser.save_group_ids)
            println("Error: reference unknown")
            return false
        end
    end
    parser.ast_tree = node
    return true
end

# Функция для построения грамматики
function build_grammar(parser::RegexParser, ast, rule_name::String="S", index::Int=0)
    if ast["kind"] == "capture_group"
        if !haskey(parser.group_ids, ast["key"])
            group_rule_name = "G$(index)"
            parser.group_ids[ast["key"]] = group_rule_name
            index += 1
        else
            group_rule_name = parser.group_ids[ast["key"]]
        end

        parser.rules[rule_name] = []
        push!(parser.rules[rule_name], group_rule_name)
        build_grammar(parser, ast["value"], group_rule_name, index)
    elseif ast["kind"] == "alternative"
        alternatives = []
        parser.rules[rule_name] = []
        for option in ast["value"]
            name = "$(rule_name)_$(index)"
            index += 1
            parser.rules[name] = []
            push!(alternatives, name)
            build_grammar(parser, option, name, index)
        end
        append!(parser.rules[rule_name], alternatives)
    elseif ast["kind"] == "concatination"
        concatenation = []
        for item in ast["value"]
            name = "$(rule_name)_$(index)"
            index += 1
            parser.rules[name] = []
            push!(concatenation, name)
            build_grammar(parser, item, name, index)
        end
        parser.rules[rule_name] = []
        push!(parser.rules[rule_name], join(concatenation, " "))
    elseif ast["kind"] == "letter"
        parser.rules[rule_name] = []
        push!(parser.rules[rule_name], ast["value"])
    elseif ast["kind"] == "referenseDigit"
        parser.rules[rule_name] = []
        referenseDigit = ast["value"]
        if !haskey(parser.group_ids, referenseDigit)
            parser.rules["G$(index)"] = []
            parser.group_ids[referenseDigit] = "G$(index)"
        end
        push!(parser.rules[rule_name], parser.group_ids[referenseDigit])
    elseif ast["kind"] == "repeat"
        parser.rules[rule_name] = []
        name = "$(rule_name)_$(index)"
        index += 1
        push!(parser.rules[rule_name], join([name, rule_name]))
        push!(parser.rules[rule_name], "eps")
        build_grammar(parser, ast["value"], name, index)
    elseif ast["kind"] == "lookahead"
        name = "LOOK_$(index)"
        index += 1
        parser.rules[name] = []
        parser.rules[rule_name] = []
        push!(parser.rules[rule_name], name)
        push!(parser.rules[name], "eps")
    elseif ast["kind"] == "non_capturing"
        parser.rules[rule_name] = []
        capturing_rule_name = "NonCap_$(index)"
        index += 1
        push!(parser.rules[rule_name], capturing_rule_name)
        build_grammar(parser, ast["value"], capturing_rule_name, index)
    end
    return parser.rules
end

# Функция для вывода грамматики
function print_grammar(grammar_rules)
    for (nt, rules) in sort(collect(grammar_rules))
        if length(rules) == 1
            println("$nt -> $(rules[1])")
        else
            println("$nt -> $(join(rules, " | "))")
        end
    end
end

# Пример использования
ok_patterns = [
    "((hj)|(gh))(k|(?2)|(?1))",
    "(ahg|(t))(alh|(?3))",
    "(a*(?=b)*)c*",
    "(auy|hh*|wr)*|d",
    "((aaa|ba)*ca)*",
    "(afg*|(?:(kj)*|rt))rtd",
    "(?=ab)(?=bb)bbb",
    "(tyu|fg)(?1)",
    "att(?=dfb|gh)dttt",
    "(a(?1)b|c)",
    "(?1)(first|second|third)",
    "fb**"
]

error_patterns = [
    "agg*|bsf)df",
    "(?2)(a|(b|c)(gh)",
    "((ag)(reb)(tgsc)(dsg)((dg)f)((dfd))(fghh)(eri)(ghj)(yry))",
    "(a)(?2)",
    "(?=(dfa*))",
    "sds*(?=rt(?=rt))dfdg",
    "(?3)(ty*|op)(i*o)*",
    "(?399)(ty*|o",
    "(gh||dfb)",
    "gh||dfb)",
    "(gh<dfb)",
    "fb|*",
    ")fb|ui",
    "()",
    "(?=(?:sd))|(?=(?=df))|(?=(?=df))"
]

for pattern in ok_patterns
    parser = RegexParser(pattern)
    println("Entered pattern: ", pattern)
    result = get_tokens(parser)
    if result
        result = parseRg(parser)
        println("Pattern: $pattern -> Valid: $result")
        if result
            grammar = build_grammar(parser, parser.ast_tree)
            print_grammar(parser.rules)
        end
    else
        println("Ошибка: token()")
        println("Pattern: $pattern -> Valid: False")
    end
end
