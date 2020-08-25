"""covid_api.cache.memcache: memcached layer."""

from typing import Optional, Tuple, Dict

from bmemcached import Client

from covid_api.ressources.enums import ImageType


class CacheLayer(object):
    """Memcache Wrapper."""

    def __init__(
        self,
        host,
        port: int = 11211,
        user: Optional[str] = None,
        password: Optional[str] = None,
    ):
        """Init Cache Layer."""
        self.client = Client((f"{host}:{port}",), user, password)

    def get_image_from_cache(self, img_hash: str) -> Tuple[bytes, ImageType]:
        """
        Get image body from cache layer.

        Attributes
        ----------
            img_hash : str
                file url.

        Returns
        -------
            img : bytes
                image body.
            ext : str
                image ext

        """
        content, ext = self.client.get(img_hash)
        return content, ext

    def set_image_cache(
        self, img_hash: str, body: Tuple[bytes, ImageType], timeout: int = 432000
    ) -> bool:
        """
        Set base64 encoded image body in cache layer.

        Attributes
        ----------
            img_hash : str
                file url.
            body : tuple
                image body + ext
        Returns
        -------
            bool

        """
        try:
            return self.client.set(img_hash, body, time=timeout)
        except Exception:
            return False

    def get_dataset_from_cache(self, ds_hash: str ) -> Dict:
        """Get dataset response from cache layer"""
        return self.client.get(ds_hash)

    def set_dataset_cache(self, ds_hash: str, body: Dict, timeout: int = 3600) -> bool:
        """Set dataset response in cache layer"""
        try:
            return self.client.set(ds_hash, body, time=timeout)
        except Exception:
            return False
