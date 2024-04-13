def make_tk(type, val=None):
    return [type, val] if val is not None else [type]


def tk_tag(t):
    return t[0]


def tk_val(t):
    return t[1] if len(t) > 1 else None


def error(src, msg):
    raise Exception(f'<{src}>: {msg}')


def lexer(prog):
    def err(msg):
        error('lexer', msg)

    pos = -1
    cur = None

    keywords = ['return', 'fun', 'print', 'if', 'else', 'var', 'true', 'false', 'while', ]

    def next():
        nonlocal pos, cur

        t = cur

        pos = pos + 1
        if pos >= len(prog):
            cur = 'eof'
        else:
            cur = prog[pos]

        return t

    def peek():
        return cur

    def match(m):
        if cur != m:
            err(f'期望是{m},实际是{cur}')

        return next()

    def ws_skip():
        while peek() in [' ', '\t', '\r', '\n']:
            next()

    def string():

        match('"')
        r = ''

        while peek() != '"':
            r = r + next()

        match('"')

        return make_tk('str', r)

    def isdigit(c):
        return c >= '0' and c <= '9'

    def num():
        r = next()

        while isdigit(peek()):
            r = r + next()

        if peek() == '.':
            r = r + next()
            while isdigit(peek()):
                r = r + next()
        return make_tk('num', float(r) if '.' in r else int(r))

    def isletter_(c):
        return c == '_' or (c >= 'a' and c <= 'z') or (c >= 'A' and c <= 'Z')

    def isletter_or_digit(c):
        return isdigit(c) or isletter_(c)

    def id():
        r = next()

        while isletter_or_digit(peek()):
            r = r + next()

        if r in keywords:
            return make_tk(r)

        return make_tk('id', r)

    def token():
        ws_skip()

        t = peek()

        if t == 'eof':
            return make_tk('eof')

        if t in [':', ',', '+', '-', '*', '/', ';', '(', ')', '{', '}', '[', ']', '!']:
            next()
            return make_tk(t)

        if t == '=':
            next()
            if peek() == '=':
                next()
                return make_tk('==')
            else:
                return make_tk('=')

        if t == '>':
            next()
            if peek() == '=':
                next()
                return make_tk('>=')
            else:
                return make_tk('>')

        if t == '<':
            next()
            if peek() == '=':
                next()
                return make_tk('<=')
            else:
                return make_tk('<')

        if t == '"':
            return string()

        if isdigit(t):
            return num()

        if isletter_(t):
            return id()

        err(f'非法字符{t}')

    next()

    tokens = []

    while True:
        t = token()
        tokens.append(t)
        if tk_tag(t) == 'eof':
            break

    return tokens


def make_tokenizer(tokens, err):
    cur = None
    pos = -1

    def next():
        nonlocal cur, pos

        t = cur

        pos = pos + 1
        if pos >= len(tokens):
            cur = ['eof']
        else:
            cur = tokens[pos]

        return t

    def peek(k=0, return_type='tag'):
        if k + pos < len(tokens):
            if return_type == 'tag':
                return tk_tag(tokens[pos + k])
            elif return_type == 'full':
                return tokens[pos + k]
            else:
                raise ValueError("Invalid return type. Use 'tag' or 'full'.")
        else:
            return 'eof'

    def match(*m):
        if peek() not in m:
            err(f'期望{m},实际为{peek()}')

        return next()

    next()
    return (next, peek, match)


def cilly_parser(tokens):
    def err(m):
        error('cilly parser', m)

    next, peek, match = make_tokenizer(tokens, err)
    func_list = []  # 创建函数列表,每创建或者赋值一个新的函数就将函数名加入列表

    def program():  # 解析程序，由多个语句组成，直到‘eof’解析完成
        r = []
        while peek() != 'eof':
            r.append(statement())
        return ['program', r]

    def statement():  # 解析单个语句
        nonlocal func_list
        t = peek()
        if t == 'return':
            return return_statement()
        elif t == 'fun':
            return function_definition()
        elif t == 'if':
            return if_statement()
        elif t == 'print':
            return print_statement()
        elif t == 'var':
            return var_statement()
        elif t == 'while':
            return while_statement()
        elif t == 'id':
            # 如果标签是id分为两类，若对象名是函数名则进入函数使用解析，其他则进入普通赋值解析
            print(f"Current token: {t}, Function list: {func_list}")
            if peek(return_type='full')[1] in func_list:
                return func_use()
            else:
                return assign_statement()
        else:
            err(f'Unexpected token: {t}')

    # 函数使用语句解析
    # 表达式 + ';'
    def func_use():
        exp = expr()
        match(';')
        return ['func_use', exp]

    # 赋值语句解析
    # 变量名 + '=' + 表达式 + ';'
    def assign_statement():
        variable = match('id')[1]
        match('=')
        exp = expr()
        match(';')
        return ['assign_statement', variable, exp]

    # var语句解析
    # 'var' + 变量名 + 表达式 + ';'
    def var_statement():
        match('var')
        variables = []
        while peek() != ';':
            var_name = match('id')[1]
            if peek() == '=':
                match('=')
                var_value = expr()
                # 如果赋值的对象是函数，就将对象名加入函数列表
                if isinstance(var_value, list) and var_value[0] == 'function_call':
                    func_list.append(var_name)
            else:
                var_value = None
            variables.append([var_name, var_value])
        match(';')
        return ['var', variables]

    # print语句解析
    # print + '(' + 表达式 + ') '+ ';'
    def print_statement():
        match('print')
        match('(')
        expressions = []
        while peek() != ')':
            expressions.append(expr())
            if peek() == ',':
                match(',')
        match(')')
        match(';')
        return ['print', expressions]

    # while语句解析
    # while + 条件表达式 + 语句块/单个语句
    def while_statement():
        match('while')
        condition = expr()
        then_clause = statement() if peek() != '{' else block()
        return ['while', condition, then_clause]

    # if语句解析
    # if + 条件表达式 + 语句块/单个语句 +（else + 语句块/单个语句）

    def if_statement():
        match('if')
        condition = expr()
        then_clause = statement() if peek() != '{' else block()
        else_clause = None
        if peek() == 'else':
            match('else')
            else_clause = statement() if peek() != '{' else block()
        return ['if', condition, then_clause, 'else', else_clause]

    # return语句解析
    # return + 表达式/null  + ';'
    def return_statement():
        match('return')
        if peek() != ';':
            e = expr()
        else:
            e = None
        match(';')
        return ['return', e]

    # 函数定义语句解析
    # fun + id +（ + id + ）+ block
    def function_definition():
        match('fun')
        func_name = match('id')[1]
        # 将函数名加入函数列表
        func_list.append(func_name)
        match('(')
        para = []
        if peek() != ')':
            para.append(match('id')[1])
            while peek() == ',':
                match(',')
                para.append(match('id')[1])
        match(')')
        body = block()
        return ['function_definition', func_name, para, body]

    def block():  # 语句块解析
        match('{')
        state = []
        while peek() != '}':
            state.append(statement())
        match('}')
        return ['block', state]

    def expr():  # 表达式解析，按照运算符优先级别不断递归
        return logic_or()

    def logic_or():
        left = logic_and()
        while peek() == 'or':
            operator = match('or')
            right = logic_and()
            left = ['or', left, right]
        return left

    def logic_and():
        left = equality()
        while peek() == 'and':
            operator = match('and')
            right = equality()
            left = ['and', left, right]
        return left

    def equality():
        left = comparison()
        while peek() in ['==', '!=']:
            operator = match('==', '!=')
            right = comparison()
            left = [operator, left, right]
        return left

    def comparison():
        left = term()
        while peek() in ['>', '>=', '<', '<=']:
            operator = match('>', '>=', '<', '<=')
            right = term()
            left = [operator, left, right]
        return left

    def term():
        left = factor()
        while peek() in ['+', '-']:
            operator = match('+', '-')
            right = factor()
            left = [operator, left, right]
        return left

    def factor():
        left = unary()
        while peek() in ['*', '/']:
            operator = match('*', '/')
            right = unary()
            left = [operator, left, right]
        return left

    def unary():
        if peek() in ['-', '!']:
            operator = match('-', '!')
            if operator == '!':  # 阶乘操作
                return ['factorial', unary()]
            operand = unary()
            return [operator, operand]
        else:
            return pow()

    def pow():
        left = atom()
        if peek() == '^':
            operator = match('^')
            right = pow()
            return ['^', left, right]
        return left

    def atom():
        if peek() == '(':
            match('(')
            expression = expr()
            match(')')
            return expression
        elif peek() == 'id':
            if peek(1) != '(':
                return match('id')[1]
            else:
                # 如果下一个标记是左括号，表示这是一个函数调用
                func_name = match('id')[1]
                match('(')
                arguments = []
                if peek() != ')':
                    arguments.append(expr())
                    while peek() == ',':
                        match(',')
                        arguments.append(expr())
                match(')')
                return ['function_call', func_name, arguments]
        elif peek() == 'num':
            value = match('num')[1]
            if peek() == '!':  # 如果num类型的后面跟上‘！’，则代表使用阶乘运算
                match('!')
                return ['!', value]
            else:
                return value
        elif peek() == 'str':
            return match('str')[1]
        elif peek() in ['true', 'false']:
            return match('true', 'false')
        else:
            err(f'Unexpected token: {peek()}')

    return program()


test = '''

fun fact(n){
    if(n==0)
        return 1;
    else
        return n * fact(n-1);

}

print(fact(10));

fun k(x){
    fun ky(y){
        return x + y;
    }

    return ky;
}
var ky = k(3);
print(ky(5));

fun fib0(n){
    if(n < 2)
        return n;
    else
        return fib0(n-1) + fib0(n-2);
}

fun fib(n){
    var f0 = 0;
    var f1 = 1;

    while(n > 0){
        var t = f1;
        f1 = f0 + f1;
        f0 = t;
        n = n - 1;
    }

    return f0;
}

print(fib(10),"hello world");

fun make_count(n){
    fun inc(){
        n = n + 1;
        return n;
    }

    return inc;
}

fun make_dog(){
    var weight = 10;
    fun eat(m){
        weight = m + weight;        
    }

    fun get(){
        return weight;
    }

    fun dispatch(m){

        if(m == "eat"){
            return eat;
        } else if (m == "get"){
            return get();
        }
    }

    return dispatch;
}

var dog = make_dog();
var eat = dog("eat");


eat(10);
print(dog("get"));
eat(20);
print(dog("get"));



var c1 = make_count(1);
var c2 = make_count(1);

print(c1(), c1(), c1(), c2());

print(2*10!);

'''

l = lexer(test)
c = cilly_parser(l)

