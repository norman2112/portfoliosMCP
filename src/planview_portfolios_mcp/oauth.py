"""OAuth token management for Planview Portfolios API."""

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional

import httpx

from .config import settings
from .exceptions import PlanviewAuthError, PlanviewError

logger = logging.getLogger(__name__)


@dataclass
class OAuthToken:
    """OAuth token with expiration tracking."""

    access_token: str
    expires_at: datetime
    token_type: str = "bearer"

    def is_expired(self, buffer_seconds: int = 60) -> bool:
        """Check if token is expired (with buffer for clock skew)."""
        return datetime.now() >= (self.expires_at - timedelta(seconds=buffer_seconds))


class OAuthTokenManager:
    """Manages OAuth token lifecycle with caching and automatic refresh."""

    def __init__(self):
        self._token: Optional[OAuthToken] = None
        self._lock = asyncio.Lock()

    async def get_token(self, force_refresh: bool = False) -> str:
        """Get a valid OAuth token, refreshing if necessary.

        Args:
            force_refresh: Force a new token even if current is valid

        Returns:
            Bearer token string

        Raises:
            PlanviewAuthError: If authentication fails
            PlanviewError: If token retrieval fails
        """
        async with self._lock:
            # Check if we have a valid token
            if not force_refresh and self._token and not self._token.is_expired():
                return self._token.access_token

            # Get a new token
            token = await self._fetch_token()
            self._token = token
            return token.access_token

    async def _fetch_token(self) -> OAuthToken:
        """Fetch a new OAuth token from the API.

        Returns:
            OAuthToken with access token and expiration

        Raises:
            PlanviewAuthError: If authentication fails
            PlanviewError: If token retrieval fails
        """
        if not settings.planview_client_id or not settings.planview_client_secret:
            raise PlanviewAuthError(
                "OAuth credentials not configured. "
                "Set PLANVIEW_CLIENT_ID and PLANVIEW_CLIENT_SECRET environment variables."
            )

        token_url = f"{settings.planview_api_url}/public-api/v1/oauth/token"

        try:
            async with httpx.AsyncClient(timeout=settings.api_timeout) as client:
                # Use multipart/form-data per API docs
                form = {
                    "grant_type": (None, "client_credentials"),
                    "client_id": (None, settings.planview_client_id),
                    "client_secret": (None, settings.planview_client_secret),
                }
                response = await client.post(token_url, files=form)

                if response.status_code == 401:
                    raise PlanviewAuthError(
                        "Invalid OAuth credentials. Check CLIENT_ID and CLIENT_SECRET."
                    )

                response.raise_for_status()
                data = response.json()

                access_token = data.get("access_token")
                expires_in = data.get("expires_in", 3600)  # Default to 60 minutes
                token_type = data.get("token_type", "bearer")

                if not access_token:
                    raise PlanviewError("Token response missing access_token")

                # Calculate expiration time
                expires_at = datetime.now() + timedelta(seconds=expires_in)

                logger.info(
                    f"Successfully obtained OAuth token (expires in {expires_in}s)"
                )

                return OAuthToken(
                    access_token=access_token,
                    expires_at=expires_at,
                    token_type=token_type,
                )

        except httpx.HTTPStatusError as e:
            if e.response.status_code in (401, 403):
                raise PlanviewAuthError(
                    f"OAuth authentication failed: {e.response.text}"
                ) from e
            raise PlanviewError(
                f"Failed to obtain OAuth token: HTTP {e.response.status_code}"
            ) from e
        except httpx.TimeoutException as e:
            raise PlanviewError(f"Timeout obtaining OAuth token: {str(e)}") from e
        except httpx.NetworkError as e:
            raise PlanviewError(
                f"Network error obtaining OAuth token: {str(e)}"
            ) from e
        except Exception as e:
            raise PlanviewError(f"Unexpected error obtaining OAuth token: {str(e)}") from e

    async def clear_token(self):
        """Clear the cached token (force refresh on next request)."""
        async with self._lock:
            self._token = None


# Global token manager instance
_token_manager = OAuthTokenManager()


async def get_oauth_token(force_refresh: bool = False) -> str:
    """Get a valid OAuth token.

    Args:
        force_refresh: Force a new token even if current is valid

    Returns:
        Bearer token string
    """
    return await _token_manager.get_token(force_refresh=force_refresh)


async def clear_oauth_token():
    """Clear the cached OAuth token."""
    await _token_manager.clear_token()


class OKROAuthTokenManager:
    """Manages OKR OAuth token lifecycle with caching and automatic refresh."""
    
    def __init__(self):
        self._token: Optional[OAuthToken] = None
        self._lock = asyncio.Lock()
    
    async def get_token(self, force_refresh: bool = False) -> str:
        """Get a valid OKR OAuth token, refreshing if necessary.
        
        Args:
            force_refresh: Force a new token even if current is valid
            
        Returns:
            Bearer token string
            
        Raises:
            PlanviewAuthError: If authentication fails
            PlanviewError: If token retrieval fails
        """
        async with self._lock:
            # Check if we have a valid token
            if not force_refresh and self._token and not self._token.is_expired():
                return self._token.access_token
            
            # Get a new token
            token = await self._fetch_token()
            self._token = token
            return token.access_token
    
    async def _fetch_token(self) -> OAuthToken:
        """Fetch a new OKR OAuth token from the API.
        
        Returns:
            OAuthToken with access token and expiration
            
        Raises:
            PlanviewAuthError: If authentication fails
            PlanviewError: If token retrieval fails
        """
        if not settings.planview_okr_client_id or not settings.planview_okr_client_secret:
            raise PlanviewAuthError(
                "OKR OAuth credentials not configured. "
                "Set PLANVIEW_OKR_CLIENT_ID and PLANVIEW_OKR_CLIENT_SECRET environment variables."
            )
        
        # OKR OAuth endpoint
        token_url = "https://us.id.planview.com/io/v1/oauth2/token"
        
        try:
            async with httpx.AsyncClient(timeout=settings.api_timeout) as client:
                # Use application/x-www-form-urlencoded per OKR API
                form_data = {
                    "grant_type": "client_credentials",
                    "client_id": settings.planview_okr_client_id,
                    "client_secret": settings.planview_okr_client_secret,
                }
                response = await client.post(token_url, data=form_data)
                
                if response.status_code == 401:
                    raise PlanviewAuthError(
                        "Invalid OKR OAuth credentials. Check PLANVIEW_OKR_CLIENT_ID and PLANVIEW_OKR_CLIENT_SECRET."
                    )
                
                response.raise_for_status()
                data = response.json()
                
                access_token = data.get("access_token")
                expires_in = data.get("expires_in", 3600)  # Default to 60 minutes
                token_type = data.get("token_type", "bearer")
                
                if not access_token:
                    raise PlanviewError("OKR token response missing access_token")
                
                # Calculate expiration time
                expires_at = datetime.now() + timedelta(seconds=expires_in)
                
                logger.info(
                    f"Successfully obtained OKR OAuth token (expires in {expires_in}s)"
                )
                
                return OAuthToken(
                    access_token=access_token,
                    expires_at=expires_at,
                    token_type=token_type,
                )
        
        except httpx.HTTPStatusError as e:
            if e.response.status_code in (401, 403):
                raise PlanviewAuthError(
                    f"OKR OAuth authentication failed: {e.response.text}"
                ) from e
            raise PlanviewError(
                f"Failed to obtain OKR OAuth token: HTTP {e.response.status_code}"
            ) from e
        except httpx.TimeoutException as e:
            raise PlanviewError(f"Timeout obtaining OKR OAuth token: {str(e)}") from e
        except httpx.NetworkError as e:
            raise PlanviewError(
                f"Network error obtaining OKR OAuth token: {str(e)}"
            ) from e
        except Exception as e:
            raise PlanviewError(f"Unexpected error obtaining OKR OAuth token: {str(e)}") from e
    
    async def clear_token(self):
        """Clear the cached token (force refresh on next request)."""
        async with self._lock:
            self._token = None


# Global OKR token manager instance
_okr_token_manager = OKROAuthTokenManager()


async def get_okr_oauth_token(force_refresh: bool = False) -> str:
    """Get a valid OKR OAuth token with automatic refresh.
    
    Args:
        force_refresh: Force a new token even if current is valid
        
    Returns:
        Bearer token string
        
    Raises:
        PlanviewAuthError: If OAuth credentials are not configured
        PlanviewError: If token retrieval fails
    """
    return await _okr_token_manager.get_token(force_refresh=force_refresh)


async def clear_okr_oauth_token():
    """Clear the cached OKR OAuth token."""
    await _okr_token_manager.clear_token()

