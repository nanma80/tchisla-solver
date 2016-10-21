import math
from gmpy2 import is_square, isqrt
from expression import Expression
from solver.base import BaseTchisla

__all__ = ["IntegralTchisla"]

class IntegralTchisla(BaseTchisla):
    constructor = int

    def __init__(self, n):
        super().__init__(n)

    @staticmethod
    def name():
        return "integral"

    def range_check(self, x):
        return x <= self.MAX

    def integer_check(self, x):
        return True

    def divide(self, p, q, digits):
        if p < q:
            p, q = q, p
        if p % q == 0:
            self.check(p // q, digits, Expression.divide(p, q))

    def exponent(self, p, q, digits):
        if p == 1:
            return
        p_digits = math.log2(p)
        exp = Expression.power(p, q)
        while p_digits * q > self.MAX_DIGITS:
            if q & 1 == 0:
                q >>= 1
                exp = Expression.sqrt(exp)
            else:
                return
        self.check(p ** q, digits, exp)

    def sqrt(self, x, digits):
        if is_square(x):
            y = int(isqrt(x))
            self.check(y, digits, Expression.sqrt(x))
