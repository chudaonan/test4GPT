import re

# 定义一个简单的词法分析器来分割输入的tokens
class Lexer:
    def __init__(self, input):
        self.tokens = re.findall(r'\b\w+\b|[\(\)\{\};,=^!*&|<>\+\-]', input)
        self.index = 0

    def get_next_token(self):
        if self.index < len(self.tokens):
            token = self.tokens[self.index]
            self.index += 1
            return token
        return None

# 定义一个解析器类
class Parser:
    def __init__(self, lexer):
        self.lexer = lexer
        self.current_token = self.lexer.get_next_token()

    def eat(self, token_type):
        if self.current_token == token_type:
            self.current_token = self.lexer.get_next_token()
        else:
            raise Exception(f'Unexpected token: {self.current_token}')

    def program(self):
        statements = []
        while self.current_token is not None and self.current_token != 'EOF':
            statements.append(self.statement())
        return {'program': statements}

    def statement(self):
        if self.current_token == 'return':
            return self.ret_stat()

    def if_stat(self):
        self.eat('if')
        self.eat('(')
        condition = self.expr()
        self.eat(')')
        true_statement = self.statement()
        false_statement = None
        if self.current_token == 'else':
            self.eat('else')
            false_statement = self.statement()
        return {'if': condition, 'true': true_statement, 'false': false_statement}

    def while_stat(self):
        self.eat('while')
        self.eat('(')
        condition = self.expr()
        self.eat(')')
        body = self.statement()
        return {'while': condition, 'body': body}

    def var_stat(self):
        self.eat('var')
        var_name = self.current_token
        self.eat('ID')
        self.eat('=')
        var_value = self.expr()
        self.eat(';')
        return {'var': var_name, 'value': var_value}

    def assign_stat(self):
        var_name = self.current_token
        self.eat('ID')
        self.eat('=')
        var_value = self.expr()
        self.eat(';')
        return {'assign': var_name, 'value': var_value}

    def block_stat(self):
        self.eat('{')
        statements = []
        while self.current_token != '}':
            statements.append(self.statement())
        self.eat('}')
        return {'block': statements}

    def func_stat(self):
        self.eat('fun')
        func_name = self.current_token
        self.eat('ID')
        self.eat('(')
        params = self.params() if self.current_token != ')' else []
        self.eat(')')
        body = self.block_stat()
        return {'function': func_name, 'params': params, 'body': body}

    def atom(self):
        if self.current_token == '(':
            self.eat('(')
            node = self.expr()
            self.eat(')')
            return node
        elif self.current_token.isdigit():
            node = {'num': int(self.current_token)}
            self.eat('NUM')
            return node
        elif self.current_token in ['true', 'false']:
            node = {'bool': self.current_token == 'true'}
            self.eat(self.current_token)
            return node
        else:
            node = self.call() if self.current_token == 'ID' and self.lexer.tokens[self.lexer.index] == '(' else {
                'var': self.current_token}
            self.eat('ID')
            return node

    def pow(self):
        node = self.atom()
        if self.current_token == '^':
            self.eat('^')
            node = {'pow': [node, self.pow()]}
        return node

    def unary(self):
        nodes = []
        while self.current_token in ['-', '!']:
            token = self.current_token
            self.eat(token)
            nodes.append(token)
        node = self.pow()
        return {'unary': nodes, 'node': node} if nodes else node

    def factor(self):
        node = self.unary()
        while self.current_token in ['*', '/']:
            token = self.current_token
            self.eat(token)
            node = {'binary': [node, token, self.unary()]}
        return node

    def term(self):
        node = self.factor()
        while self.current_token in ['+', '-']:
            token = self.current_token
            self.eat(token)
            node = {'binary': [node, token, self.factor()]}
        return node

    def comparison(self):
        node = self.term()
        while self.current_token in ['>', '>=', '<', '<=']:
            token = self.current_token
            self.eat(token)
            node = {'comparison': [node, token, self.term()]}
        return node

    def equality(self):
        node = self.comparison()
        while self.current_token in ['==', '!=']:
            token = self.current_token
            self.eat(token)
            node = {'equality': [node, token, self.comparison()]}
        return node

    def logic_and(self):
        node = self.equality()
        while self.current_token == 'and':
            self.eat('and')
            node = {'logic_and': [node, self.equality()]}
        return node

    def logic_or(self):
        node = self.logic_and()
        while self.current_token == 'or':
            self.eat('or')
            node = {'logic_or': [node, self.logic_and()]}
        return node

# 测试解析器
input_program = '''
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
lexer = Lexer(input_program)
parser = Parser(lexer)
parsed_program = parser.program()
print(parsed_program)
