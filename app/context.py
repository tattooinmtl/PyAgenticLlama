from dataclasses import dataclass, field

@dataclass
class ContextManager:
    max_tokens: int = 4096
    system_prompt: str = 'You are a helpful assistant.'
    messages: list = field(default_factory=list)
    total_tokens: int = 0
    threshold: float = 0.80

    def add(self, role: str, content: str):
        self.messages.append({'role': role, 'content': content})

    def update_tokens(self, n: int):
        self.total_tokens = max(self.total_tokens, n)

    def _estimated_tokens(self) -> int:
        """Character-based token estimate (~4 chars/token) used when the server hasn't reported usage yet."""
        chars = sum(
            len(m['content']) if isinstance(m['content'], str)
            else sum(len(p.get('text', '')) for p in m['content'] if isinstance(p, dict))
            for m in self.messages
            if isinstance(m, dict) and 'content' in m
        )
        return chars // 4

    def _effective_tokens(self) -> int:
        return self.total_tokens or self._estimated_tokens()

    def needs_compaction(self) -> bool:
        return self._effective_tokens() >= self.max_tokens * self.threshold and len(self.messages) >= 4

    def usage_pct(self) -> float:
        return min(self._effective_tokens() / max(self.max_tokens, 1), 1.0)

    def get_messages(self, system: str | None = None) -> list:
        sys_prompt = system or self.system_prompt
        return [{'role': 'system', 'content': sys_prompt}] + list(self.messages)

    def apply_summary(self, summary: str, n: int):
        self.messages = (
            [{'role': 'system', 'content': f'[Earlier conversation summary]: {summary}'}]
            + self.messages[n:]
        )
        self.total_tokens = 0

    def clear(self):
        self.messages.clear()
        self.total_tokens = 0

    def info(self) -> dict:
        tokens = self._effective_tokens()
        pct = min(tokens / max(self.max_tokens, 1), 1.0)
        return {
            'total_tokens': tokens,
            'max_tokens': self.max_tokens,
            'usage_pct': round(pct * 100, 1),
            'message_count': len(self.messages),
            'needs_compaction': self.needs_compaction(),
        }

_contexts: dict[str, ContextManager] = {}

def get_context(conv_id: str = 'default') -> ContextManager:
    if conv_id not in _contexts:
        _contexts[conv_id] = ContextManager()
    return _contexts[conv_id]

def list_context_ids() -> list[str]:
    return list(_contexts.keys())
