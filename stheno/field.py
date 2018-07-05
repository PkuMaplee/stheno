# -*- coding: utf-8 -*-

from __future__ import absolute_import, division, print_function

from plum import Dispatcher, Referentiable, Self, NotFoundLookupError
from numbers import Number

__all__ = []

dispatch_field = Dispatcher()


def apply_optional_arg(f, arg1, arg2):
    """If `f` takes in two or more arguments, run `f(arg1, arg2)`; otherwise,
    run `f(arg1)`.

    Args:
        f (function): Function to run.
        arg1 (object): First argument for `f`.
        arg2 (object): Optional argument for `f`.

    Returns:
        object: Result of `f(arg1, arg2)` or `f(arg1)`.
    """
    try:
        return f(arg1, arg2)
    except TypeError:
        return f(arg1)
    except NotFoundLookupError:
        return f(arg1)


def squeeze(xs):
    """Squeeze an sequence if it only contains a single element.

    Args:
        xs (sequence): Sequence to squeeze.

    Returns:
        object: `xs[0]` if `xs` consists of a single element and `xs` otherwise.
    """
    return xs[0] if len(xs) == 1 else xs


def get_subclasses(c):
    """Get all subclasses of a class.

    Args:
        c (type): Class to get subclasses of.

    Returns:
        list[type]: List of subclasses of `c`.
    """
    return c.__subclasses__() + \
           [x for sc in c.__subclasses__() for x in get_subclasses(sc)]


def broadcast(op, xs, ys):
    """Perform a binary operation `op` on elements of `xs` and `ys`. If `xs` or
    `ys` has length 1, then it is repeated sufficiently many times to match the
    length of the other.

    Args:
        op (function): Binary operation.
        xs (sequence): First sequence.
        ys (sequence): Second sequence.

    Returns:
        tuple: Result of applying `op` to every element of `zip(xs, ys)` after
        broadcasting appropriately.
    """
    if len(xs) == 1 and len(ys) > 1:
        # Broadcast `xs`.
        xs = xs * len(ys)
    elif len(ys) == 1 and len(xs) > 1:
        # Broadcast `ys.
        ys = ys * len(xs)

    # Check that `xs` and `ys` are compatible now.
    if len(xs) != len(ys):
        raise ValueError('Inputs "{}" and "{}" could not be broadcasted.'
                         ''.format(xs, ys))
    # Perform operation.
    return tuple(op(x, y) for x, y in zip(xs, ys))


class Element(Referentiable):
    """A field over functions.

    Functions are also referred to as elements of the field. Elements can be
    added and multiplied.
    """

    dispatch_field = Dispatcher(in_class=Self)

    def __eq__(self, other):
        return equal(self, other)

    def __mul__(self, other):
        return mul(self, other)

    def __rmul__(self, other):
        return mul(other, self)

    def __add__(self, other):
        return add(self, other)

    def __radd__(self, other):
        return add(other, self)

    def __neg__(self):
        return mul(-1, self)

    def __sub__(self, other):
        return add(self, -other)

    def __rsub__(self, other):
        return add(other, -self)

    @property
    def num_terms(self):
        """Number of terms"""
        return 1

    def term(self, i):
        """Get a specific term.

        Args:
            i (int): Index of term.

        Returns:
            :class:`.field.Element`: The referenced term.
        """
        if i == 0:
            return self
        else:
            raise IndexError('Index out of range.')

    @property
    def num_factors(self):
        """Number of factors"""
        return 1

    def factor(self, i):
        """Get a specific factor.

        Args:
            i (int): Index of factor.

        Returns:
            :class:`.field.Element`: The referenced factor.
        """
        if i == 0:
            return self
        else:
            raise IndexError('Index out of range.')

    def __repr__(self):
        return str(self)

    @property
    def __name__(self):
        return self.__class__.__name__

    def __str__(self):
        return self.__class__.__name__ + '()'


class PrimitiveElement(Element):
    """A primitive.

    Instances of primitives should always be the same element. It therefore
    does not make sense if primitive elements have external parameters.
    """


class OneElement(PrimitiveElement):
    """The constant `1`."""

    def __str__(self):
        return '1'


class ZeroElement(PrimitiveElement):
    """The constant `0`."""

    def __str__(self):
        return '0'


class WrappedElement(Element):
    """A wrapped element.

    Args:
        e (:class:`.field.Element`): Element to wrap.
    """

    def __init__(self, e):
        self.e = e

    def __getitem__(self, item):
        if item == 0:
            return self.e
        else:
            raise IndexError('Index out of range.')

    def display(self, e):
        raise NotImplementedError()

    def __str__(self):
        return pretty_print(self)


class JoinElement(Element):
    """Two wrapped elements.

    Args:
        e1 (:class:`.field.Element`): First element to wrap.
        e2 (:class:`.field.Element`): Second element to wrap.
    """

    def __init__(self, e1, e2):
        self.e1 = e1
        self.e2 = e2

    def __getitem__(self, item):
        if item == 0:
            return self.e1
        elif item == 1:
            return self.e2
        else:
            raise IndexError('Index out of range.')

    def display(self, e1, e2):
        raise NotImplementedError()

    def __str__(self):
        return pretty_print(self)


class ScaledElement(WrappedElement):
    """Scaled element.

    Args:
        e (:class:`.field.Element`): Element to scale.
        scale (tensor): Scale.
    """

    def __init__(self, e, scale):
        WrappedElement.__init__(self, e)
        self.scale = scale

    @property
    def num_factors(self):
        return self[0].num_factors + 1

    def display(self, e):
        return '{} * {}'.format(self.scale, e)

    def factor(self, i):
        if i >= self.num_factors:
            raise IndexError('Index out of range.')
        else:
            return self.scale if i == 0 else self[0].factor(i - 1)


class ProductElement(JoinElement):
    """Product of elements."""

    @property
    def num_factors(self):
        return self[0].num_factors + self[1].num_factors

    def factor(self, i):
        if i >= self.num_factors:
            raise IndexError('Index out of range.')
        if i < self[0].num_factors:
            return self[0].factor(i)
        else:
            return self[1].factor(i - self[0].num_factors)

    def display(self, e1, e2):
        return '{} * {}'.format(e1, e2)


class SumElement(JoinElement):
    """Sum of elements."""

    @property
    def num_terms(self):
        return self[0].num_terms + self[1].num_terms

    def term(self, i):
        if i >= self.num_terms:
            raise IndexError('Index out of range.')
        if i < self[0].num_terms:
            return self[0].term(i)
        else:
            return self[1].term(i - self[0].num_terms)

    def display(self, e1, e2):
        return '{} + {}'.format(e1, e2)


@dispatch_field(object, object)
def mul(a, b):
    """Multiply two elements.

    Args:
        a (:class:`.field.Element`): First element in product.
        b (:class:`.field.Element`): Second element in product.

    Returns:
        :class:`.field.Element`: Product of the elements.
    """
    raise NotImplementedError('Multiplication not implemented for {} and {}.'
                              ''.format(type(a).__name__, type(b).__name__))


@dispatch_field(object, object)
def add(a, b):
    """Add two elements.

    Args:
        a (:class:`.field.Element`): First element in summation.
        b (:class:`.field.Element`): Second element in summation.

    Returns:
        :class:`.field.Element`: Sum of the elements.
    """
    raise NotImplementedError('Addition not implemented for {} and {}.'
                              ''.format(type(a).__name__, type(b).__name__))


@dispatch_field(object)
def get_field(a):
    """Get the field of an element.

    Args:
        a (:class:`.field.Element`): Element to get field of.

    Returns:
        type: Field of `a`.
    """
    raise RuntimeError('Could not determine field type of {}.'
                       ''.format(type(a).__name__))


new_cache = {}


def new(a, t):
    """Create a new specialised type.

    Args:
        a (:class:`.field.Element`): Element to create new type for.
        t (type): Type to create.

    Returns:
        type: Specialisation of `t` appropriate for `a`.
    """
    try:
        return new_cache[type(a), t]
    except KeyError:
        field = get_field(a)
        candidates = list(set(get_subclasses(field)) & set(get_subclasses(t)))

        # There should only be a single candidate.
        if len(candidates) != 1:
            raise RuntimeError('Could not determine {} for field {}.'
                               ''.format(t.__name__, field.__name__))

        new_cache[type(a), t] = candidates[0]
        return new_cache[type(a), t]


# Pretty printing with minimal parentheses.

@dispatch_field(Element)
def pretty_print(el):
    """Pretty print an element with a minimal number of parentheses.

    Args:
        el (:class:`.field.Element`): Element to print.

    Returns:
        str: `el` converted to string prettily.
    """
    return str(el)


@dispatch_field(WrappedElement)
def pretty_print(el):
    return el.display(pretty_print(el[0], el))


@dispatch_field(JoinElement)
def pretty_print(el):
    return el.display(pretty_print(el[0], el), pretty_print(el[1], el))


@dispatch_field(object, object)
def pretty_print(el, parent):
    if need_parens(el, parent):
        return '(' + pretty_print(el) + ')'
    else:
        return pretty_print(el)


@dispatch_field(Element, SumElement)
def need_parens(el, parent):
    """Check whether `el` needs parentheses when printed in `parent`.

    Args:
        el (:class:`.field.Element`): Element to print.
        parent (:class:`.field.Element`): Parent of element to print.

    Returns:
        bool: Boolean whether `el` needs parentheses.
    """
    return False


@dispatch_field(Element, ProductElement)
def need_parens(el, parent): return False


@dispatch_field({SumElement, WrappedElement}, ProductElement)
def need_parens(el, parent): return True


@dispatch_field(ScaledElement, ProductElement)
def need_parens(el, parent): return False


@dispatch_field(Element, WrappedElement)
def need_parens(el, parent): return False


@dispatch_field({WrappedElement, JoinElement}, WrappedElement)
def need_parens(el, parent): return True


@dispatch_field({ProductElement, ScaledElement}, ScaledElement)
def need_parens(el, parent): return False


# Generic multiplication.

@dispatch_field(Element, object)
def mul(a, b):
    if isinstance(b, Number) and b == 0:
        return new(a, ZeroElement)()
    elif isinstance(b, Number) and b == 1:
        return a
    else:
        return new(a, ScaledElement)(a, b)


@dispatch_field(object, Element)
def mul(a, b):
    if isinstance(a, Number) and a == 0:
        return new(b, ZeroElement)()
    elif isinstance(a, Number) and a == 1:
        return b
    else:
        return new(b, ScaledElement)(b, a)


@dispatch_field(Element, Element)
def mul(a, b): return new(a, ProductElement)(a, b)


# Generic addition.

@dispatch_field(Element, object)
def add(a, b):
    if isinstance(b, Number) and b == 0:
        return a
    else:
        return new(a, SumElement)(a, mul(b, new(a, OneElement)()))


@dispatch_field(object, Element)
def add(a, b):
    if isinstance(a, Number) and a == 0:
        return b
    else:
        return new(b, SumElement)(mul(a, new(b, OneElement)()), b)


@dispatch_field(Element, Element)
def add(a, b):
    if a == b:
        return mul(2, a)
    else:
        return new(a, SumElement)(a, b)


# Cancel redundant zeros and ones.

@dispatch_field.multi((ZeroElement, object), (Element, OneElement),
                      precedence=2)
def mul(a, b): return a


@dispatch_field.multi((object, ZeroElement), (OneElement, Element),
                      precedence=2)
def mul(a, b): return b


@dispatch_field.multi((ZeroElement, ZeroElement), (OneElement, OneElement),
                      precedence=2)
def mul(a, b): return a


@dispatch_field(Element, ZeroElement, precedence=2)
def add(a, b): return a


@dispatch_field(ZeroElement, Element, precedence=2)
def add(a, b): return b


@dispatch_field(ZeroElement, ZeroElement, precedence=2)
def add(a, b): return a


@dispatch_field(ZeroElement, object)
def add(a, b):
    if isinstance(b, Number) and b == 0:
        return a
    elif isinstance(b, Number) and b == 1:
        return new(a, OneElement)()
    else:
        return new(a, ScaledElement)(new(a, OneElement)(), b)


@dispatch_field(object, ZeroElement)
def add(a, b):
    if isinstance(a, Number) and a == 0:
        return b
    elif isinstance(a, Number) and a == 1:
        return new(b, OneElement)()
    else:
        return new(b, ScaledElement)(new(b, OneElement)(), a)


# Group factors and terms if possible.

@dispatch_field(object, ScaledElement)
def mul(a, b): return mul(b.scale * a, b[0])


@dispatch_field(ScaledElement, object)
def mul(a, b): return mul(a.scale * b, a[0])


@dispatch_field(ScaledElement, Element)
def mul(a, b): return mul(a.scale, mul(a[0], b))


@dispatch_field(Element, ScaledElement)
def mul(a, b): return mul(b.scale, mul(a, b[0]))


@dispatch_field(ScaledElement, ScaledElement)
def mul(a, b):
    if a[0] == b[0]:
        return new(a, ScaledElement)(a[0], a.scale * b.scale)
    else:
        scaled = new(a, ScaledElement)(a[0], a.scale * b.scale)
        return new(a, ProductElement)(scaled, b[0])


@dispatch_field(ScaledElement, Element)
def add(a, b):
    if a[0] == b:
        return mul(a.scale + 1, b)
    else:
        return new(a, SumElement)(a, b)


@dispatch_field(Element, ScaledElement)
def add(a, b):
    if a == b[0]:
        return mul(b.scale + 1, a)
    else:
        return new(a, SumElement)(a, b)


@dispatch_field(ScaledElement, ScaledElement)
def add(a, b):
    if a[0] == b[0]:
        return mul(a.scale + b.scale, a[0])
    else:
        return new(a, SumElement)(a, b)


# Equality:

@dispatch_field(object, object)
def equal(a, b): return False


@dispatch_field(PrimitiveElement, PrimitiveElement)
def equal(a, b): return type(a) == type(b)


@dispatch_field.multi((SumElement, SumElement),
                      (ProductElement, ProductElement))
def equal(a, b): return (equal(a[0], b[0]) and equal(a[1], b[1])) or \
                        (equal(a[0], b[1]) and equal(a[1], b[0]))
