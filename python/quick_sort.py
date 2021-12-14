def swap(arr, left, right):
    tmp = arr[left]
    arr[left] = arr[right]
    arr[right] = tmp


def partition(arr, leftBound, rightBound):
    prvot = arr[rightBound]
    left = leftBound
    right = rightBound
    while left < right:
        while left < right and arr[left] <= prvot:
            left += 1
        while left < right and arr[right] >= prvot:
            right -= 1
        if left < right:
            swap(arr, left, right)
    swap(arr, left, rightBound)
    return left


def quickSort(arr, leftBound, rightBound):
    if leftBound >= rightBound:
        return
    mid = partition(arr, leftBound, rightBound)
    quickSort(arr, leftBound, mid - 1)
    quickSort(arr, mid + 1, rightBound)


if __name__ == "__main__":
    a = [8, 3, 2, 7, 5, 9, 4, 6]
    quickSort(a, 0, len(a) - 1)
    print(a)
