from abc import ABC, abstractmethod

class IRateLimiter(ABC):
    @abstractmethod
    def allow_request(self, key: str, weight: float = 1.0) -> bool:
        pass

    @abstractmethod
    def get_remaining_tokens(self, key: str) -> float:
        pass

    @abstractmethod
    def get_headers(self, key: str) -> dict:
        pass

class IRateLimitStore(ABC):
    @abstractmethod
    def get_state(self, key: str) -> dict:
        pass

    @abstractmethod
    def set_state(self, key: str, tokens: float, last_refill: float) -> None:
        pass


class IAsyncRateLimitStore(ABC):
    @abstractmethod
    async def get_state(self, key: str) -> dict:
        pass

    @abstractmethod
    async def set_state(self, key: str, tokens: float, last_refill: float) -> None:
        pass
