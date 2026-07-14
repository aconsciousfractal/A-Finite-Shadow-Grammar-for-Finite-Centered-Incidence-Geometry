#!/usr/bin/env python3
"""Read-only exact checker for the public X13 Type-A static certificate.

The checker uses only the Python standard library.  It independently rebuilds
the locked A3 lattice matrices and the rational Young-seminormal blocks for the
four finite incidence layers recorded by the certificate.  It never writes a
file and is deliberately not a thirteenth quantitative replay route.
"""

from __future__ import annotations

from collections import Counter
from fractions import Fraction
from itertools import combinations, permutations
import json
from math import factorial, gcd
from pathlib import Path
import re
import sys
from time import perf_counter
from typing import Iterable, Sequence


ROOT = Path(__file__).resolve().parents[1]
CERTIFICATE = ROOT / "artifacts" / "x13_type_a_lattice_rank_mass_certificate.json"
PASS_MARKER = "PASS_X13_TYPE_A_LATTICE_RANK_MASS_CERTIFICATE"
FAIL_MARKER = "FAIL_X13_TYPE_A_LATTICE_RANK_MASS_CERTIFICATE"

Permutation = tuple[int, ...]
Partition = tuple[int, ...]
RationalMatrix = list[list[Fraction]]


def compose(left: Permutation, right: Permutation) -> Permutation:
    """Right-to-left composition: (left right)(i) = left(right(i))."""

    return tuple(left[right[i]] for i in range(len(left)))


def identity_permutation(n: int) -> Permutation:
    return tuple(range(n))


def parse_word(word: str, n: int) -> Permutation:
    if not isinstance(word, str) or len(word) != n or not word.isascii():
        raise ValueError(f"invalid one-line word {word!r} for S_{n}")
    if not word.isdigit() or n > 9:
        raise ValueError(f"unsupported one-line word {word!r}")
    result = tuple(int(char) - 1 for char in word)
    if sorted(result) != list(range(n)):
        raise ValueError(f"word {word!r} is not a permutation of 1,...,{n}")
    return result


def cycle_type(permutation: Permutation) -> tuple[int, ...]:
    seen: set[int] = set()
    lengths: list[int] = []
    for start in range(len(permutation)):
        if start in seen:
            continue
        current = start
        length = 0
        while current not in seen:
            seen.add(current)
            current = permutation[current]
            length += 1
        lengths.append(length)
    return tuple(sorted(lengths, reverse=True))


def histogram(words: Sequence[Permutation]) -> dict[str, int]:
    counts = Counter(cycle_type(word) for word in words)
    return {",".join(str(part) for part in key): counts[key] for key in sorted(counts, reverse=True)}


def zero_matrix(rows: int, columns: int | None = None) -> RationalMatrix:
    columns = rows if columns is None else columns
    return [[Fraction(0) for _ in range(columns)] for _ in range(rows)]


def identity_matrix(size: int) -> RationalMatrix:
    return [[Fraction(int(i == j)) for j in range(size)] for i in range(size)]


def matrix_multiply(left: RationalMatrix, right: RationalMatrix) -> RationalMatrix:
    rows = len(left)
    middle = len(right)
    columns = len(right[0])
    return [
        [sum(left[i][k] * right[k][j] for k in range(middle)) for j in range(columns)]
        for i in range(rows)
    ]


def matrix_add_in_place(target: RationalMatrix, source: RationalMatrix) -> None:
    for i, row in enumerate(source):
        for j, value in enumerate(row):
            target[i][j] += value


def rational_rank(matrix: Sequence[Sequence[int | Fraction]]) -> int:
    work = [[Fraction(value) for value in row] for row in matrix]
    if not work:
        return 0
    pivot_row = 0
    for column in range(len(work[0])):
        pivot = next(
            (row for row in range(pivot_row, len(work)) if work[row][column] != 0),
            None,
        )
        if pivot is None:
            continue
        work[pivot_row], work[pivot] = work[pivot], work[pivot_row]
        pivot_value = work[pivot_row][column]
        for row in range(pivot_row + 1, len(work)):
            if work[row][column] == 0:
                continue
            factor = work[row][column] / pivot_value
            work[row] = [
                value - factor * pivot_entry
                for value, pivot_entry in zip(work[row], work[pivot_row])
            ]
        pivot_row += 1
        if pivot_row == len(work):
            break
    return pivot_row


def determinant(matrix: Sequence[Sequence[int | Fraction]]) -> Fraction:
    size = len(matrix)
    if size == 0:
        return Fraction(1)
    work = [[Fraction(value) for value in row] for row in matrix]
    result = Fraction(1)
    sign = 1
    for column in range(size):
        pivot = next((row for row in range(column, size) if work[row][column] != 0), None)
        if pivot is None:
            return Fraction(0)
        if pivot != column:
            work[column], work[pivot] = work[pivot], work[column]
            sign *= -1
        pivot_value = work[column][column]
        result *= pivot_value
        for row in range(column + 1, size):
            if work[row][column] == 0:
                continue
            factor = work[row][column] / pivot_value
            for target_column in range(column + 1, size):
                work[row][target_column] -= factor * work[column][target_column]
    return sign * result


def determinantal_divisors(matrix: Sequence[Sequence[int]]) -> list[int]:
    row_count = len(matrix)
    column_count = len(matrix[0])
    result: list[int] = []
    for size in range(1, min(row_count, column_count) + 1):
        divisor = 0
        for rows in combinations(range(row_count), size):
            for columns in combinations(range(column_count), size):
                minor = [[matrix[row][column] for column in columns] for row in rows]
                value = determinant(minor)
                if value.denominator != 1:
                    raise ArithmeticError("an integral minor acquired a denominator")
                divisor = gcd(divisor, abs(value.numerator))
        result.append(divisor)
    return result


def smith_divisors_from_determinantal(divisors: Sequence[int]) -> list[int]:
    previous = 1
    smith: list[int] = []
    zero_seen = False
    for divisor in divisors:
        if divisor == 0:
            zero_seen = True
            smith.append(0)
            continue
        if zero_seen or divisor % previous != 0:
            raise ArithmeticError("invalid determinantal-divisor chain")
        smith.append(divisor // previous)
        previous = divisor
    return smith


def standard_lattice_matrix(words: Sequence[Permutation]) -> list[list[int]]:
    """Sum the standard S_n action in basis e_1-e_n,...,e_{n-1}-e_n."""

    n = len(words[0])
    dimension = n - 1
    total = [[0 for _ in range(dimension)] for _ in range(dimension)]
    for word in words:
        image_of_n = word[-1]
        for column in range(dimension):
            image = word[column]
            if image < dimension:
                total[image][column] += 1
            if image_of_n < dimension:
                total[image_of_n][column] -= 1
    return total


def integer_partitions(n: int, maximum: int | None = None) -> list[Partition]:
    if n == 0:
        return [()]
    maximum = n if maximum is None else min(maximum, n)
    result: list[Partition] = []
    for first in range(maximum, 0, -1):
        for rest in integer_partitions(n - first, first):
            result.append((first,) + rest)
    return result


def standard_tableaux(partition: Partition) -> list[tuple[int, ...]]:
    cells = [(row, column) for row, length in enumerate(partition) for column in range(length)]
    cell_index = {cell: index for index, cell in enumerate(cells)}
    tableaux: list[tuple[int, ...]] = []
    for values in permutations(range(len(cells))):
        valid = True
        for index, (row, column) in enumerate(cells):
            if column + 1 < partition[row]:
                if values[index] > values[cell_index[(row, column + 1)]]:
                    valid = False
                    break
            if row + 1 < len(partition) and column < partition[row + 1]:
                if values[index] > values[cell_index[(row + 1, column)]]:
                    valid = False
                    break
        if valid:
            tableaux.append(tuple(values))
    return tableaux


def seminormal_generators(partition: Partition) -> tuple[int, list[RationalMatrix]]:
    tableaux = standard_tableaux(partition)
    index = {tableau: position for position, tableau in enumerate(tableaux)}
    cells = [(row, column) for row, length in enumerate(partition) for column in range(length)]
    generators: list[RationalMatrix] = []
    for adjacent in range(sum(partition) - 1):
        matrix = zero_matrix(len(tableaux))
        for tableau_index, tableau in enumerate(tableaux):
            locations = {value: cells[position] for position, value in enumerate(tableau)}
            row, column = locations[adjacent]
            next_row, next_column = locations[adjacent + 1]
            if row == next_row:
                matrix[tableau_index][tableau_index] = Fraction(1)
            elif column == next_column:
                matrix[tableau_index][tableau_index] = Fraction(-1)
            else:
                axial_distance = (next_column - next_row) - (column - row)
                rho = Fraction(1, axial_distance)
                swapped = list(tableau)
                left_position = swapped.index(adjacent)
                right_position = swapped.index(adjacent + 1)
                swapped[left_position], swapped[right_position] = (
                    swapped[right_position],
                    swapped[left_position],
                )
                partner = index[tuple(swapped)]
                matrix[tableau_index][tableau_index] = rho
                matrix[partner][tableau_index] = Fraction(1)
                matrix[tableau_index][partner] = Fraction(1) - rho * rho
                matrix[partner][partner] = -rho
        generators.append(matrix)
    return len(tableaux), generators


def representation_relations_hold(generators: Sequence[RationalMatrix]) -> bool:
    if not generators:
        return True
    dimension = len(generators[0])
    identity = identity_matrix(dimension)
    if any(matrix_multiply(generator, generator) != identity for generator in generators):
        return False
    for left_index, left in enumerate(generators):
        for right_index, right in enumerate(generators):
            distance = abs(left_index - right_index)
            if distance > 1 and matrix_multiply(left, right) != matrix_multiply(right, left):
                return False
            if distance == 1:
                left_braid = matrix_multiply(matrix_multiply(left, right), left)
                right_braid = matrix_multiply(matrix_multiply(right, left), right)
                if left_braid != right_braid:
                    return False
    return True


def all_representation_matrices(
    n: int, partition: Partition
) -> tuple[int, dict[Permutation, RationalMatrix], bool]:
    dimension, generators = seminormal_generators(partition)
    relations_ok = representation_relations_hold(generators)
    adjacent_permutations: list[Permutation] = []
    for adjacent in range(n - 1):
        generator = list(range(n))
        generator[adjacent], generator[adjacent + 1] = (
            generator[adjacent + 1],
            generator[adjacent],
        )
        adjacent_permutations.append(tuple(generator))

    identity = identity_permutation(n)
    matrices: dict[Permutation, RationalMatrix] = {identity: identity_matrix(dimension)}
    frontier = [identity]
    while frontier:
        current = frontier.pop()
        for adjacent_permutation, generator_matrix in zip(adjacent_permutations, generators):
            successor = compose(current, adjacent_permutation)
            candidate = matrix_multiply(matrices[current], generator_matrix)
            if successor not in matrices:
                matrices[successor] = candidate
                frontier.append(successor)
            elif matrices[successor] != candidate:
                relations_ok = False
    return dimension, matrices, relations_ok and len(matrices) == factorial(n)


def incidence_layer(n: int, fixed_hits: int, reversal_hits: int) -> list[Permutation]:
    return [
        word
        for word in permutations(range(n))
        if sum(word[index] == index for index in range(n)) == fixed_hits
        and sum(word[index] == n - 1 - index for index in range(n)) == reversal_hits
    ]


def parse_incidence_row(label: str) -> tuple[int, int, int]:
    match = re.fullmatch(r"I_(\d+)\((\d+),(\d+)\)", label)
    if match is None:
        raise ValueError(f"invalid incidence-row label {label!r}")
    return tuple(int(value) for value in match.groups())  # type: ignore[return-value]


class Audit:
    def __init__(self) -> None:
        self.passed = 0
        self.failures: list[str] = []

    def check(self, condition: bool, name: str, detail: str = "") -> None:
        if condition:
            self.passed += 1
            return
        suffix = f": {detail}" if detail else ""
        self.failures.append(f"{name}{suffix}")

    @property
    def total(self) -> int:
        return self.passed + len(self.failures)


def verify_value_witness(certificate: dict[str, object], audit: Audit) -> None:
    witness = certificate.get("type_a_value_witness")
    if not isinstance(witness, dict):
        audit.check(False, "value_witness_present")
        return

    audit.check(witness.get("partition") == [3, 1], "partition_is_3_1")
    audit.check(witness.get("lattice_id") == "L_(3,1)^A3", "lattice_id_locked")
    audit.check(
        witness.get("lattice_basis") == ["e_1-e_4", "e_2-e_4", "e_3-e_4"],
        "lattice_basis_locked",
    )

    rebuilt: dict[str, dict[str, object]] = {}
    for row_name in ("X_A", "X_B"):
        row = witness.get(row_name)
        if not isinstance(row, dict):
            audit.check(False, f"{row_name}_present")
            continue
        try:
            words_data = row.get("words")
            if not isinstance(words_data, list):
                raise ValueError("words must be a list")
            words = [parse_word(word, 4) for word in words_data]
            audit.check(len(words) == len(set(words)) == 4, f"{row_name}_four_distinct_words")
            computed_histogram = histogram(words)
            computed_matrix = standard_lattice_matrix(words)
            computed_rank = rational_rank(computed_matrix)
            computed_determinantal = determinantal_divisors(computed_matrix)
            computed_smith = smith_divisors_from_determinantal(computed_determinantal)
            audit.check(row.get("class_histogram") == computed_histogram, f"{row_name}_histogram")
            audit.check(row.get("matrix") == computed_matrix, f"{row_name}_matrix")
            audit.check(row.get("rank_Q") == computed_rank, f"{row_name}_rank")
            audit.check(
                row.get("determinantal_divisors") == computed_determinantal,
                f"{row_name}_determinantal_divisors",
            )
            audit.check(row.get("snf_divisors") == computed_smith, f"{row_name}_snf")
            rebuilt[row_name] = {"histogram": computed_histogram}
        except (ArithmeticError, KeyError, TypeError, ValueError) as exc:
            audit.check(False, f"{row_name}_reconstruction", str(exc))

    if set(rebuilt) == {"X_A", "X_B"}:
        audit.check(
            rebuilt["X_A"]["histogram"] == rebuilt["X_B"]["histogram"],
            "same_class_histogram",
        )

    declared_checks = witness.get("checks")
    audit.check(
        isinstance(declared_checks, dict)
        and bool(declared_checks)
        and all(value is True for value in declared_checks.values()),
        "value_witness_declared_checks_true",
    )


def verify_rank_mass_rows(certificate: dict[str, object], audit: Audit) -> None:
    rows = certificate.get("type_a_rank_mass_rows")
    if not isinstance(rows, list) or not rows:
        audit.check(False, "rank_mass_rows_present")
        return

    representation_cache: dict[
        int, dict[Partition, tuple[int, dict[Permutation, RationalMatrix]]]
    ] = {}
    for row_data in rows:
        if not isinstance(row_data, dict):
            audit.check(False, "rank_mass_row_is_object")
            continue
        label = row_data.get("row")
        if not isinstance(label, str):
            audit.check(False, "rank_mass_row_label")
            continue
        try:
            n, fixed_hits, reversal_hits = parse_incidence_row(label)
            expected_partitions_data = row_data.get("partition_order")
            if not isinstance(expected_partitions_data, list):
                raise ValueError("partition_order must be a list")
            expected_partitions = [tuple(int(value) for value in part) for part in expected_partitions_data]
            canonical_partitions = integer_partitions(n)
            audit.check(expected_partitions == canonical_partitions, f"{label}_partition_order")

            if n not in representation_cache:
                representation_cache[n] = {}
                for partition in canonical_partitions:
                    dimension, matrices, relations_ok = all_representation_matrices(n, partition)
                    audit.check(relations_ok, f"S{n}_{partition}_representation_relations")
                    representation_cache[n][partition] = (dimension, matrices)

            layer = incidence_layer(n, fixed_hits, reversal_hits)
            dimensions: list[int] = []
            ranks: list[int] = []
            for partition in canonical_partitions:
                dimension, matrices = representation_cache[n][partition]
                block = zero_matrix(dimension)
                for word in layer:
                    matrix_add_in_place(block, matrices[word])
                dimensions.append(dimension)
                ranks.append(rational_rank(block))
            contributions = [dimension * rank for dimension, rank in zip(dimensions, ranks)]
            rank_mass = sum(contributions)

            audit.check(row_data.get("size") == len(layer), f"{label}_size")
            audit.check(row_data.get("dimensions") == dimensions, f"{label}_dimensions")
            audit.check(row_data.get("ranks_Q") == ranks, f"{label}_ranks")
            audit.check(
                row_data.get("weighted_contributions") == contributions,
                f"{label}_weighted_contributions",
            )
            audit.check(row_data.get("rank_mass") == rank_mass, f"{label}_rank_mass")
        except (ArithmeticError, KeyError, TypeError, ValueError) as exc:
            audit.check(False, f"{label}_reconstruction", str(exc))


def verify_certificate(certificate: object) -> Audit:
    audit = Audit()
    if not isinstance(certificate, dict):
        audit.check(False, "certificate_is_object")
        return audit

    audit.check(certificate.get("schema_version") == 1, "schema_version")
    audit.check(certificate.get("certificate_id") == "X13-TYPE-A-STATIC-001", "certificate_id")
    audit.check(certificate.get("claim_id") == "X13-001", "claim_id")
    status = certificate.get("status")
    audit.check(isinstance(status, str) and status.upper().startswith("PASS"), "status_pass")
    posture = certificate.get("verification_posture")
    audit.check(
        isinstance(posture, str) and "not_a_quantitative_route" in posture,
        "nonroute_posture",
    )

    conventions = certificate.get("conventions")
    audit.check(
        isinstance(conventions, dict)
        and all(
            key in conventions
            for key in ("permutation_words", "action", "incidence_layer", "rank_mass")
        ),
        "conventions_present",
    )

    verify_value_witness(certificate, audit)
    verify_rank_mass_rows(certificate, audit)

    declared_checks = certificate.get("checks")
    audit.check(
        isinstance(declared_checks, dict)
        and bool(declared_checks)
        and all(
            (value is True if key != "creates_thirteenth_quantitative_route" else value is False)
            for key, value in declared_checks.items()
        ),
        "outer_declared_checks_consistent",
    )
    boundary = certificate.get("boundary")
    audit.check(
        isinstance(boundary, str)
        and "no tiling" in boundary
        and "classification" in boundary
        and "family-wide" in boundary,
        "boundary_present",
    )
    return audit


def main() -> int:
    started = perf_counter()
    try:
        raw = CERTIFICATE.read_text(encoding="utf-8")
        certificate = json.loads(raw)
        audit = verify_certificate(certificate)
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        print(f"{FAIL_MARKER} checks=0/1 runtime_seconds={perf_counter() - started:.3f}")
        print(f"certificate_load: {exc}")
        return 1

    elapsed = perf_counter() - started
    if audit.failures:
        print(f"{FAIL_MARKER} checks={audit.passed}/{audit.total} runtime_seconds={elapsed:.3f}")
        for failure in audit.failures:
            print(f"- {failure}")
        return 1

    print(f"{PASS_MARKER} checks={audit.passed}/{audit.total} runtime_seconds={elapsed:.3f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
