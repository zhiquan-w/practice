def fabnacci(max):
    n, a, b = 0, 0, 1
    while n < max:
        yield b
        a, b = b, a + b 
        n = n + 1

for i in fabnacci(5):
    print(i)