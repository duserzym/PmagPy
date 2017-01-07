"""
tests for magic_gui
"""

import wx
import unittest
import os
#import dialogs.pmag_widgets as pmag_widgets
from pmagpy import new_builder as nb
from pmagpy import data_model3 as data_model
from pmagpy import controlled_vocabularies3 as cv3

# set constants
DMODEL = data_model.DataModel()
WD = os.getcwd()
PROJECT_WD = os.path.join(WD, "data_files", "magic_gui", "3_0")


class TestVocabularies(unittest.TestCase):

    def setUp(self):
        self.vocab = cv3.Vocabulary()
        self.vocab.get_all_vocabulary()

    def tearDown(self):
        pass

    def test_vocabularies(self):
        self.assertIn('timescale_era', self.vocab.vocabularies.index)
        self.assertIn('Neoproterozoic', self.vocab.vocabularies.ix['timescale_era'])

    def test_suggested(self):
        self.assertIn('fossil_class', self.vocab.suggested.index)
        self.assertIn('Anthozoa', self.vocab.suggested.ix['fossil_class'])


    def test_methods(self):
        self.assertIn('sample_preparation', self.vocab.methods.keys())
        for item in self.vocab.methods['sample_preparation']:
            self.assertTrue(item.startswith('SP-'))

    def test_all_codes(self):
        self.assertIn('SM-TTEST', self.vocab.all_codes.index)
        self.assertEqual('statistical_method',
                         self.vocab.all_codes.ix['SM-TTEST']['dtype'])