# attack_keys.json 저장(한 키 = 한 줄로 짧게)
import json
def dumps(o, ind=0):
    sp = ' ' * ind
    if isinstance(o, dict):
        if all(not isinstance(v, (dict,)) and (not isinstance(v, list) or all(not isinstance(x, (list, dict)) for x in v)) for v in o.values()) and len(json.dumps(o, ensure_ascii=False)) < 110:
            return json.dumps(o, ensure_ascii=False)
        items = [f'{sp} {json.dumps(k, ensure_ascii=False)}: {dumps(v, ind + 1)}' for k, v in o.items()]
        return '{\n' + ',\n'.join(items) + '\n' + sp + '}'
    if isinstance(o, list) and o and all(isinstance(x, list) for x in o):
        s = json.dumps(o, ensure_ascii=False)
        if len(s) < 160: return s
        return '[' + (',\n' + sp + ' ').join(json.dumps(x, ensure_ascii=False) for x in o) + ']'
    return json.dumps(o, ensure_ascii=False)
def save(A, p='attack_keys.json'): open(p, 'w', encoding='utf-8').write(dumps(A) + '\n')
