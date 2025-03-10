"""
ANN module tests
"""

import os
import tempfile
import unittest

import numpy as np

from txtai.ann import ANNFactory, ANN


class TestANN(unittest.TestCase):
    """
    ANN tests.
    """

    def testAnnoy(self):
        """
        Test Annoy backend
        """

        self.runTests("annoy", None, False)

    def testAnnoyCustom(self):
        """
        Test Annoy backend with custom settings
        """

        # Test with custom settings
        self.runTests("annoy", {"annoy": {"ntrees": 2, "searchk": 1}}, False)

    def testFaiss(self):
        """
        Test Faiss backend
        """

        self.runTests("faiss")

    def testFaissCustom(self):
        """
        Test Faiss backend with custom settings
        """

        # Test with custom settings
        self.runTests("faiss", {"faiss": {"nprobe": 2, "components": "PCA16,IDMap,SQ8"}}, False)

    @unittest.skipIf(os.name == "nt", "mmap not supported on Windows")
    def testFaissMmap(self):
        """
        Test Faiss backend with mmap enabled
        """

        # Test to with mmap enabled
        self.runTests("faiss", {"faiss": {"mmap": True}}, False)

    def testHnsw(self):
        """
        Test Hnswlib backend
        """

        self.runTests("hnsw")

    def testHnswCustom(self):
        """
        Test Hnswlib backend with custom settings
        """

        # Test with custom settings
        self.runTests("hnsw", {"hnsw": {"efconstruction": 100, "m": 4, "randomseed": 0, "efsearch": 5}})

    def testNotImplemented(self):
        """
        Tests exceptions for non-implemented methods
        """

        ann = ANN({})

        self.assertRaises(NotImplementedError, ann.load, None)
        self.assertRaises(NotImplementedError, ann.index, None)
        self.assertRaises(NotImplementedError, ann.append, None)
        self.assertRaises(NotImplementedError, ann.delete, None)
        self.assertRaises(NotImplementedError, ann.search, None, None)
        self.assertRaises(NotImplementedError, ann.count)
        self.assertRaises(NotImplementedError, ann.save, None)

    def runTests(self, name, params=None, update=True):
        """
        Runs a series of standard backend tests.

        Args:
            name: backend name
            params: additional config parameters
            update: If append/delete options should be tested
        """

        self.assertEqual(self.backend(name, params).config["backend"], name)
        self.assertEqual(self.save(name, params).count(), 10000)

        if update:
            self.assertEqual(self.append(name, params, 500).count(), 10500)
            self.assertEqual(self.delete(name, params, [0, 1]).count(), 9998)
            self.assertEqual(self.delete(name, params, [100000]).count(), 10000)

        self.assertGreater(self.search(name, params), 0)

    def backend(self, name, params=None, length=10000):
        """
        Test a backend.

        Args:
            name: backend name
            params: additional config parameters
            length: number of rows to generate

        Returns:
            ANN model
        """

        # Generate test data
        data = np.random.rand(length, 300).astype(np.float32)
        self.normalize(data)

        config = {"backend": name, "dimensions": data.shape[1]}
        if params:
            config.update(params)

        model = ANNFactory.create(config)
        model.index(data)

        return model

    def append(self, name, params=None, length=500):
        """
        Appends new data to index.

        Args:
            name: backend name
            params: additional config parameters
            length: number of rows to generate

        Returns:
            ANN model
        """

        # Initial model
        model = self.backend(name, params)

        # Generate test data
        data = np.random.rand(length, 300).astype(np.float32)
        self.normalize(data)

        model.append(data)

        return model

    def delete(self, name, params=None, ids=None):
        """
        Deletes data from index.

        Args:
            name: backend name
            params: additional config parameters
            ids: ids to delete

        Returns:
            ANN model
        """

        # Initial model
        model = self.backend(name, params)
        model.delete(ids)

        return model

    def save(self, name, params=None):
        """
        Test save/load.

        Args:
            name: backend name
            params: additional config parameters

        Returns:
            ANN model
        """

        model = self.backend(name, params)

        # Generate temp file path
        index = os.path.join(tempfile.gettempdir(), "ann")

        model.save(index)
        model.load(index)

        return model

    def search(self, name, params=None):
        """
        Test ANN search.

        Args:
            name: backend name
            params: additional config parameters

        Returns:
            search results
        """

        # Generate ANN index
        model = self.backend(name, params)

        # Generate query vector
        query = np.random.rand(300).astype(np.float32)
        self.normalize(query)

        # Ensure top result has similarity > 0
        return model.search(np.array([query]), 1)[0][0][1]

    def normalize(self, embeddings):
        """
        Normalizes embeddings using L2 normalization. Operation applied directly on array.

        Args:
            embeddings: input embeddings matrix
        """

        # Calculation is different for matrices vs vectors
        if len(embeddings.shape) > 1:
            embeddings /= np.linalg.norm(embeddings, axis=1)[:, np.newaxis]
        else:
            embeddings /= np.linalg.norm(embeddings)
