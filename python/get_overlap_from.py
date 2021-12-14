def _get_st_end(t_chunk, ocm_chunks):
    offset = t_chunk[0]
    t_st = 0
    t_end = 0
    for st, size in ocm_chunks:
        offset -= size
        if offset <= 0:
            t_st = st + size - abs(offset)
            break
    offset_end = sum(t_chunk)
    for st, size in ocm_chunks:
        offset_end -= size
        if offset_end <= 0:
            t_end = st + size - abs(offset_end)
            break
    return (t_st, t_end)


t_chunk = (10, 200)
chunks = [(100, 120), (230, 100)]
print(_get_st_end(t_chunk, chunks))
