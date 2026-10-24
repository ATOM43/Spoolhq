"""Weighted tokens: what the per-ticket token budget counts."""


def weighted_tokens(input_tokens: int, output_tokens: int, cache_read_tokens: int) -> int:
    """Tokens with cache reads at a tenth, since they cost a tenth of fresh input.

    ``input_tokens`` includes the cache reads (and cache writes), as SpoolHQ stores it.
    """
    return input_tokens - cache_read_tokens + output_tokens + cache_read_tokens // 10
