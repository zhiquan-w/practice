def lengthOfLongestSubstring(s: str) -> int:
    left = 0
    res = 0
    if len(s) > 0:
        if len(s) == 1:
            res = 1
        else:
            for right in range(0, len(s), 1):
                from IPython import embed;embed()
                if right - left > res:
                    res = right - left
                if s[right] in s[left:right]:
                    left = right
    return res

s = " "
print(lengthOfLongestSubstring(s))