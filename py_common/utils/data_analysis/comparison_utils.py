import pandas as pd
from typing import List, Dict, Callable, Optional, Union, Sequence, Hashable
from pandas import Series
from rapidfuzz import fuzz

Record = Dict[str, str]
FieldWeights = Dict[str, float]
SimilarityFunc = Callable[[Sequence[Hashable], Sequence[Hashable]], float]

class SimilarityScorer:
    """
    Generic similarity scorer for dict or pandas.Series records, weighted by fields,
    with detailed HoornLogger instrumentation.

    Modes:
      - optimize=True: inlined, fast dict/Series path
      - optimize=False: pandas-based methods for multi-field comparisons
    """
    def __init__(
            self,
            field_weights: FieldWeights,
            logger,
            similarity_func: SimilarityFunc = fuzz.token_sort_ratio,
            threshold: Optional[float] = None
    ):
        self.field_weights = field_weights
        self.similarity_func = similarity_func
        self.threshold = threshold
        self._logger = logger
        self._separator = "Common.SimilarityScorer"

        self._fields = sorted(field_weights.items(), key=lambda kv: kv[1], reverse=True)
        self._total_weight = sum(w for _, w in self._fields)
        self._logger.trace(
            f"Initialized with fields={self._fields}, threshold={self.threshold}",
            separator=self._separator
        )

    def score(
            self,
            rec1: Union[Record, Series],
            rec2: Union[Record, Series],
            optimize: bool = True
    ) -> float:
        self._logger.debug(f"Scoring records optimize={optimize}", separator=self._separator)
        if not optimize and isinstance(rec1, Series) and isinstance(rec2, Series):
            self._logger.trace("Using pandas-based scorer", separator=self._separator)
            rows = [rec1, rec2]
            return self.calculate_similarity_score(rows)

        total = 0.0
        remaining = self._total_weight
        for field, weight in self._fields:
            try:
                a = rec1[field]
                b = rec2[field]
            except KeyError as e:
                self._logger.error(f"Missing field {e} in record", separator=self._separator)
                continue
            contrib = weight * self.similarity_func(str(a), str(b))
            total += contrib
            remaining -= weight
            self._logger.trace(
                f"Field '{field}' contributed {contrib:.2f}, total={total:.2f}, remaining potential={remaining*100:.2f}",
                separator=self._separator
            )
            if self.threshold is not None and total + remaining * 100 < self.threshold:
                self._logger.info(
                    f"Early exit: cannot reach threshold {self.threshold}, current={total:.2f}",
                    separator=self._separator
                )
                break
        self._logger.debug(f"Final optimized score: {total:.2f}", separator=self._separator)
        return total

    def calculate_similarity_score(
            self,
            rows: List[Series]
    ) -> float:
        self._logger.trace(
            f"calculate_similarity_score called on {len(rows)} rows",
            separator=self._separator
        )
        if len(rows) == 2:
            return self._score_two_rows(rows[0], rows[1])
        return self._score_multi_rows(rows)

    def _score_two_rows(
            self,
            row1: Series,
            row2: Series
    ) -> float:
        self._logger.trace("_score_two_rows start", separator=self._separator)
        sim = self.similarity_func
        fields = self._fields
        total = 0.0
        remaining_weight = sum(w for _, w in fields)
        values1 = {f: str(row1[f]) for f, _ in fields}
        values2 = {f: str(row2[f]) for f, _ in fields}

        for field, weight in fields:
            a = values1[field]
            b = values2[field]
            contrib = weight * sim(a, b)
            total += contrib
            remaining_weight -= weight
            self._logger.trace(
                f"Two-row field '{field}': contrib={contrib:.2f}, total={total:.2f}, remaining={remaining_weight*100:.2f}",
                separator=self._separator
            )
            if self.threshold is not None and total + remaining_weight * 100 < self.threshold:
                self._logger.info(
                    f"Two-row early exit threshold {self.threshold}, total={total:.2f}",
                    separator=self._separator
                )
                break
        self._logger.debug(f"_score_two_rows result: {total:.2f}", separator=self._separator)
        return total

    def _score_multi_rows(
            self,
            rows: List[Series]
    ) -> float:
        self._logger.trace("_score_multi_rows start", separator=self._separator)
        sim = self.similarity_func
        fields = self._fields
        n = len(rows)
        num_pairs = n * (n - 1) / 2
        composite = 0.0
        extracted = {field: [str(r[field]) for r in rows] for field, _ in fields}
        remaining_weight = sum(w for _, w in fields)

        for field, weight in fields:
            subtotal = 0.0
            texts = extracted[field]
            for i in range(n - 1):
                for j in range(i + 1, n):
                    subtotal += sim(texts[i], texts[j])
            average = subtotal / num_pairs if num_pairs else 0.0
            contrib = weight * average
            composite += contrib
            remaining_weight -= weight
            self._logger.trace(
                f"Multi-row field '{field}': contrib={contrib:.2f}, composite={composite:.2f}, remaining={remaining_weight*100:.2f}",
                separator=self._separator
            )
            if self.threshold is not None and composite + remaining_weight * 100 < self.threshold:
                self._logger.info(
                    f"Multi-row early exit threshold {self.threshold}, composite={composite:.2f}",
                    separator=self._separator
                )
                break
        self._logger.debug(f"_score_multi_rows result: {composite:.2f}", separator=self._separator)
        return composite

    def batch_score(
            self,
            df1: pd.DataFrame,
            df2: pd.DataFrame,
            key_column: str,
            optimize: bool = True
    ) -> pd.DataFrame:
        self._logger.trace("batch_score start", separator=self._separator)
        recs1 = df1.to_dict(orient='records') if optimize else list(df1.to_dict(orient='records'))
        recs2 = df2.to_dict(orient='records') if optimize else list(df2.to_dict(orient='records'))
        results = []
        for r1 in recs1:
            best_score = -1.0
            best_id = None
            for r2 in recs2:
                score = self.score(r1, r2, optimize=optimize)
                if score > best_score:
                    best_score = score
                    best_id = r2.get('UUID')
            self._logger.debug(
                f"Best match for {r1.get(key_column)}: {best_id} at {best_score:.2f}",
                separator=self._separator
            )
            results.append({key_column: r1.get(key_column), 'best_match_id': best_id, 'best_score': best_score})
        df_out = pd.DataFrame(results)
        self._logger.trace("batch_score complete", separator=self._separator)
        return df_out
