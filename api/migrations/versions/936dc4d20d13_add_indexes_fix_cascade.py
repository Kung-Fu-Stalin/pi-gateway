
"""add indexes fix cascade
Revision ID: 936dc4d20d13
Revises: 2a0569dfa111
Create Date: 2026-03-14 21:21:56.611288
"""
from typing import Sequence, Union
from alembic import op

revision: str = '936dc4d20d13'
down_revision: Union[str, Sequence[str], None] = '2a0569dfa111'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _create_index_safe(name, table, columns, unique=False):
    try:
        op.create_index(name, table, columns, unique=unique)
    except Exception:
        pass


def upgrade() -> None:
    _create_index_safe('ix_domain_groups_name', 'domain_groups', ['name'], unique=True)
    _create_index_safe('ix_domains_domain', 'domains', ['domain'], unique=True)
    _create_index_safe('ix_proxy_users_pac_token', 'proxy_users', ['pac_token'], unique=True)
    _create_index_safe('ix_refresh_tokens_token_hash', 'refresh_tokens', ['token_hash'], unique=True)


def downgrade() -> None:
    try:
        op.drop_index('ix_refresh_tokens_token_hash', table_name='refresh_tokens')
        op.drop_index('ix_proxy_users_pac_token', table_name='proxy_users')
        op.drop_index('ix_domains_domain', table_name='domains')
        op.drop_index('ix_domain_groups_name', table_name='domain_groups')
    except Exception:
        pass