import ast
from fractions import Fraction


def parse_subgroup(subgroup_str):
    try:
        return set(ast.literal_eval(str(subgroup_str)))
    except Exception:
        return set()


def parse_fraction(s):
    try:
        return float(Fraction(str(s).strip()))
    except Exception:
        return float(s)


def parse_coefficients(coeffs):
    if isinstance(coeffs, list):
        return coeffs
    if isinstance(coeffs, str) and coeffs.strip() not in ('', 'nan'):
        try:
            return ast.literal_eval(coeffs.strip())
        except Exception:
            pass
    return None


def eval_polynomial(coeffs, intercept_str, x):
    """Évalue: intercept + c[0]*x + c[1]*x² + c[2]*x³ ..."""
    try:
        result = parse_fraction(intercept_str)
        for i, c in enumerate(coeffs):
            result += parse_fraction(c) * (x ** (i + 1))
        return result
    except Exception:
        return None
