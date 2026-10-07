"""Final current-doc publication; retain the preceding bank-only QA receipt."""
import json, re
from pathlib import Path
import publish_voice_serial as original


def main():
    root = original.ROOT
    prior = root/'evidence/voice_serial_release01.json'
    p = json.loads(prior.read_text(encoding='utf8'))
    bankp, bank = original.final_bank()
    if not p['passed'] or p['bank_sha256'] != original.sha(bankp):
        raise ValueError('preceding immutable bank publication required')
    for n, h in p['source_sha256'].items():
        if n not in original.DOCS and original.sha(root/n) != h:
            raise ValueError('bank-only publication input changed: '+n)
    if (bank['long_note_admitted_locally'] or len(bank['records']) != 4
            or sum(r['trajectory_complete'] for r in bank['records'].values()) != 1
            or any(c['measured'] for c in bank['comparisons'].values())):
        raise ValueError('current document covers the one-complete rejected campaign')
    original.OUTPUT = root/'evidence/voice_serial_release02.json'
    doc = root/'docs/VOZ_SERIAL_CAMPANA_RESULTADOS.md'
    text = doc.read_text(encoding='utf8')
    if 'Banco largo rechazado' not in text or 'una de cuatro' not in text:
        raise ValueError('current outcome scope missing')
    for link in re.findall(r'\]\(([^)]+)\)', text):
        if link.startswith(('https:', 'http:', '#')):
            continue
        target = (doc.parent/link.split('#')[0]).resolve()
        if not target.exists() and target != original.OUTPUT.resolve():
            raise ValueError('current campaign link missing: '+link)
    original.release()


if __name__ == '__main__':
    main()
