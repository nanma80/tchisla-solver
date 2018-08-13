import sys
import numbers
import operator
from functools import reduce
from gmpy2 import mpz, mpq as Fraction, is_square, isqrt

__all__ = ["Quadratic"]

# primes = (2, 3, 5, 7)
primes = (2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47, 53, 59, 61, 67, 71, 73, 79, 83, 89, 97, 101, 103, 107, 109, 113, 127, 131, 137, 139, 149, 151, 157, 163, 167, 173, 179, 181, 191, 193, 197, 199, 211, 223, 227, 229, 233, 239, 241, 251)

def exp2(n):
    return {1: 0, 3: 1, 7: 2, 15: 3}[n ^ (n - 1)]

_PyHASH_MODULUS = sys.hash_info.modulus

mpz_type = type(mpz())
mpq_type = type(Fraction())

class Quadratic(numbers.Real):
    __slots__ = ("rational_part", "quadratic_power", "quadratic_part")

    def __new__(cls, rational_part = Fraction(), quadratic_power = 0, quadratic_part = None):
        self = super(Quadratic, cls).__new__(cls)
        if type(rational_part) is str:
            rational_part = Fraction(rational_part)
        if isinstance(rational_part, (int, mpz_type, mpq_type)):
            self.rational_part = Fraction(rational_part)
            self.quadratic_power = quadratic_power
            self.quadratic_part = quadratic_part
            return self
        elif isinstance(rational_part, Quadratic):
            return rational_part
        else:
            raise NotImplementedError

    def __str__(self):
        if self.quadratic_part:
            q = reduce(operator.mul, map(operator.pow, primes, self.quadratic_part))
            quadratic_part_string = "s" * self.quadratic_power + "qrt(" + str(q) + ")"
            if self.rational_part == 1:
                return quadratic_part_string
            elif self.rational_part == -1:
                return "-" + quadratic_part_string
            else:
                return str(self.rational_part) + "*" + quadratic_part_string
        else:
            return str(self.rational_part)

    __repr__ = __str__

    def _operator_fallbacks(monomorphic_operator, fallback_operator):
        def forward(a, b):
            if isinstance(b, (int, mpz_type, mpq_type, Quadratic)):
                return monomorphic_operator(a, Quadratic(b))
            else:
                return NotImplemented

        def reverse(b, a):
            if isinstance(a, (int, mpz_type, mpq_type, Quadratic)):
                return monomorphic_operator(a, Quadratic(b))
            else:
                return NotImplemented

        return forward, reverse

    def _add(x, y):
        if x.quadratic_power == y.quadratic_power and x.quadratic_part == y.quadratic_part:
            if x.rational_part + y.rational_part == 0:
                return Quadratic()
            else:
                return Quadratic(x.rational_part + y.rational_part, x.quadratic_power, x.quadratic_part)

    __add__, __radd__ = _operator_fallbacks(_add, operator.add)

    def _sub(x, y):
        if x.quadratic_power == y.quadratic_power and x.quadratic_part == y.quadratic_part:
            if x.rational_part == y.rational_part:
                return Quadratic()
            else:
                return Quadratic(x.rational_part - y.rational_part, x.quadratic_power, x.quadratic_part)

    __sub__, __rsub__ = _operator_fallbacks(_sub, operator.sub)

    def _mul(x, y):
        r = x.rational_part * y.rational_part
        if x.quadratic_power == 0:
            return Quadratic(r, y.quadratic_power, y.quadratic_part)
        if y.quadratic_power == 0:
            return Quadratic(r, x.quadratic_power, x.quadratic_part)

        quadratic_power = max(x.quadratic_power, y.quadratic_power)
        exp_quadratic_power = 1 << quadratic_power
        shifts = quadratic_power - x.quadratic_power, quadratic_power - y.quadratic_power
        prime_power_list = []
        mask = 0
        for prime, x_power, y_power in zip(primes, x.quadratic_part, y.quadratic_part):
            power = (x_power << shifts[0]) + (y_power << shifts[1])
            if power >= exp_quadratic_power:
                r *= prime
                power ^= exp_quadratic_power
            prime_power_list.append(power)
            mask |= power
        if mask == 0:
            return Quadratic(r)
        mask_shift = exp2(mask)
        return Quadratic(
            r,
            quadratic_power - mask_shift,
            tuple(n >> mask_shift for n in prime_power_list)
        )

    __mul__, __rmul__ = _operator_fallbacks(_mul, operator.mul)

    def _div(x, y):
        r = x.rational_part / y.rational_part
        if y.quadratic_power == 0:
            return Quadratic(r, x.quadratic_power, x.quadratic_part)

        quadratic_power = max(x.quadratic_power, y.quadratic_power)
        exp_quadratic_power = 1 << quadratic_power
        shifts = quadratic_power - x.quadratic_power, quadratic_power - y.quadratic_power
        prime_power_list = []
        mask = 0
        for prime, x_power, y_power in zip(
            primes,
            x.quadratic_part or (0,) * len(primes),
            y.quadratic_part
        ):
            power = (x_power << shifts[0]) - (y_power << shifts[1])
            if power < 0:
                r /= prime
                power += exp_quadratic_power
            prime_power_list.append(power)
            mask |= power
        if mask == 0:
            return Quadratic(r)
        mask_shift = exp2(mask)
        return Quadratic(
            r,
            quadratic_power - mask_shift,
            tuple(n >> mask_shift for n in prime_power_list)
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

    @staticmethod
    def square(x):
        r = x.rational_part ** 2
        p = x.quadratic_power
        if p == 0:
            return Quadratic(r)
        elif p == 1:
            for prime, power in zip(primes, x.quadratic_part):
                if power:
                    r *= prime
            return Quadratic(r)
        power_mask = 1 << (p - 1)
        prime_power_list = []
        for prime, power in zip(primes, x.quadratic_part):
            if power >= power_mask:
                r *= prime
                prime_power_list.append(power ^ power_mask)
            else:
                prime_power_list.append(power)
        return Quadratic(r, p - 1, tuple(prime_power_list))

    @staticmethod
    def inverse(x):
        r = x.rational_part ** -1
        q = x.quadratic_part
        if x.quadratic_power == 0:
            return Quadratic(r)
        prime_base = 1
        prime_power_list = []
        for prime, power in zip(primes, q):
            if power:
                r /= prime
                prime_power_list.append((1 << x.quadratic_power) - power)
            else:
                prime_power_list.append(0)
        return Quadratic(r, x.quadratic_power, tuple(prime_power_list))

    def __pow__(x, y):
        power = None
        inverse = False
        if isinstance(y, (int, mpz_type)):
            power = int(abs(y))
            inverse = y < 0
        elif y.quadratic_power == 0 and y.rational_part.denominator == 1:
            power = int(abs(y.rational_part.numerator))
            inverse = y.rational_part.numerator < 0
        else:
            raise NotImplementedError

        if power == 0:
            return Quadratic(1)
        r = x.rational_part ** power
        quadratic_power = x.quadratic_power
        if quadratic_power == 0:
            return Quadratic(r ** -1) if inverse else Quadratic(r)
        while quadratic_power and power & 1 == 0:
            quadratic_power -= 1
            power >>= 1
        exp_quadratic_power_m1 = (1 << quadratic_power) - 1
        prime_power_list = []
        for prime, x_power in zip(primes, x.quadratic_part):
            p = x_power * power
            r *= prime ** (p >> quadratic_power)
            prime_power_list.append(p & exp_quadratic_power_m1)
        result = None
        if quadratic_power == 0:
            result = Quadratic(r)
        else:
            result = Quadratic(r, quadratic_power, tuple(prime_power_list))
        return Quadratic.inverse(result) if inverse else result

    def __rpow__(x, y):
        raise NotImplementedError

    @staticmethod
    def sqrt(x):
        p = x.rational_part
        s, t = p.numerator, p.denominator
        if p == 0:
            return Quadratic()
        elif p < 0:
            raise NotImplementedError
        elif x.quadratic_power == 0:
            if is_square(s) and is_square(t):
                return Quadratic(Fraction(isqrt(s), isqrt(t)))

        r = Fraction(1, t)
        p = s * t
        prime_power_list = []
        for prime, x_power in zip(primes, x.quadratic_part or (0,) * len(primes)):
            power = 0
            while p % prime == 0:
                p //= prime
                power += 1
            r *= prime ** (power >> 1)
            prime_power_list.append(((power & 1) << x.quadratic_power) | x_power)
        if not is_square(p):
            return
        return Quadratic(r * isqrt(p), x.quadratic_power + 1, tuple(prime_power_list))

    def __pos__(x):
        return Quadratic(x.rational_part, x.quadratic_power, x.quadratic_part)

    def __neg__(x):
        return Quadratic(-x.rational_part, x.quadratic_power, x.quadratic_part)

    def __abs__(x):
        return Quadratic(abs(x.rational_part), x.quadratic_power, x.quadratic_part)

    def __int__(x):
        if x.quadratic_power == 0 and x.rational_part.denominator == 1:
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
        if self.quadratic_power == 0:
            return hash(self.rational_part)
        else:
            return hash(self.rational_part) * hash(self.quadratic_power) * hash(self.quadratic_part) % _PyHASH_MODULUS

    def __eq__(x, y):
        if isinstance(y, (int, mpz_type, mpq_type)):
            return x.quadratic_power == 0 and x.rational_part == y
        elif isinstance(y, Quadratic):
            return x.rational_part == y.rational_part and x.quadratic_power == y.quadratic_power and x.quadratic_part == y.quadratic_part
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
        return x.rational_part != 0

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
