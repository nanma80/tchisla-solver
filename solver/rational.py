import math
from gmpy2 import mpq as Fraction, is_square, isqrt
from expression import Expression
from solver.base import BaseTchisla

__all__ = ["RationalTchisla"]

class RationalTchisla(BaseTchisla):
    constructor = Fraction

    def __init__(self, n):
        super().__init__(n)

    @staticmethod
    def name():
        return "rational"

    def range_check(self, x):
        return x.numerator <= self.MAX and x.denominator <= self.MAX

    def integer_check(self, x):
        return x.denominator == 1

    def exponent(self, p, q, digits):
        if q.denominator != 1 or p == 1:
            return
        p_digits = math.log2(max(p.numerator, p.denominator))
        q_int = q.numerator
        exp = Expression.power(p, q), Expression.power(p, Expression.negate(q))
        while p_digits * q_int > self.MAX_DIGITS:
            if q_int & 1 == 0:
                q_int >>= 1
                exp = Expression.sqrt(exp[0]), Expression.sqrt(exp[1])
            else:
                return
        x = p ** q_int
        self.check(x, digits, exp[0])
        self.check(x ** -1, digits, exp[1])

    def sqrt(self, x, digits):
        if is_square(x.numerator) and is_square(x.denominator):
            y = isqrt(x.numerator)
            z = isqrt(x.denominator)
            self.check(Fraction(y, z), digits, Expression.sqrt(x))
