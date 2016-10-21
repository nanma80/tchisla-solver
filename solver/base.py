import math, sys, copy
import operator
from itertools import count, product, combinations_with_replacement, chain
from functools import reduce
from abc import ABCMeta, abstractmethod
from config import global_config, specials, limits
from gmpy2 import mpq as Fraction, fac as factorial
from expression import Expression

__all__ = ["BaseTchisla"]

class SolutionFoundError(Exception):
    def __init__(self, message):
        self.message = message

class BaseTchisla(metaclass=ABCMeta):
    instances = {}
    last_digit = 0
    __slots__ = ("n", "target", "solutions", "max_depth", "visited", "number_printed", "specials", "limits", "depth_started", "depth_finished", "start_state")

    def __new__(cls, n):
        class_name = cls.name()
        if class_name not in cls.instances:
            cls.instances[class_name] = {}
        if n not in cls.instances[class_name]:
            instance = super(BaseTchisla, cls).__new__(cls)
            instance.solutions = {}
            instance.visited = [None, []]
            instance.depth_started = 0
            instance.depth_finished = 0
            instance.start_state = []
            cls.instances[class_name][n] = instance
        if cls.last_digit != 0 and cls.last_digit != n:
            for x in cls.instances:
                if cls.last_digit in cls.instances[x]:
                    del cls.instances[x][cls.last_digit]
        cls.last_digit = n

        return cls.instances[class_name][n]

    def __init__(self, n):
        self.n = n
        self.target = None
        self.max_depth = None
        self.number_printed = set()

        self.specials = {}
        if n in specials[self.name()]:
            self.specials = specials[self.name()][n]

        self.limits = copy.deepcopy(limits[self.name()]["default"])
        if n in limits[self.name()]:
            self.limits.update(limits[self.name()][n])
        self.MAX = self.limits["max"]
        self.MAX_DIGITS = self.limits["max_digits"]
        self.MAX_CONCAT = self.limits["max_concat"]
        self.MAX_FACTORIAL = self.limits["max_factorial"]

    def insert(self, x, digits, expression):
        self.solutions[x] = digits, expression
        self.visited[digits].append(x)
        if x == self.target:
            raise SolutionFoundError((x, digits))

    @staticmethod
    @abstractmethod
    def name():
        pass

    @abstractmethod
    def range_check(self, x):
        pass

    @abstractmethod
    def integer_check(self, x):
        pass

    def check(self, x, digits, expression, *, need_sqrt = True):
        if not self.range_check(x) or x in self.solutions:
            return
        self.insert(x, digits, expression)
        if need_sqrt:
            self.sqrt(x, digits)
        if self.integer_check(x):
            self.factorial(x, digits)

    def concat(self, digits):
        if digits <= self.MAX_CONCAT:
            x = self.constructor((10 ** digits - 1) // 9 * self.n)
            self.check(x, digits, Expression.concat(x))

    def add(self, p, q, digits):
        self.check(p + q, digits, Expression.add(p, q))

    def subtract(self, p, q, digits):
        if p == q:
            return
        result = p - q
        if result < 0:
            self.check(-result, digits, Expression.subtract(q, p))
        else:
            self.check(result, digits, Expression.subtract(p, q))

    def multiply(self, p, q, digits):
        self.check(p * q, digits, Expression.multiply(p, q))

    def divide(self, p, q, digits):
        quotient = p / q
        if quotient < 1:
            self.check(quotient ** -1, digits, Expression.divide(q, p))
            self.check(quotient, digits, Expression.divide(p, q))
        else:
            self.check(quotient, digits, Expression.divide(p, q))
            self.check(quotient ** -1, digits, Expression.divide(q, p))

    def factorial_divide(self, p, q, digits):
        if p == q or not self.integer_check(p) or not self.integer_check(q):
            return
        x = int(p)
        y = int(q)
        if x < y:
            x, y = y, x
            p, q = q, p
        if x <= self.MAX_FACTORIAL or y <= 2 or x - y == 1 or (
            (x - y) * (math.log2(x) + math.log2(y)) > self.MAX_DIGITS << 1
        ):
            return
        result = reduce(operator.mul, range(x, y, -1))
        p_factorial = Expression.factorial(p)
        q_factorial = Expression.factorial(q)
        self.check(self.constructor(result), digits, Expression.divide(p_factorial, q_factorial))
        if digits == self.max_depth:
            return
        if self.solutions[q][0] == 1:
            self.check(self.constructor(result - 1), digits + 1, Expression.divide(
                Expression.subtract(p_factorial, q_factorial),
                q_factorial
            ))
            self.check(self.constructor(result + 1), digits + 1, Expression.divide(
                Expression.add(p_factorial, q_factorial),
                q_factorial
            ))
            self.check(self.constructor(result >> 1), digits + 1, Expression.divide(
                p_factorial,
                Expression.add(q_factorial, q_factorial)
            ))
        if self.solutions[p][0] == 1:
            self.check(self.constructor(result << 1), digits + 1, Expression.divide(
                Expression.add(p_factorial, p_factorial),
                q_factorial
            ))

    @abstractmethod
    def exponent(self, p, q, digits):
        pass

    @abstractmethod
    def sqrt(self, x, digits):
        pass

    def factorial(self, x, digits):
        if int(x) <= self.MAX_FACTORIAL:
            y = self.constructor(factorial(int(x)))
            self.check(y, digits, Expression.factorial(x))

    def binary_operation(self, p, q, digits):
        self.add(p, q, digits)
        self.subtract(p, q, digits)
        self.multiply(p, q, digits)
        self.divide(p, q, digits)
        self.exponent(p, q, digits)
        self.exponent(q, p, digits)

    def binary_generator(self, digits):
        for d1 in range(1, (digits + 1) >> 1):
            d2 = digits - d1
            yield from product(self.visited[d1], self.visited[d2])
        if digits & 1 == 0:
            yield from combinations_with_replacement(self.visited[digits >> 1], 2)

    def search(self, digits):
        # if already found, raise it
        if self.target in self.solutions:
            solution = self.solutions[self.target]
            raise SolutionFoundError((self.target, solution[0]))

        # no need to search finished depth
        if digits <= self.depth_finished:
            return

        # needs digits + 1 for factorial_divide
        while len(self.visited) <= digits + 1:
            self.visited.append([])

        # restart search for the unfinished depth
        # we need to keep results provided by factorial_divide of last depth
        if self.depth_started < digits:
            self.start_state = copy.copy(self.visited[digits])
            self.depth_started = digits
        for x in self.visited[digits]:
            if x not in self.start_state:
                del self.solutions[x]
        self.visited[digits] = copy.copy(self.start_state)
        if digits in self.specials:
            for (x, expression) in self.specials[digits]:
                self.insert(x, digits, expression)

        self.concat(digits)
        for p, q in self.binary_generator(digits):
            self.binary_operation(p, q, digits)
        for p, q in self.binary_generator(digits):
            self.factorial_divide(p, q, digits)
        self.depth_finished = digits

    def solve(self, target, *, max_depth = None):
        self.target = self.constructor(target)
        self.max_depth = max_depth
        for digits in count(1):
            if digits - 1 == max_depth:
                return
            if global_config["verbose"]:
                print(digits, file=sys.stderr, flush = True)
            try:
                self.search(digits)
            except SolutionFoundError as solution:
                if max_depth is None or solution.message[1] <= max_depth:
                    return solution.message[1]
                return

    def printer(self, n):
        digits, expression = self.solutions[n]
        string = str(digits) + ": " + str(n)
        if expression.name == "concat":
            return string
        else:
            return string + " = " + Expression.str(expression, spaces = True)

    def solution_prettyprint(self, n, *, force_print = False):
        def requirements(expression):
            if type(expression) is Expression:
                return chain(*map(requirements, expression.args))
            else:
                return (expression,)

        if n in self.number_printed or n not in self.solutions:
            return []
        digits, expression = self.solutions[n]
        if expression.name == "concat" and not force_print:
            return []
        solution_list = [self.printer(n)]
        self.number_printed.add(n)
        for x in requirements(expression):
            solution_list += self.solution_prettyprint(x)
        return solution_list

    def full_expression(self, n):
        if type(n) is Expression:
            return Expression(n.name, *map(self.full_expression, n.args))
        _, expression = self.solutions[n]
        if expression.name == "concat":
            return n
        else:
            return Expression(expression.name, *map(self.full_expression, expression.args))
