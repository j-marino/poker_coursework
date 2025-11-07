def powerRecursive(num, power):
    if power == 0:
        return 1
    return powerRecursive(num, power - 1) * num

# print(powerRecursive(2, 3))

def powerIterative(num, power):
    total = 1
    while power != 0:
        total *= num
        power -= 1
    return total

# print(powerIterative(2, 4))

def factorial(n):
    if n == 0:
        return 1
    else:
        return factorial(n - 1) * n

def factorialIterative(n):
    total = 1
    while n != 0: # negation
        total *= n
        n -= 1
    return total

# print(factorialIterative(4))

def GCDRECUR(a, b):
    if a == 0: return b
    if b == 0: return a
    else:
        r = a % b
        return GCDRECUR(b, r)

def GCD(a, b):
    while a != 0 and b != 0:
        r = a % b
        a = b
        b = r
    if a == 0:
        return b
    if b == 0:
        return 

# print(GCD(30 ,3))

def sumDigr(n):
    if n < 10:
        return n
    else:
        return n % 10 + sumDigr(n // 10)

def sumDig(n):
    total = 0
    while n >= 10: # negation
        total += n % 10
        n //= 10
    return total + n

# print(sumDig(56))

def mf(a, b, c):
    if b == len(a):
        return c
    elif a[b] > c:
        return mf(a, b+1, a[b])
    else:
        return mf(a, b+1, c)
    
def mf_it(a, b, c):
    while b != len(a):
        if a[b] > c:
            c = a[b]
        b += 1
    return c
    
print(mf([5, 4, 3, 2, 1], 0, 0))
print(mf_it([5, 4, 3, 2, 1], 0, 0))