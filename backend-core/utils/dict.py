def rename_key(data: dict, old_key, new_key) -> dict:
    assert type(data) is dict
    if old_key in data.keys():
        data[new_key] = data.pop(old_key)
    return data
