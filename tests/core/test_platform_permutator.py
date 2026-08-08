import unittest

from osint_nexus.core.platform_permutator import PlatformPermutator


class TestPlatformPermutator(unittest.TestCase):
    def setUp(self) -> None:
        self.permutator = PlatformPermutator()

    def test_generate_variations(self) -> None:
        platforms = ["example"]
        variations = self.permutator.generate(platforms)

        # Check if some expected variations exist
        self.assertIn("example.com", variations)
        self.assertIn("app.example", variations)
        self.assertIn("api.example", variations)
        self.assertIn("m.example", variations)
        self.assertIn("graphql.example", variations)
        self.assertIn("old.example", variations)
        self.assertIn("cdn.example", variations)


if __name__ == "__main__":
    unittest.main()
