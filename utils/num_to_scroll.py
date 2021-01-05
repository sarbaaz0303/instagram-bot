'''use to find number of scroll it needs to collect n data
    num: number of posts
    start: first set of post that becomes visible on page loads
    per_scroll: difference in new data per scroll'''
def num_to_scroll(num: int, start: int, per_scroll: int) -> int:
    if num <= start:
        return 1
    return (1 + num_to_scroll((num - per_scroll), start, per_scroll))

# print(num_to_scroll(58,24,12))