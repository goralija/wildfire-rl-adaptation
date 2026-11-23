from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import tempfile
import unittest

from wildfire_rl.feds_simfire_setup import prepare_output_directory


class SimFireOutputDirectoryTests(unittest.TestCase):
    def test_simultaneous_fresh_initializers_and_repeated_calls_do_not_race(self):
        with tempfile.TemporaryDirectory() as d:
            target=Path(d)/'nested'/'new-output'
            config={'simulation':{'sf_home':str(target)}}
            with ThreadPoolExecutor(max_workers=4) as pool:
                results=list(pool.map(prepare_output_directory,[config]*16))
            self.assertTrue(target.is_dir())
            self.assertTrue(all(path==target for path in results))
            sentinel=target/'existing-result';sentinel.write_text('preserve')
            prepare_output_directory(config)
            self.assertEqual(sentinel.read_text(),'preserve')

if __name__=='__main__':unittest.main()
