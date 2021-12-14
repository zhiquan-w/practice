import numpy as np

a = np.random.random([5, 3])
if a.shape[0] % 2 == 0:
    b = a.copy()
    b[0::2, :] = a[1::2, :]
    b[1::2, :] = a[0::2, :]
else:
    temp = a[0:-1, :]
    b = temp.copy()
    b[0::2, :] = temp[1::2, :]
    b[1::2, :] = temp[0::2, :]

print(a)
print(b)
