import os
from dataclasses import dataclass, field
from dotenv import load_dotenv

load_dotenv()

MAX_CONTEXT_TOKENS = int(os.getenv("MAX_CONTEXT_TOKENS", "4096"))


@dataclass
class SelectionResult:
    """Result of the selection stage — which chunks made the cut."""
    selected: list = field(default_factory=list)
    excluded: list = field(default_factory=list)
    total_tokens: int = 0
    total_score: float = 0.0
    max_budget: int = MAX_CONTEXT_TOKENS
    strategy: str = "greedy_by_density"
    savings: dict = field(default_factory=dict)

    def __post_init__(self):
        if not self.savings:
            self._compute_savings()

    def _compute_savings(self):
        total_available = 0
        for c in self.selected + self.excluded:
            total_available += c.chunk.token_count
        
        tokens_saved = total_available - self.total_tokens
        savings_pct = (tokens_saved / max(total_available, 1)) * 100
        
        self.savings = {
            "tokens_used": self.total_tokens,
            "tokens_available": total_available,
            "tokens_saved": tokens_saved,
            "savings_percent": round(savings_pct, 1),
            "budget_utilization_percent": round(
                (self.total_tokens / max(self.max_budget, 1)) * 100, 1
            ),
        }

    @property
    def context_text(self):
        """Selected chunks combined in document order, ready for the LLM."""
        def sort_key(chunk):
            return (chunk.chunk.document_id, chunk.chunk.chunk_index) # ScoredChunk.chunk.document_id
        
        ordered = sorted(self.selected, key=sort_key)
        
        parts = []
        for c in ordered:
            parts.append(c.chunk.text)
        return "\n\n".join(parts)


def _greedy_by_density(chunks, max_tokens):
    """Pick chunks with highest value-per-token first."""
    def value_density(chunk):
        tokens = max(chunk.chunk.token_count, 1)
        return chunk.context_score / tokens
    
    sorted_chunks = sorted(chunks, key=value_density, reverse=True)
    
    selected = []
    excluded = []
    tokens_used = 0
    total_score = 0.0
    
    for chunk in sorted_chunks:
        chunk_tokens = max(chunk.chunk.token_count, 1)
        
        if tokens_used + chunk_tokens <= max_tokens:
            selected.append(chunk)
            tokens_used += chunk_tokens
            total_score += chunk.context_score
        else:
            excluded.append(chunk)
    
    return selected, excluded, tokens_used, total_score


def _greedy_by_score(chunks, max_tokens):
    """Pick highest-scoring chunks first. Skip chunks that don't fit."""
    def get_score(chunk):
        return chunk.context_score
    
    sorted_chunks = sorted(chunks, key=get_score, reverse=True)
    
    selected = []
    excluded = []
    tokens_used = 0
    total_score = 0.0
    
    for chunk in sorted_chunks:
        chunk_tokens = max(chunk.chunk.token_count, 1)
        
        if tokens_used + chunk_tokens <= max_tokens:
            selected.append(chunk)
            tokens_used += chunk_tokens
            total_score += chunk.context_score
        else:
            excluded.append(chunk)
    
    return selected, excluded, tokens_used, total_score


STRATEGIES = {
    "greedy_by_density": _greedy_by_density,
    "greedy_by_score": _greedy_by_score,
}


def select_chunks(scoring_result, max_tokens=MAX_CONTEXT_TOKENS, strategy="greedy_by_density"):
    """Select the best subset of chunks that fits within the token budget."""
    if strategy not in STRATEGIES:
        raise ValueError(f"Unknown strategy '{strategy}'. Options: {list(STRATEGIES.keys())}")
    
    chunks = scoring_result.ranked_chunks
    
    if not chunks:
        return SelectionResult(max_budget=max_tokens, strategy=strategy)
    
    strategy_fn = STRATEGIES[strategy]
    selected, excluded, tokens_used, total_score = strategy_fn(chunks, max_tokens)
    
    return SelectionResult(
        selected=selected,
        excluded=excluded,
        total_tokens=tokens_used,
        total_score=round(total_score, 6),
        max_budget=max_tokens,
        strategy=strategy,
    )