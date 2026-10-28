"""Encrypt the distribution dataset with the same password as the plan.

Usage: python3 tools/encrypt_dist.py /path/to/dist.json [app_dir]

The password is typed in the terminal (never stored). It is first checked against
data/plan.enc.json, so the app can unlock both files with the one password.
The plaintext dist.json must stay outside the repository.
"""
import base64, getpass, json, os, sys
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

ITER = 250000


def key(password, salt, iterations):
    return PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=iterations).derive(password.encode())


def main():
    src = sys.argv[1]
    app = sys.argv[2] if len(sys.argv) > 2 else os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
    plan = json.load(open(os.path.join(app, 'data', 'plan.enc.json')))
    password = os.environ.get('CC_PASS') or getpass.getpass('Senha do roteiro: ')
    try:
        b = base64.b64decode
        visits = json.loads(AESGCM(key(password, b(plan['salt']), plan['iter'])).decrypt(b(plan['iv']), b(plan['ct']), None))['visits']
    except Exception:
        sys.exit('Senha incorreta: ela precisa ser a mesma do roteiro (data/plan.enc.json). Nada foi gravado.')
    data = json.load(open(src))
    salt, iv = os.urandom(16), os.urandom(12)
    ct = AESGCM(key(password, salt, ITER)).encrypt(iv, json.dumps(data, ensure_ascii=False).encode(), None)
    e = lambda x: base64.b64encode(x).decode()
    out = os.path.join(app, 'data', 'dist.enc.json')
    json.dump({'v': 1, 'iter': ITER, 'salt': e(salt), 'iv': e(iv), 'ct': e(ct)}, open(out, 'w'))
    planned = {str(v.get('catId')): v for v in visits if v.get('catId')}
    print(f'OK: {out} gravado ({len(data["companies"])} empresas, {len(data["materials"])} matérias-primas).')
    for c in sorted(data['companies'], key=lambda c: c['order']):
        v = planned.get(c['cat'])
        print(f"  {c['cat']}  {'JÁ NO ROTEIRO ' + str(v.get('day')) + ' · ' + str(v.get('name')) if v else 'nova (vai para 13/11)'}")


if __name__ == '__main__':
    main()
