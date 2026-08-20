"""
Coloca `src/` no sys.path para os pontos de entrada da raiz.

Os módulos da biblioteca vivem em `src/gk_scouting/`, mas `main.py`,
`streamlit_app.py` e `download_extended_data.py` são executados a partir
da raiz do repositório — e nem o Python nem o `streamlit run` colocam
`src/` no caminho de importação automaticamente.

Importar este módulo resolve isso sem exigir um passo de instalação, o que
mantém válidas as instruções do README (`pip install -r requirements.txt`
seguido de `streamlit run streamlit_app.py`).

Quando o projeto passar a ser instalado como pacote (`pip install -e .`),
este ficheiro deixa de ser necessário e pode ser removido.

Uso:

    import _bootstrap  # noqa: F401
    from gk_scouting.metrics import build_scouting_table

Os testes não precisam disto: usam `pythonpath = src` no `pytest.ini`.
"""

import pathlib
import sys

SRC = pathlib.Path(__file__).resolve().parent / "src"

if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))
