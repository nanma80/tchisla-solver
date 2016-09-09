import sys
import numbers
import operator
from itertools import starmap
from functools import reduce
from gmpy2 import mpz, mpq as Fraction, is_square, isqrt

__all__ = ["Quadratic"]

primes = (2, 3, 5, 7)

def exp2(n):
    return {1: 0, 3: 1, 7: 2, 15: 3}[n ^ (n - 1)]

_PyHASH_MODULUS = sys.hash_info.modulus

class Quadratic(numbers.Real):
    __slots__ = ("rational_part", "quadratic_part")

    def __new__(cls, rational_part = Fraction(), quadratic_part = None):
        self = super(Quadratic, cls).__new__(cls)
        if type(rational_part) is str:
            rational_part = Fraction(rational_part)
        if isinstance(rational_part, (int, type(mpz()), type(Fraction()))):
            self.rational_part = Fraction(rational_part)
            self.quadratic_part = quadratic_part
            return self
        elif isinstance(rational_part, Quadratic):
            self.rational_part = rational_part.rational_part
            self.quadratic_part = rational_part.quadratic_part
            return self
        else:
            raise NotImplementedError

    def __str__(self):
        if self.quadratic_part:
            q = reduce(operator.mul, starmap(operator.pow, zip(primes, self.quadratic_part[1:])))
            quadratic_part_string = "sqrt(" * self.quadratic_part[0] + str(q) + ")" * self.quadratic_part[0]
            if self.rational_part == 1:
                return quadratic_part_string
            elif self.rational_part == -1:
                return "-" + quadratic_part_string
            else:
                return str(self.rational_part) + "*" + quadratic_part_string
        else:
            return str(self.rational_part)

    def _operator_fallbacks(monomorphic_operator, fallback_operator):
        def forward(a, b):
            if isinstance(b, (int, type(mpz()), type(Fraction()), Quadratic)):
                return monomorphic_operator(a, Quadratic(b))
            else:
                return NotImplemented

        def reverse(b, a):
            if isinstance(a, (int, type(mpz()), type(Fraction()), Quadratic)):
                return monomorphic_operator(a, Quadratic(b))
            else:
                return NotImplemented

        return forward, reverse

    def _add(x, y):
        if x.quadratic_part == y.quadratic_part:
            if x.rational_part + y.rational_part == 0:
                return Quadratic()
            else:
                return Quadratic(x.rational_part + y.rational_part, x.quadratic_part)

    __add__, __radd__ = _operator_fallbacks(_add, operator.add)

    def _sub(x, y):
        if x.quadratic_part == y.quadratic_part:
            if x.rational_part == y.rational_part:
                return Quadratic()
            else:
                return Quadratic(x.rational_part - y.rational_part, x.quadratic_part)

    __sub__, __rsub__ = _operator_fallbacks(_sub, operator.sub)

    def _mul(x, y):
        r = x.rational_part * y.rational_part
        if x.quadratic_part is None:
            return Quadratic(r, y.quadratic_part)
        if y.quadratic_part is None:
            return Quadratic(r, x.quadratic_part)

        p = x.quadratic_part
        q = y.quadratic_part
        quadratic_power = max(p[0], q[0])
        exp_quadratic_power = 1 << quadratic_power
        shifts = quadratic_power - p[0], quadratic_power - q[0]
        prime_power_list = []
        mask = 0
        for index in range(len(primes)):
            power = (p[index + 1] << shifts[0]) + (q[index + 1] << shifts[1])
            if power >= exp_quadratic_power:
                r *= primes[index]
                power -= exp_quadratic_power
            prime_power_list.append(power)
            mask |= power
        if mask == 0:
            return Quadratic(r)
        mask_shift = exp2(mask)
        return Quadratic(
            r,
            (quadratic_power - mask_shift,) + tuple(map(lambda n: n >> mask_shift, prime_power_list))
        )

    __mul__, __rmul__ = _operator_fallbacks(_mul, operator.mul)

    def _div(x, y):
        r = x.rational_part / y.rational_part
        if y.quadratic_part is None:
            return Quadratic(r, x.quadratic_part)

        p = x.quadratic_part or (0, 0, 0, 0, 0)
        q = y.quadratic_part
        quadratic_power = max(p[0], q[0])
        exp_quadratic_power = 1 << quadratic_power
        shifts = quadratic_power - p[0], quadratic_power - q[0]
        prime_power_list = []
        mask = 0
        for index in range(len(primes)):
            power = (p[index + 1] << shifts[0]) - (q[index + 1] << shifts[1])
            if power < 0:
                r /= primes[index]
                power += exp_quadratic_power
            prime_power_list.append(power)
            mask |= power
        if mask == 0:
            return Quadratic(r)
        mask_shift = exp2(mask)
        return Quadratic(
            r,
            (quadratic_power - mask_shift,) + tuple(map(lambda n: n >> mask_shift, prime_power_list))
        )

    __truediv__, __rtruediv__ = _operator_fallbacks(_div, operator.truediv)

    def __float__(x):
        raise NotImplementedError

    def __floordiv__(x, y):
        raise NotImplementedError

    def __rfloordiv__(x, y):
        raise NotImplementedError

    def __mod__(x, y):
        raise NotImplementedError

    def __rmod__(x, y):
        raise NotImplementedError

    def inverse(x):
        r = x.rational_part ** -1
        q = x.quadratic_part
        if q is None:
            return Quadratic(r)
        prime_base = 1
        prime_power_list = [q[0]]
        for index in range(len(primes)):
            if q[index + 1]:
                r /= primes[index]
                prime_power_list.append((1 << q[0]) - q[index + 1])
            else:
                prime_power_list.append(0)
        return Quadratic(r, tuple(prime_power_list))

    def __pow__(x, y):
        power = None
        inverse = False
        if isinstance(y, (int, type(mpz()))):
            power = abs(y)
            inverse = y < 0
        elif y.quadratic_part is None and y.rational_part.denominator == 1:
            power = abs(y.rational_part.numerator)
            inverse = y.rational_part.numerator < 0
        else:
            raise NotImplementedError

        if power == 0:
            return Quadratic(1)
        r = x.rational_part ** power
        if x.quadratic_part is None:
            return Quadratic(r ** -1) if inverse else Quadratic(r)
        quadratic_power = x.quadratic_part[0]
        while quadratic_power and power & 1 == 0:
            quadratic_power -= 1
            power >>= 1
        exp_quadratic_power = 1 << quadratic_power
        prime_power_list = []
        for index in range(len(primes)):
            p = x.quadratic_part[index + 1] * power
            r *= primes[index] ** (p // exp_quadratic_power)
            prime_power_list.append(p % exp_quadratic_power)
        result = None
        if quadratic_power == 0:
            result = Quadratic(r)
        else:
            result = Quadratic(r, (quadratic_power,) + tuple(prime_power_list))
        return result.inverse() if inverse else result

    def __rpow__(x, y):
        raise NotImplementedError

    @staticmethod
    def sqrt(x):
        p = x.rational_part
        s, t = p.numerator, p.denominator
        q = x.quadratic_part
        if p == 0:
            return Quadratic()
        elif p < 0:
            raise NotImplementedError
        elif q is None:
            if is_square(s) and is_square(t):
                return Quadratic(Fraction(isqrt(s), isqrt(t)))
            else:
                q = (0, 0, 0, 0, 0)

        r = Fraction(1, t)
        p = s * t
        prime_power_list = []
        for index in range(len(primes)):
            prime = primes[index]
            power = 0
            while p % prime == 0:
                p //= prime
                power += 1
            r *= prime ** (power >> 1)
            prime_power_list.append(((power & 1) << q[0]) | q[index + 1])
        if not is_square(p):
            return
        return Quadratic(r * isqrt(p), (q[0] + 1,) + tuple(prime_power_list))

    def __pos__(x):
        return Quadratic(x.rational_part, x.quadratic_part)

    def __neg__(x):
        return Quadratic(-x.rational_part, x.quadratic_part)

    def __abs__(x):
        return Quadratic(abs(x.rational_part), x.quadratic_part)

    def __int__(x):
        if x.quadratic_part is None and x.rational_part.denominator == 1:
            return int(x.rational_part.numerator)

    def __trunc__(x):
        raise NotImplementedError

    def __floor__(x):
        raise NotImplementedError

    def __ceil__(x):
        raise NotImplementedError

    def __round__(x):
        raise NotImplementedError

    def __hash__(self):
        if self.quadratic_part is None:
            return hash(self.rational_part)
        else:
            return hash(self.rational_part) * hash(self.quadratic_part) % _PyHASH_MODULUS

    def __eq__(x, y):
        if isinstance(y, (int, type(mpz()), type(Fraction()))):
            return x.quadratic_part is None and x.rational_part == y
        elif isinstance(y, Quadratic):
            return x.rational_part == y.rational_part and x.quadratic_part == y.quadratic_part
        else:
            return NotImplemented

    def __lt__(x, y):
        raise NotImplementedError

    def __gt__(x, y):
        raise NotImplementedError

    def __le__(x, y):
        raise NotImplementedError

    def __ge__(x, y):
        raise NotImplementedError

    def __bool__(x):
        return x.quadratic_part is None and x.rational_part == 0

    def __reduce__(self):
        return (self.__class__, (str(self),))

    def __copy__(self):
        if type(self) is Quadratic:
            return self
        return self.__class__(self)

    def __deepcopy__(self):
        if type(self) is Quadratic:
            return self
        return self.__class__(self)
