"""
"""


tsequence = tuple([t / 20.0 for t in range(21)])
beziers = {}


def pascal_row(n):
    """Returns n-th row of Pascal's triangle"""
    result = [1]
    x, numerator = 1, n
    for denominator in range(1, n // 2 + 1):
        x *= numerator
        x /= denominator
        result.append(x)
        numerator -= 1
    if n & 1 == 0:
        result.extend(reversed(result[:-1]))
    else:
        result.extend(reversed(result))
    return result


def make_bezier(n):
    """Bezier curves:
    http://en.wikipedia.org/wiki/B%C3%A9zier_curve#Generalization
    """
    try:
        return beziers[n]
    except KeyError:
        combinations = pascal_row(n - 1)
        result = []
        for t in tsequence:
            tpowers = (t ** i for i in range(n))
            upowers = ((1 - t) ** i for i in range(n - 1, -1, -1))
            coefs = [
                c * a * b for c, a, b in zip(combinations, tpowers, upowers)
            ]
            result.append(coefs)
        beziers[n] = result
        return result
