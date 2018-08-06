import math
from gmpy2 import mpq as Fraction, is_square, isqrt
from quadratic import Quadratic
from expression import Expression
from solver.base import BaseTchisla

__all__ = ["QuadraticTchisla"]

class QuadraticTchisla(BaseTchisla):
    constructor = Quadratic

    def __init__(self, n):
        super().__init__(n)
        print(self.limits)
        self.MAX_QUADRATIC_POWER = self.limits["max_quadratic_power"]

    @staticmethod
    def name():
        return "quadratic"

    def range_check(self, x):
        x = x.rational_part
        return x.numerator <= self.MAX and x.denominator <= self.MAX

    def integer_check(self, x):
        return x.quadratic_power == 0 and x.rational_part.denominator == 1

    def add(self, p, q, digits):
        result = p + q
        if result is not None:
            self.check(result, digits, Expression.add(p, q))

    def subtract(self, p, q, digits):
        if p == q:
            return
        result = p - q
        if result is not None:
            if result.rational_part < 0:
                result = -result
                p, q = q, p
            self.check(result, digits, Expression.subtract(p, q))

    def multiply(self, p, q, digits):
        self.check(p * q, digits, Expression.multiply(p, q))

    def divide(self, p, q, digits):
        quotient = p / q
        self.check(quotient, digits, Expression.divide(p, q))
        self.check(quotient ** -1, digits, Expression.divide(q, p))

    def exponent(self, p, q, digits):
        if not self.integer_check(q) or p == 1:
            return
        base = math.log2(max(p.rational_part.numerator, p.rational_part.denominator))
        exp = Expression.power(p, q), Expression.power(p, Expression.negate(q))
        q_max = q.rational_part.numerator
        while base * q_max > self.MAX_DIGITS << p.quadratic_power:
            if q_max & 1 == 0:
                q_max >>= 1
                exp = Expression.sqrt(exp[0]), Expression.sqrt(exp[1])
            else:
                return
        q_min = q_max
        while q_min & 1 == 0:
            q_min >>= 1
            exp = Expression.sqrt(exp[0]), Expression.sqrt(exp[1])
        q = q_min
        x = p ** q
        while q <= q_max:
            if not self.range_check(x):
                break
            self.check(x, digits, exp[0], need_sqrt = q == q_min)
            self.check(Quadratic.inverse(x), digits, exp[1], need_sqrt = q == q_min)
            q <<= 1
            x = Quadratic.square(x)
            if q <= q_max:
                exp = exp[0].args[0], exp[1].args[0]

    def sqrt(self, x, digits):
        if x.quadratic_power < self.MAX_QUADRATIC_POWER:
            y = Quadratic.sqrt(x)
            if y is not None:
                self.check(y, digits, Expression.sqrt(x))
