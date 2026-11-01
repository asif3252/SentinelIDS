import unittest
import numpy as np
from sentinel import demo, train, predict, validate, FEATURES

class PipelineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.model, cls.report, cls.cm, cls.importance, cls.splits = train(demo(600))

    def test_reserved_test_and_probability(self):
        self.assertEqual(self.cm.sum(), self.splits['test'])
        result = predict(self.model, demo(50, 99).drop(columns='label'))
        self.assertTrue(result.attack_score.between(0, 1).all())
        self.assertEqual(len(result), 50)

    def test_threshold_monotonicity(self):
        data = demo(100, 98)
        self.assertGreaterEqual(predict(self.model, data, .2).alert.sum(), predict(self.model, data, .8).alert.sum())

    def test_reject_bad_schema_and_infinity(self):
        with self.assertRaises(ValueError):
            validate(demo(20).drop(columns=[FEATURES[0]]))
        data = demo(20)
        data.loc[0, 'bytes'] = np.inf
        with self.assertRaises(ValueError):
            validate(data)

    def test_unknown_labels(self):
        data = demo(100)
        data.loc[0, 'label'] = 'UNKNOWN'
        with self.assertRaises(ValueError):
            validate(data, True)

if __name__ == '__main__':
    unittest.main()
