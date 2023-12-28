# SPDX-FileCopyrightText: 2022 James R. Barlow
# SPDX-License-Identifier: CC0-1.0

from __future__ import annotations

import pickle
from math import isclose

import pytest

from pikepdf import Array
from pikepdf._core import Matrix, Rectangle
from pikepdf.models import PdfMatrix
from pikepdf.objects import Dictionary


def allclose(m1, m2, abs_tol=1e-6):
    return all(
        isclose(x, y, abs_tol=abs_tol) for x, y in zip(m1.shorthand, m2.shorthand)
    )


@pytest.mark.filterwarnings("ignore::DeprecationWarning")
class TestOldPdfMatrix:
    def test_init_6(self):
        m = PdfMatrix(1, 0, 0, 1, 0, 0)
        m2 = m.scaled(2, 2)
        m2t = m2.translated(2, 3)
        # This is the wrong result,
        assert (
            repr(m2t)
            == "pikepdf.PdfMatrix(((2.0, 0.0, 0.0), (0.0, 2.0, 0.0), (2.0, 3.0, 1.0)))"
        )
        m2tr = m2t.rotated(90)
        expected = PdfMatrix(0, 2, -2, 0, -3, 2)
        assert allclose(m2tr, expected)

    def test_invalid_init(self):
        with pytest.raises(ValueError, match="arguments"):
            PdfMatrix("strings")

    def test_matrix_from_matrix(self):
        m = PdfMatrix(1, 0, 0, 1, 0, 0)
        m_copy = PdfMatrix(m)
        assert m == m_copy
        assert m != "not matrix"

    def test_matrix_encode(self):
        m = PdfMatrix(1, 0, 0, 1, 0, 0)
        assert m.encode() == b"1.000000 0.000000 0.000000 1.000000 0.000000 0.000000"

    def test_matrix_inverse(self):
        _np = pytest.importorskip("numpy")
        m = PdfMatrix(2, 0, 0, 1, 0, 3)
        minv_m = m.inverse() @ m
        assert allclose(minv_m, PdfMatrix.identity())

    def test_numpy(self):
        np = pytest.importorskip("numpy")

        m = PdfMatrix(1, 0, 0, 2, 7, 0)
        m2 = PdfMatrix(np.array([[1, 0, 0], [0, 2, 0], [7, 0, 1]]))
        assert m == m2
        arr = np.array(m)
        arr2 = np.array(m2)
        assert np.array_equal(arr, arr2)


class TestMatrix:
    def test_default_is_identity(self):
        assert Matrix() == Matrix(1, 0, 0, 1, 0, 0)

    def test_not_enough_args(self):
        with pytest.raises(TypeError):
            Matrix(1, 2, 3, 4, 5)

    def test_tuple(self):
        assert Matrix() == Matrix((1, 0, 0, 1, 0, 0))
        with pytest.raises(ValueError):
            Matrix((1, 2, 3, 4, 5))

    def test_failed_object_conversion(self):
        with pytest.raises(ValueError):
            assert Matrix(Array([1, 2, 3]))
        with pytest.raises(ValueError):
            assert Matrix(Dictionary(Foo=1))

    def test_accessors(self):
        m = Matrix(1, 2, 3, 4, 5, 6)
        assert m.a == 1
        assert m.b == 2
        assert m.c == 3
        assert m.d == 4
        assert m.e == 5
        assert m.f == 6

    def test_init(self):
        m = Matrix()
        m2 = m.scaled(2, 2)
        m2t = m2.translated(2, 3)
        assert repr(m2t) == "pikepdf.Matrix(2, 0, 0, 2, 4, 6)"
        m2tr = m2t.rotated(90)
        expected = Matrix(0, 2, -2, 0, 4, 6)
        assert allclose(m2tr, expected)

    def test_matmul(self):
        m = Matrix()
        scale = Matrix().scaled(3, 3)
        translate = Matrix().translated(10, 10)
        assert allclose(translate @ scale @ m, Matrix(3, 0, 0, 3, 30, 30))
        assert allclose(scale @ translate @ m, Matrix(3, 0, 0, 3, 10, 10))
        assert allclose(m.scaled(3, 3).translated(10, 10), Matrix(3, 0, 0, 3, 30, 30))

    def test_inverse(self):
        m = Matrix().rotated(45)
        minv_m = m.inverse() @ m
        assert allclose(minv_m, Matrix())

    def test_non_invertible(self):
        m = Matrix(4, 4, 4, 4, 0, 0)
        with pytest.raises(ValueError, match="not invertible"):
            m.inverse()

    def test_numpy(self):
        np = pytest.importorskip("numpy")

        m = Matrix(1, 0, 0, 2, 7, 0)
        a = np.array([[1, 0, 0], [0, 2, 0], [7, 0, 1]])
        arr = np.array(m)
        assert np.array_equal(arr, a)

    def test_bool(self):
        with pytest.raises(ValueError):
            bool(Matrix(1, 0, 0, 1, 0, 0))

    def test_pickle(self):
        assert Matrix(1, 0, 0, 1, 42, 0) == pickle.loads(
            pickle.dumps(Matrix(1, 0, 0, 1, 42, 0))
        )

    def test_encode(self):
        assert Matrix((1, 2, 3, 4, 0, 0)).encode() == b"1 2 3 4 0 0"

    def test_from_object_array(self):
        assert Matrix(Array([1, 2, 3, 4, 5, 6])).shorthand == (1, 2, 3, 4, 5, 6)

    def test_transform_point(self):
        m = Matrix(1, 0, 0, 1, 0, 0)
        assert m.transform((0, 0)) == (0, 0)
        assert m.transform((1, 1)) == (1, 1)
        m = Matrix(2, 0, 0, 2, 0, 1)
        assert m.transform((0, 0)) == (0, 1)
        assert m.transform((1, 1)) == (2, 3)

    def test_transform_rect(self):
        m = Matrix(2, 0, 0, 2, 1, 1)
        assert m.transform(Rectangle(0, 0, 1, 1)) == Rectangle(1, 1, 3, 3)

    def test_rotated_ccw(self):
        m = Matrix().rotated(45)
        assert (0, 0) < m.transform((1, 0)) < (1, 1)
        m = Matrix().rotated(-45)
        assert (0, 0) < m.transform((1, 0)) < (1, -1)

    def test_latex(self):
        assert "\\begin" in Matrix(1, 0, 0, 1, 0, 0)._repr_latex_()
