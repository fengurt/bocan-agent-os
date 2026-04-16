"""
IdentityVault - 凭证保险箱
使用 keyring + AES 加密存储平台账号密码、API Key 等敏感信息
"""
import json
import logging
import os
from typing import Any, Optional

import keyring
from cryptography.fernet import Fernet

logger = logging.getLogger(__name__)

SERVICE_NAME = "bocan-agent-os"
_encryption_key: Optional[bytes] = None


def _get_encryption_key() -> bytes:
    """获取或生成加密密钥（存储在系统 Keychain 中）"""
    global _encryption_key
    if _encryption_key is not None:
        return _encryption_key

    stored = keyring.get_password(SERVICE_NAME, "_encryption_key")
    if stored:
        _encryption_key = stored.encode()
    else:
        _encryption_key = Fernet.generate_key()
        keyring.set_password(SERVICE_NAME, "_encryption_key", _encryption_key.decode())
    return _encryption_key


def _get_cipher() -> Fernet:
    return Fernet(_get_encryption_key())


class IdentityVault:
    """
    凭证保险箱
    - 使用系统 Keychain 存储加密密钥
    - 对敏感数据使用 Fernet AES 加密后存储
    - 支持平台凭证、API Key、Token 等
    """

    def __init__(self, tenant_id: str):
        self.tenant_id = tenant_id
        self._cipher = _get_cipher()
        self._cache: dict[str, str] = {}

    def _key(self, platform: str, key_name: str) -> str:
        """构建 keyring 的 key"""
        return f"{self.tenant_id}/{platform}/{key_name}"

    def set(self, platform: str, key_name: str, value: str) -> None:
        """
        存储凭证（自动加密）

        Args:
            platform: 平台名，如 "meituan", "ele"
            key_name: 键名，如 "password", "app_secret"
            value:    明文值
        """
        encrypted = self._cipher.encrypt(value.encode()).decode()
        keyring.set_password(SERVICE_NAME, self._key(platform, key_name), encrypted)
        self._cache[f"{platform}/{key_name}"] = value
        logger.info(f"Stored credential: {platform}/{key_name}")

    def get(self, platform: str, key_name: str) -> Optional[str]:
        """
        读取凭证（自动解密，内存缓存）

        Returns:
            明文值或 None
        """
        cache_key = f"{platform}/{key_name}"
        if cache_key in self._cache:
            return self._cache[cache_key]

        raw = keyring.get_password(SERVICE_NAME, self._key(platform, key_name))
        if raw is None:
            return None

        try:
            decrypted = self._cipher.decrypt(raw.encode()).decode()
            self._cache[cache_key] = decrypted
            return decrypted
        except Exception as e:
            logger.error(f"Failed to decrypt credential {platform}/{key_name}: {e}")
            return None

    def delete(self, platform: str, key_name: str) -> None:
        """删除凭证"""
        keyring.delete_password(SERVICE_NAME, self._key(platform, key_name))
        self._cache.pop(f"{platform}/{key_name}", None)
        logger.info(f"Deleted credential: {platform}/{key_name}")

    def list_platforms(self) -> list[str]:
        """列出已存储凭证的平台"""
        return list(set(k.split("/")[1] for k in self._cache.keys()))

    def store_meituan(self, app_id: str, app_secret: str) -> None:
        """便捷方法：存储美团 API 凭证"""
        self.set("meituan", "app_id", app_id)
        self.set("meituan", "app_secret", app_secret)

    def get_meituan_credentials(self) -> dict[str, str]:
        """获取美团凭证"""
        return {
            "app_id": self.get("meituan", "app_id") or "",
            "app_secret": self.get("meituan", "app_secret") or "",
        }
