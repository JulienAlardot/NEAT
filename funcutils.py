class ChainListNode:
    def __init__(self, value, head, tail):
        self.value = value
        self.head = head
        self.tail = tail


class LinkedList:
    def __init__(self, *args):
        self._size = len(args)
        args = args
        previous = ChainListNode(args[0], StopIteration, StopIteration)
        self.head = previous
        self._now = self.head
        self.tail = None
        for i in range(1, self._size):
            now = ChainListNode(args[i], previous, StopIteration)
            previous.tail = now
            previous = now
            self.tail = now

    def __len__(self):
        return self._size

    def __repr__(self):
        x = 'LinkedList['
        tail = self.head
        while tail is not StopIteration:
            x += " " + str(tail.value)
            tail = tail.tail
            if tail is not StopIteration:
                x += ','
        x += " ]"

        return x

    def __getitem__(self, item):
        indices = list()
        reversed = False
        if isinstance(item, int):
            indices = [item]
        elif isinstance(item, slice):
            step = item.step if item.step else 1
            if step >= 1:
                indices = list(range(item.start if item.start else 0,
                                     item.stop if item.stop else self._size,
                                     step))
            else:
                indices = list(range(item.stop - 1 if item.stop else self._size - 1,
                                     item.start - 1 if item.start else -1,
                                     step))[::-1]
                reversed = True
        elif isinstance(item, (list, tuple, set)):
            indices = list(item)
        else:
            raise TypeError("Indices must be either of type int or a slice or iterable")

        values = list()
        pos = 0
        now = self.head
        while indices:
            element = indices.pop(0)
            element = self._size - element if element < 0 else element
            value = None
            while pos <= element:
                value = now.value
                if now == StopIteration:
                    raise StopIteration
                now = now.tail
                pos += 1

            values.append(value)
        if len(values) == 1:
            return values[0]
        else:
            step = -1 if reversed else 1
            return LinkedList(*values[::step])

    def __delitem__(self, item):
        indices = list()
        if isinstance(item, int):
            indices = [item]
        elif isinstance(item, (tuple, list, set)):
            indices = list(item)
        elif isinstance(item, slice):
            step = item.step if item.step else 1
            if step >= 1:
                start = item.start if item.start else 0
                stop = item.stop if item.stop else self._size
            else:
                stop = item.start if item.start else 0
                start = item.stop if item.stop else self._size
            indices = list(range(start, stop, step))
        else:
            raise TypeError("Indices must be either of type int or a slice or iterable")
        indices = [self._size - item - i if item < 0 else item - i for i, item in enumerate(indices)]
        pos = 0
        now = self.head
        while indices:
            item = indices.pop(0)
            while pos <= item:
                if now == StopIteration:
                    raise IndexError("Index is out of bounds")

                if pos == item:
                    previous = now.head
                    tail = now.tail
                    if previous:
                        previous.tail = tail
                    else:
                        self.head = tail
                    if tail != StopIteration:
                        tail.head = previous
                    else:
                        previous.tail = StopIteration
                        self.tail = tail
                    old = now
                    now = now.tail
                    del old
                    self._size -= 1
                    break
                now = now.tail
                pos += 1

    def __iter__(self):
        self._now = self.head
        return self

    def __next__(self):
        while self._now is not StopIteration:
            result = self._now.value
            self._now = self._now.tail
            return result
        else:
            raise StopIteration

    def __reversed__(self):
        l = list(self.__iter__())
        self._now = self.head
        return LinkedList(*l[::-1])

    def __add__(self, other):
        if not hasattr(other, "__iter__"):
            type_1 = str(type(self)).split(".")[-1][:-2]
            type_2 = str(type(other))[6:-1]
            raise TypeError(f"unsupported operand type(s) for +: '{type_1}' and {type_2}")

        l = list(self.__iter__()) + list(other.__iter__())
        self._now = self.head
        return LinkedList(*l)

    def __sub__(self, other):
        if not hasattr(other, "__iter__"):
            type_1 = str(type(self)).split(".")[-1][:-2]
            type_2 = str(type(other))[6:-1]
            raise TypeError(f"unsupported operand type(s) for -: '{type_1}' and {type_2}")
        l = [x for x in self.__iter__() if x not in other.__iter__()]
        self._now = self.head
        return LinkedList(*l)

    def __mul__(self, other):
        if not isinstance(other, int):
            type_2 = str(type(other))[6:-1]
            raise TypeError(f"Can't multiply sequence by non-int of type {type_2}")
        l = list(self.__iter__()) * other
        self._now = self.head
        return LinkedList(*l)

    def __divmod__(self, other):
        type_1 = str(type(self)).split(".")[-1][:-2]
        type_2 = str(type(other))[6:-1]
        raise TypeError(f"unsupported operand type(s) for %: '{type_1}' and {type_2}")

    def __truediv__(self, other):
        type_1 = str(type(self)).split(".")[-1][:-2]
        type_2 = str(type(other))[6:-1]
        raise TypeError(f"unsupported operand type(s) for /: '{type_1}' and {type_2}")

    def __floordiv__(self, other):
        type_1 = str(type(self)).split(".")[-1][:-2]
        type_2 = str(type(other))[6:-1]
        raise TypeError(f"unsupported operand type(s) for //: '{type_1}' and {type_2}")

    def __contains__(self, item):
        it = self.__iter__()
        r = False
        try:
            r = next(it) == item
        except StopIteration:
            pass
        self._now = self.head
        return r

    def __dir__(self):
        return (
            '__add__',
            '__class__',
            '__contains__',
            '__delattr__',
            '__delitem__',
            '__dir__',
            '__doc__',
            '__eq__',
            '__format__',
            '__ge__',
            '__getattribute__',
            '__getitem__',
            '__gt__',
            '__hash__',
            '__iadd__',
            '__isub__',
            '__imul__',
            '__init__',
            '__init_subclass__',
            '__iter__',
            '__le__',
            '__len__',
            '__lt__',
            '__mul__',
            '__ne__',
            '__new__',
            '__reduce__',
            '__reduce_ex__',
            '__repr__',
            '__reversed__',
            '__rmul__',
            '__setattr__',
            '__setitem__',
            '__sizeof__',
            '__str__',
            '__sub__',
            '__subclasshook__',
            'append',
            'clear',
            'copy',
            'count',
            'extend',
            'index',
            'insert',
            'pop',
            'remove',
            'reverse',
            'sort'
        )

    def __copy__(self):
        # TODO
        raise NotImplementedError

    def __deepcopy__(self, memodict={}):
        # TODO
        raise NotImplementedError


if __name__ == "__main__":
    x = LinkedList(4, 5, 6, 7)
    print(x)
    print(iter(x))
    print(reversed(x))
    print(next(x))
    print(next(x))
    print(next(x))
    print(next(x))
    print(len(x))
    print(x + x)
    print(x - [5])
    print(x * 5)
    print(x[1])
    print(x[1:])
    print(list(x))
    print(x[::-1])
    print(x)
    del x[1]
    print(x)
    del x[1:]
    print(x)
    try:
        x + 5
    except TypeError:
        print("Add error catched")
    try:
        x - 5
    except TypeError:
        print("Sub error catched")

    try:
        x * [5]
    except TypeError:
        print("Mult error catched")

    try:
        x * [5]
    except TypeError:
        print("Mult error catched")

    try:
        x / 2
    except TypeError:
        print("Div error catched")

    try:
        x // 2
    except TypeError:
        print("Floor Div error catched")

    try:
        x % 5
    except TypeError:
        print("Modulo error catched")
    print(x)
    print(5 in x)
    print(4 in x)
    print(dir(x))
    print(isinstance(x, LinkedList))
    print(x.__sizeof__())
    x += [5]
    print(x)
