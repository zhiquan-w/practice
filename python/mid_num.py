def findMedianSortedArrays(nums1, nums2) -> float:
    '''
        1. nums1 和 nums2 的集合的排序问题
        '''
    sarray = []
    len1 = len(nums1)
    len2 = len(nums2)
    st1 = st2 = 0
    for i in range(len1 + len2):
        if st1 < len1 and st2 < len2:
            if nums1[st1] < nums2[st2]:
                sarray.append(nums1[st1])
                st1 += 1
            else:
                sarray.append(nums2[st2])
                st2 += 1
        elif st1 >= len1:
            sarray += nums2[st2:]
            break
        elif st2 >= len2:
            sarray += nums1[st1:]
            break

    if (len1+len2) % 2 == 0:
        return (sarray[(len2+len1)//2] + sarray[(len2+len1)//2 - 1]) / 2
    else:
        return sarray[(len2+len1)//2]

a = [3,1,5]
b = [2,6,4]
c = findMedianSortedArrays(a, b)
print(c)
