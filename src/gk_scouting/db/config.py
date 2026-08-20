"""
Configuração de ligação à base de dados, via variável de ambiente.

Não há password nem string de ligação hardcoded em código nenhum: tudo
vem de `DATABASE_URL`. Localmente essa variável é definida num ficheiro
`.env` (nunca commitado -- ver `.env.example` e `.gitignore`) e lida pelo
`docker-compose.yml` / por quem correr os scripts de migração.
"""

import os


def get_database_url() -> str:
    """
    Devolve a string de ligação SQLAlchemy a partir de `DATABASE_URL`.

    Levanta `RuntimeError` com uma mensagem explícita em vez de usar um
    valor por omissão -- um default silencioso (ex.: apontar para
    localhost com uma password fixa) é exatamente o tipo de segredo
    hardcoded que este módulo existe para evitar.
    """

    url = os.environ.get("DATABASE_URL")

    if not url:
        raise RuntimeError(
            "DATABASE_URL não está definida. Copia .env.example para .env "
            "e ajusta os valores, ou exporta DATABASE_URL diretamente no "
            "ambiente antes de correr migrações ou a aplicação."
        )

    return url
