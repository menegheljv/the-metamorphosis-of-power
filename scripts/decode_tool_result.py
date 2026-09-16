import json, re, base64, sys

def decode(tool_result_path, out_path):
    with open(tool_result_path, encoding='utf-8') as f:
        data = json.load(f)
    raw = data[0]['text']
    raw2 = re.sub(r'\n\n\(captured at origin.*\)\s*$', '', raw, flags=re.S)
    b64 = json.loads(raw2)
    raw_bytes = base64.b64decode(b64)
    decoded = raw_bytes.decode('utf-8')
    with open(out_path, 'w', encoding='utf-8') as out:
        out.write(decoded)
    lines = decoded.splitlines()
    print(f"saved {out_path}: {len(decoded)} chars, {len(lines)} lines")

if __name__ == '__main__':
    decode(sys.argv[1], sys.argv[2])
