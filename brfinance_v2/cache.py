"""
Módulo de cache persistente para a biblioteca brFinance.
Armazena dados em arquivos JSON locais com expiração automática.
"""
import sys
from pathlib import Path

# Configuração de path para imports do projeto
pasta_raiz = Path(__file__).parent.parent
if str(pasta_raiz) not in sys.path:
    sys.path.insert(0, str(pasta_raiz))

import json
import logging
import time
import os
from datetime import datetime, timedelta
from typing import Optional, Any, Dict

logger = logging.getLogger(__name__)

class CacheManager:
    """Gerencia o cache local de dados persistentes."""

    # Diretório padrão para cache: .cache na raiz do projeto
    CACHE_DIR = pasta_raiz / ".cache"

    def __init__(self, use_cache: bool = True) -> None:
        """Inicializa o gerenciador de cache.

        Args:
            use_cache: Se False, desabilita a leitura/escrita de cache.
        """
        self.use_cache = use_cache
        if self.use_cache:
            self.CACHE_DIR.mkdir(exist_ok=True)

    def get_data(self, key: str, max_age_hours: int = 24) -> Optional[Any]:
        """Tenta obter dados do cache se não tiverem expirado.

        Args:
           key: Chave única do cache (nome do arquivo).
           max_age_hours: Tempo máximo de vida do cache em horas.

        Returns:
            O dado se for válido e existir, caso contrário None.
        """
        if not self.use_cache:
            return None

        cache_file = self.CACHE_DIR / f"{key}.json"

        if not cache_file.exists():
            return None

        try:
            # Verifica a idade do arquivo
            file_mod_time = datetime.fromtimestamp(os.path.getmtime(cache_file))
            if datetime.now() - file_mod_time > timedelta(hours=max_age_hours):
                logger.info(f"Cache expirado para {key}")
                return None

            with open(cache_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data

        except (json.JSONDecodeError, OSError) as e:
            logger.warning(f"Erro ao ler cache para {key}: {str(e)}")
            return None

    def save_data(self, key: str, data: Any) -> None:
        """Salva dados no cache persistente.

        Args:
            key: Chave única do cache (nome do arquivo).
            data: Dados serializáveis em JSON.
        """
        if not self.use_cache:
            return

        cache_file = self.CACHE_DIR / f"{key}.json"

        try:
            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            logger.debug(f"Cache salvo com sucesso para {key}")
        except (TypeError, OSError) as e:
            logger.warning(f"Não foi possível salvar cache para {key}: {str(e)}")

    def clear(self, key: Optional[str] = None) -> None:
        """Limpa o cache (específico ou tudo).

        Args:
            key: Se fornecido, remove apenas este cache. Caso contrário, limpa tudo.
        """
        if not self.use_cache:
            return

        if key:
            file_path = self.CACHE_DIR / f"{key}.json"
            if file_path.exists():
                os.remove(file_path)
        else:
            for file_path in self.CACHE_DIR.glob("*.json"):
                os.remove(file_path)
