import pandas as pd
from typing import List, Dict, Callable, Optional, Union, Hashable, Sequence
from pandas import Series
from rapidfuzz import fuzz

Record = Dict[str, str]
FieldWeights = Dict[str, float]
SimilarityFunc = Callable[[Sequence[Hashable], Sequence[Hashable]], float]

class SimilarityScorer:
    """
    Generic similarity scorer for dict or pandas.Series records, weighted by fields.
    Supports early threshold short-circuiting and two modes:
      - optimize=True: inlined, fast dict/Series path
      - optimize=False: uses in-class pandas-based methods
    """
    def __init__(
            self,
            field_weights: FieldWeights,
            similarity_func: SimilarityFunc = fuzz.token_sort_ratio,
            threshold: Optional[float] = None
    ):
        # store configuration
        self.field_weights = field_weights
        self.similarity_func = similarity_func
        self.threshold = threshold
        # prepare sorted fields for optimized path
        self._fields = sorted(field_weights.items(), key=lambda kv: kv[1], reverse=True)
        self._total_weight = sum(w for _, w in self._fields)

    def score(
            self,
            rec1: Union[Record, Series],
            rec2: Union[Record, Series],
            optimize: bool = True
    ) -> float:
        """
        Compute weighted similarity between two records.

        If optimize=True, uses inlined dict/Series fast path.
        If optimize=False and inputs are Series, uses in-class pandas-based methods.
        """
        if not optimize and isinstance(rec1, Series) and isinstance(rec2, Series):
            rows = [rec1, rec2]
            return self.calculate_similarity_score(rows)

        # optimized path (dict or Series via __getitem__)
        total = 0.0
        remaining = self._total_weight
        for field, weight in self._fields:
            remaining -= weight
            a = rec1[field]
            b = rec2[field]
            total += weight * self.similarity_func(str(a), str(b))
            if self.threshold is not None and total + remaining * 100 < self.threshold:
                break
        return total

    def calculate_similarity_score(
            self,
            rows: List[Series]
    ) -> float:
        """
        Outward-facing API: delegates to specialized implementations based on number of rows.
        Supports an optional threshold cut-off to short-circuit early when it's impossible
        to exceed the given threshold.
        """
        if len(rows) == 2:
            return self._score_two_rows(rows[0], rows[1])
        return self._score_multi_rows(rows)

    def _score_two_rows(
            self,
            row1: Series,
            row2: Series
    ) -> float:
        sim = self.similarity_func
        fields = self._fields
        total = 0.0
        remaining_weight = sum(w for _, w in fields)
        # Pre-extract string values
        values1 = {f: str(row1[f]) for f, _ in fields}
        values2 = {f: str(row2[f]) for f, _ in fields}

        for field, weight in fields:
            remaining_weight -= weight
            a = values1[field]
            b = values2[field]
            total += weight * sim(a, b)
            if self.threshold is not None and total + remaining_weight * 100 < self.threshold:
                break
        return total

    def _score_multi_rows(
            self,
            rows: List[Series]
    ) -> float:
        sim = self.similarity_func
        fields = self._fields
        n = len(rows)
        num_pairs = n * (n - 1) / 2
        composite = 0.0
        # Pre-extract strings per field per row
        extracted = {field: [str(r[field]) for r in rows] for field, _ in fields}
        remaining_weight = sum(w for _, w in fields)

        for field, weight in fields:
            remaining_weight -= weight
            texts = extracted[field]
            subtotal = 0.0
            for i in range(n - 1):
                for j in range(i + 1, n):
                    subtotal += sim(texts[i], texts[j])
            average = subtotal / num_pairs if num_pairs else 0.0
            composite += weight * average
            if self.threshold is not None and composite + remaining_weight * 100 < self.threshold:
                break
        return composite

    def batch_score(
            self,
            df1: pd.DataFrame,
            df2: pd.DataFrame,
            key_column: str,
            optimize: bool = True
    ) -> pd.DataFrame:
        """
        Compute each row in df1's best match in df2, returning a DataFrame with key_column, best_match_id, best_score.
        """
        # choose records representation
        if optimize:
            recs1 = df1.to_dict(orient='records')
            recs2 = df2.to_dict(orient='records')
        else:
            recs1 = list(df1.to_dict(orient='records'))
            recs2 = list(df2.to_dict(orient='records'))

        results = []
        for r1 in recs1:
            best_score = -1.0
            best_id = None
            for r2 in recs2:
                score = self.score(r1, r2, optimize=optimize)
                if score > best_score:
                    best_score = score
                    best_id = r2.get('UUID')
            results.append({key_column: r1.get(key_column), 'best_match_id': best_id, 'best_score': best_score})
        return pd.DataFrame(results)
