"""
Regression tests for profile import JSON path resolution.
"""

import scripts.import_profile_data as profile_import


def test_profile_import_resolver_prefers_data_directory(tmp_path, monkeypatch):
    data_dir = tmp_path / 'data'
    data_dir.mkdir()

    preferred = data_dir / 'about_info.json'
    legacy = tmp_path / 'about_info.json'
    preferred.write_text('{"source": "data"}', encoding='utf-8')
    legacy.write_text('{"source": "legacy"}', encoding='utf-8')

    monkeypatch.setattr(profile_import, 'REPO_ROOT', tmp_path)
    monkeypatch.setattr(profile_import, 'DATA_DIR', data_dir)

    assert profile_import.resolve_profile_data_file('about_info.json') == preferred


def test_profile_import_resolver_falls_back_to_legacy_root(tmp_path, monkeypatch):
    data_dir = tmp_path / 'data'
    data_dir.mkdir()

    legacy = tmp_path / 'contact_info.json'
    legacy.write_text('{"source": "legacy"}', encoding='utf-8')

    monkeypatch.setattr(profile_import, 'REPO_ROOT', tmp_path)
    monkeypatch.setattr(profile_import, 'DATA_DIR', data_dir)

    assert profile_import.resolve_profile_data_file('contact_info.json') == legacy


def test_profile_import_resolver_returns_none_when_missing(tmp_path, monkeypatch):
    data_dir = tmp_path / 'data'
    data_dir.mkdir()

    monkeypatch.setattr(profile_import, 'REPO_ROOT', tmp_path)
    monkeypatch.setattr(profile_import, 'DATA_DIR', data_dir)

    assert profile_import.resolve_profile_data_file('missing.json') is None
