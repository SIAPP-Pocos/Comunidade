"""
Diz a etiqueta da próxima versão da base, no formato vAAAA.MM.N (N começa em 0 a cada mês),
a partir das etiquetas que já existem (uma por linha na entrada padrão).

Uso:  git tag -l 'v*' | python ferramentas/proxima_versao.py [AAAA.MM]
"""
from __future__ import annotations

import re
import sys
from datetime import datetime, timezone


def proxima(etiquetas: list[str], mes: str) -> str:
    n = [int(m.group(1)) for e in etiquetas if (m := re.fullmatch(rf"v{re.escape(mes)}\.(\d+)", e.strip()))]
    return f"v{mes}.{max(n) + 1 if n else 0}"


if __name__ == "__main__":
    mes = sys.argv[1] if len(sys.argv) > 1 else datetime.now(timezone.utc).strftime("%Y.%m")
    print(proxima(sys.stdin.read().split(), mes))
