import unittest
import program_options
import sys

class TestProgramOptions(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        while len(sys.argv) > 1:
            sys.argv.pop()

    def test_save_file(self):

        save_file = '~/.focustree.save.json'

        sys.argv.append('--save-file')
        sys.argv.append(save_file)

        opts = program_options.get_options()

        self.assertEqual(opts.save_file, save_file)

    def test_port(self):

        port = 1234
        sys.argv.append('--port')
        sys.argv.append(str(port))
        opts = program_options.get_options()

        self.assertEqual(opts.port, port)