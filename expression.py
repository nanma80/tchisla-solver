import operator

__all__ = ["Expression"]

operators = {
    "+": {
        "type": "binary",
        "precedence": 1,
        "abelian": True,
        "associativity": "ltr"
    },
    "-": {
        "type": "binary",
        "precedence": 1,
        "abelian": False,
        "associativity": "ltr"
    },
    "negate": {
        "type": "unary",
        "precedence": 2,
        "abelian": False,
        "string": lambda s: "-" + s
    },
    "*": {
        "type": "binary",
        "precedence": 3,
        "abelian": True,
        "associativity": "ltr"
    },
    "/": {
        "type": "binary",
        "precedence": 3,
        "abelian": False,
        "associativity": "ltr"
    },
    "^": {
        "type": "binary",
        "precedence": 4,
        "abelian": False,
        "associativity": "rtl"
    },
    "factorial": {
        "type": "unary",
        "precedence": 5,
        "abelian": True,
        "string": lambda s: s + "!"
    },
    "sqrt": {
        "type": "unary",
        "precedence": 6,
        "abelian": True
    },
    "number": {
        "type": "number",
        "precedence": 7,
        "abelian": False
    },
    "concat": {
        "type": "number",
        "precedence": 7,
        "abelian": False
    }
}

class Expression:
    __slots__ = ("name", "args")

    def __init__(self, name, *args):
        self.name = name
        self.args = tuple(args)

    def __str__(self):
        return Expression.str(self)

    @staticmethod
    def str(expression, *, spaces = False):
        expression_operator = operators[Expression.type(expression)]
        expression_type = expression_operator["type"]
        if expression_type == "number":
            if expression_operator == operators["number"]:
                return str(expression)
            else:
                return str(expression.args[0])
        elif expression_type == "unary":
            arg = expression.args[0]
            string = Expression.str(arg, spaces = spaces)
            if Expression.type(expression) == "sqrt":
                sqrt_depth = 1
                while Expression.type(arg) == "sqrt":
                    sqrt_depth += 1
                    arg = arg.args[0]
                string = Expression.str(arg, spaces = spaces)
                return "\u221a" * sqrt_depth + "(" + string + ")"
            else:
                comparator = operator.lt if expression_operator["abelian"] else operator.le
                if comparator(
                    operators[Expression.type(arg)]["precedence"],
                    expression_operator["precedence"]
                ):
                    string = "(" + string + ")"
                return expression_operator["string"](string)
        else:
            delimiter = " " + expression.name + " " if spaces else expression.name
            def mapping(arg):
                index, arg = arg
                string = Expression.str(arg, spaces = spaces)
                op = operators[Expression.type(arg)]
                precedence_difference = op["precedence"] - expression_operator["precedence"]
                need_brackets = precedence_difference < 0 or (
                    precedence_difference == 0
                    and not expression_operator["abelian"]
                    and (expression_operator["associativity"] == "ltr") ^ (index == 0)
                )
                return "(" + string + ")" if need_brackets else string
            return delimiter.join(map(mapping, enumerate(expression.args)))

    @staticmethod
    def type(expression):
        return expression.name if type(expression) is Expression else "number"

    @staticmethod
    def concat(x):
        return Expression("concat", x)

    @staticmethod
    def add(*args):
        return Expression("+", *args)

    @staticmethod
    def subtract(x, y):
        return Expression("-", x, y)

    @staticmethod
    def multiply(*args):
        return Expression("*", *args)

    @staticmethod
    def divide(x, y):
        return Expression("/", x, y)

    @staticmethod
    def power(x, y):
        return Expression("^", x, y)

    @staticmethod
    def negate(x):
        return Expression("negate", x)

    @staticmethod
    def sqrt(x):
        return Expression("sqrt", x)

    @staticmethod
    def factorial(x):
        return Expression("factorial", x)
