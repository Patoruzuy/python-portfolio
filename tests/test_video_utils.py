"""
Tests for video utilities - URL validation, embed generation, and sanitization.
"""
import pytest
from utils import video_utils


class TestDomainValidation:
    """Test domain whitelisting and validation."""
    
    def test_is_allowed_domain_youtube(self):
        """Should allow YouTube domains."""
        assert video_utils.is_allowed_domain('https://www.youtube.com/watch?v=abc')
        assert video_utils.is_allowed_domain('https://youtube.com/watch?v=abc')
        assert video_utils.is_allowed_domain('https://youtu.be/abc')
        assert video_utils.is_allowed_domain('https://www.youtube-nocookie.com/embed/abc')
    
    def test_is_allowed_domain_vimeo(self):
        """Should allow Vimeo domains."""
        assert video_utils.is_allowed_domain('https://vimeo.com/123456')
        assert video_utils.is_allowed_domain('https://player.vimeo.com/video/123456')
    
    def test_is_allowed_domain_peertube(self):
        """Should allow PeerTube domains."""
        assert video_utils.is_allowed_domain('https://framatube.org/videos/watch/abc')
        assert video_utils.is_allowed_domain('https://peertube.social/w/abc')
    
    def test_is_allowed_domain_rejects_unknown(self):
        """Should reject non-whitelisted domains."""
        assert not video_utils.is_allowed_domain('https://malicious-site.com/video')
        assert not video_utils.is_allowed_domain('https://evil.com/embed')
    
    def test_is_allowed_domain_handles_ports(self):
        """Should handle URLs with port numbers."""
        assert video_utils.is_allowed_domain('https://youtube.com:443/watch?v=abc')
    
    def test_is_allowed_domain_handles_invalid_url(self):
        """Should handle malformed URLs gracefully."""
        assert not video_utils.is_allowed_domain('not a url')
        assert not video_utils.is_allowed_domain('')


class TestPlatformDetection:
    """Test video platform identification."""
    
    def test_get_video_platform_youtube(self):
        """Should detect YouTube platform."""
        assert video_utils.get_video_platform('https://youtube.com/watch?v=abc') == 'youtube'
        assert video_utils.get_video_platform('https://youtu.be/abc') == 'youtube'
    
    def test_get_video_platform_vimeo(self):
        """Should detect Vimeo platform."""
        assert video_utils.get_video_platform('https://vimeo.com/123456') == 'vimeo'
        assert video_utils.get_video_platform('https://player.vimeo.com/video/123') == 'vimeo'
    
    def test_get_video_platform_peertube(self):
        """Should detect PeerTube platform."""
        assert video_utils.get_video_platform('https://framatube.org/videos/watch/abc') == 'peertube'
    
    def test_get_video_platform_handles_invalid(self):
        """Should return 'peertube' as fallback for unknown platforms."""
        # Function returns 'peertube' for non-YouTube/Vimeo URLs
        assert video_utils.get_video_platform('not a url') == 'peertube'


class TestYouTubeExtraction:
    """Test YouTube video ID extraction."""
    
    def test_extract_youtube_id_watch_url(self):
        """Should extract ID from standard watch URL."""
        video_id = video_utils.extract_youtube_id('https://www.youtube.com/watch?v=dQw4w9WgXcQ')
        assert video_id == 'dQw4w9WgXcQ'
    
    def test_extract_youtube_id_short_url(self):
        """Should extract ID from short youtu.be URL."""
        video_id = video_utils.extract_youtube_id('https://youtu.be/dQw4w9WgXcQ')
        assert video_id == 'dQw4w9WgXcQ'
    
    def test_extract_youtube_id_embed_url(self):
        """Should extract ID from embed URL."""
        video_id = video_utils.extract_youtube_id('https://www.youtube.com/embed/dQw4w9WgXcQ')
        assert video_id == 'dQw4w9WgXcQ'
    
    def test_extract_youtube_id_v_url(self):
        """Should extract ID from /v/ URL format."""
        video_id = video_utils.extract_youtube_id('https://www.youtube.com/v/dQw4w9WgXcQ')
        assert video_id == 'dQw4w9WgXcQ'
    
    def test_extract_youtube_id_with_params(self):
        """Should extract ID ignoring other parameters."""
        video_id = video_utils.extract_youtube_id('https://www.youtube.com/watch?v=abc123&t=30s')
        assert video_id == 'abc123'
    
    def test_extract_youtube_id_invalid_url(self):
        """Should return None for invalid URLs."""
        assert video_utils.extract_youtube_id('https://youtube.com/invalid') is None
        assert video_utils.extract_youtube_id('not a url') is None


class TestVimeoExtraction:
    """Test Vimeo video ID extraction."""
    
    def test_extract_vimeo_id_standard_url(self):
        """Should extract ID from standard Vimeo URL."""
        video_id = video_utils.extract_vimeo_id('https://vimeo.com/123456789')
        assert video_id == '123456789'
    
    def test_extract_vimeo_id_player_url(self):
        """Should extract ID from player URL."""
        video_id = video_utils.extract_vimeo_id('https://player.vimeo.com/video/123456789')
        assert video_id == '123456789'
    
    def test_extract_vimeo_id_with_path(self):
        """Should extract ID from URL with additional path."""
        video_id = video_utils.extract_vimeo_id('https://vimeo.com/channels/staffpicks/123456')
        assert video_id == '123456'
    
    def test_extract_vimeo_id_invalid_url(self):
        """Should return None for invalid URLs."""
        assert video_utils.extract_vimeo_id('https://vimeo.com/invalid') is None
        assert video_utils.extract_vimeo_id('not a url') is None


class TestEmbedUrlGeneration:
    """Test embed URL generation."""
    
    def test_get_embed_url_youtube(self):
        """Should generate YouTube nocookie embed URL."""
        embed = video_utils.get_embed_url('https://www.youtube.com/watch?v=dQw4w9WgXcQ')
        assert embed == 'https://www.youtube-nocookie.com/embed/dQw4w9WgXcQ'
    
    def test_get_embed_url_youtube_short(self):
        """Should generate embed URL from short YouTube URL."""
        embed = video_utils.get_embed_url('https://youtu.be/abc123')
        assert embed == 'https://www.youtube-nocookie.com/embed/abc123'
    
    def test_get_embed_url_vimeo(self):
        """Should generate Vimeo player embed URL."""
        embed = video_utils.get_embed_url('https://vimeo.com/123456789')
        assert embed == 'https://player.vimeo.com/video/123456789'
    
    def test_get_embed_url_peertube_watch(self):
        """Should convert PeerTube watch URL to embed."""
        embed = video_utils.get_embed_url('https://framatube.org/videos/watch/abc-123')
        assert '/videos/embed/abc-123' in embed
    
    def test_get_embed_url_peertube_short(self):
        """Should convert PeerTube short /w/ URL to embed."""
        embed = video_utils.get_embed_url('https://peertube.social/w/xyz')
        assert '/videos/embed/xyz' in embed
    
    def test_get_embed_url_peertube_already_embed(self):
        """Should return PeerTube embed URL as-is."""
        url = 'https://framatube.org/videos/embed/abc-123'
        embed = video_utils.get_embed_url(url)
        assert embed == url
    
    def test_get_embed_url_rejects_disallowed_domain(self):
        """Should return None for non-whitelisted domains."""
        assert video_utils.get_embed_url('https://malicious.com/video') is None
    
    def test_get_embed_url_handles_empty_url(self):
        """Should handle empty/None URLs."""
        assert video_utils.get_embed_url('') is None
        assert video_utils.get_embed_url(None) is None


class TestVideoValidation:
    """Test video URL validation function."""
    
    def test_validate_video_url_youtube_success(self):
        """Should validate YouTube URL successfully."""
        is_valid, embed_url, platform, error = video_utils.validate_video_url(
            'https://www.youtube.com/watch?v=abc123'
        )
        assert is_valid is True
        assert embed_url == 'https://www.youtube-nocookie.com/embed/abc123'
        assert platform == 'youtube'
        assert error is None
    
    def test_validate_video_url_vimeo_success(self):
        """Should validate Vimeo URL successfully."""
        is_valid, embed_url, platform, error = video_utils.validate_video_url(
            'https://vimeo.com/123456'
        )
        assert is_valid is True
        assert 'player.vimeo.com' in embed_url
        assert platform == 'vimeo'
        assert error is None
    
    def test_validate_video_url_empty(self):
        """Should reject empty URL."""
        is_valid, embed_url, platform, error = video_utils.validate_video_url('')
        assert is_valid is False
        assert 'required' in error
    
    def test_validate_video_url_disallowed_domain(self):
        """Should reject non-whitelisted domains."""
        is_valid, embed_url, platform, error = video_utils.validate_video_url(
            'https://evil.com/video'
        )
        assert is_valid is False
        assert 'not allowed' in error
    
    def test_validate_video_url_invalid_format(self):
        """Should reject invalid video URL format."""
        is_valid, embed_url, platform, error = video_utils.validate_video_url(
            'https://youtube.com/invalid-path'
        )
        assert is_valid is False
        assert 'Could not extract' in error


class TestVideoSanitization:
    """Test video list sanitization."""
    
    def test_sanitize_video_data_valid_list(self):
        """Should sanitize valid video list."""
        videos = [
            {'title': 'Test Video 1', 'embed_url': 'https://youtube.com/watch?v=abc'},
            {'title': 'Test Video 2', 'embed_url': 'https://vimeo.com/123'}
        ]
        
        sanitized = video_utils.sanitize_video_data(videos)
        assert len(sanitized) == 2
        assert sanitized[0]['title'] == 'Test Video 1'
        assert 'youtube-nocookie' in sanitized[0]['embed_url']
        assert sanitized[0]['platform'] == 'youtube'
    
    def test_sanitize_video_data_filters_invalid(self):
        """Should filter out invalid entries."""
        videos = [
            {'title': 'Valid', 'embed_url': 'https://youtube.com/watch?v=abc'},
            {'title': '', 'embed_url': 'https://youtube.com/watch?v=def'},  # Empty title
            {'title': 'No URL'},  # Missing embed_url
            {'title': 'Bad Domain', 'embed_url': 'https://evil.com/video'},  # Invalid domain
            'not a dict'  # Invalid type
        ]
        
        sanitized = video_utils.sanitize_video_data(videos)
        assert len(sanitized) == 1
        assert sanitized[0]['title'] == 'Valid'
    
    def test_sanitize_video_data_limits_title_length(self):
        """Should limit title length to 200 characters."""
        long_title = 'A' * 300
        videos = [{'title': long_title, 'embed_url': 'https://youtube.com/watch?v=abc'}]
        
        sanitized = video_utils.sanitize_video_data(videos)
        assert len(sanitized[0]['title']) == 200


class TestPeerTubeDomainManagement:
    """Test PeerTube domain whitelist management."""
    
    def test_add_peertube_domain_new(self):
        """Should add new PeerTube domain."""
        # Clear list first
        video_utils.PEERTUBE_DOMAINS.clear()
        
        result = video_utils.add_peertube_domain('custom-peertube.org')
        assert result is True
        assert 'custom-peertube.org' in video_utils.PEERTUBE_DOMAINS
    
    def test_add_peertube_domain_duplicate(self):
        """Should not add duplicate domain."""
        video_utils.PEERTUBE_DOMAINS.clear()
        video_utils.add_peertube_domain('test.org')
        
        result = video_utils.add_peertube_domain('test.org')
        assert result is False
        assert video_utils.PEERTUBE_DOMAINS.count('test.org') == 1
    
    def test_add_peertube_domain_normalizes(self):
        """Should normalize domain (lowercase, trim)."""
        video_utils.PEERTUBE_DOMAINS.clear()
        
        video_utils.add_peertube_domain('  UPPERCASE.ORG  ')
        assert 'uppercase.org' in video_utils.PEERTUBE_DOMAINS
    
    def test_add_peertube_domain_empty(self):
        """Should reject empty domain."""
        result = video_utils.add_peertube_domain('')
        assert result is False
