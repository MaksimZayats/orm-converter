def dict_intersection(*dicts: dict) -> dict:
    comm_keys = dicts[0].keys()

    for _dict in dicts[1:]:
        comm_keys &= _dict.keys()  # type: ignore

    return {key: dicts[0][key] for key in comm_keys}
