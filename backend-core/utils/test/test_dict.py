from unittest import TestCase
from utils.dict import rename_key


class DictRenameKeyTestCase(TestCase):
    def test_rename_key(self):
        data = {'a': 1, 2: 2, (0, ): 3}
        self.assertEqual(rename_key(data.copy(), 'a', 'b'), {'b': 1, 2: 2, (0, ): 3})
        self.assertEqual(rename_key(data.copy(), 2, 3), {'a': 1, 3: 2, (0, ): 3})
        self.assertEqual(rename_key(data.copy(), (0, ), (1, )), {'a': 1, 2: 2, (1, ): 3})
