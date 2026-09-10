import json

from meridian.cancellation.recipes.catalog import load_catalog, match_recipe


def test_recipe_matching_is_normalized_and_unverified_is_not_executable(tmp_path):
    (tmp_path / "example.json").write_text(json.dumps({
        "merchant": "Example, Inc.",
        "aliases": ["Example Plus"],
        "channel": "live_browser",
        "steps": ["open settings", "select cancel"],
        "last_verified": None,
    }))
    catalog = load_catalog(tmp_path)
    recipe = match_recipe("example plus", catalog)
    assert recipe is not None
    assert recipe.executable is False


def test_unknown_merchant_does_not_guess(tmp_path):
    assert match_recipe("Unknown", load_catalog(tmp_path)) is None
