"""
Video Embed Sanitizer - Validates and sanitizes video embed URLs
Only allows whitelisted video platforms for security
"""
from urllib.parse import urlparse, parse_qs

# Whitelisted video platforms
ALLOWED_VIDEO_DOMAINS = [
    # YouTube
    'youtube.com',
    'www.youtube.com',
    'youtu.be',
    'www.youtube-nocookie.com',
    # Vimeo
    'vimeo.com',
    'player.vimeo.com',
    # PeerTube instances (common ones - can be extended via config)
    'framatube.org',
    'peertube.social',
    'video.ploud.fr',
    'tube.tchncs.de',
]

# Additional PeerTube domains can be loaded from environment/config
PEERTUBE_DOMAINS: list[str] = []


def is_allowed_domain(url):
    """Check if URL domain is in the whitelist"""
    try:
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        
        # Remove port if present
        if ':' in domain:
            domain = domain.split(':')[0]
        
        # Check against whitelist
        if domain in ALLOWED_VIDEO_DOMAINS:
            return True
        
        # Check PeerTube domains
        if domain in PEERTUBE_DOMAINS:
            return True
        
        # Allow subdomains of whitelisted domains
        for allowed in ALLOWED_VIDEO_DOMAINS + PEERTUBE_DOMAINS:
            if domain.endswith('.' + allowed):
                return True
        
        return False
    except Exception:
        return False


def get_video_platform(url):
    """Detect the video platform from URL"""
    try:
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        
        if 'youtube' in domain or 'youtu.be' in domain:
            return 'youtube'
        elif 'vimeo' in domain:
            return 'vimeo'
        else:
            # Assume PeerTube for other allowed domains
            return 'peertube'
    except Exception:
        return None


def extract_youtube_id(url):
    """Extract YouTube video ID from various URL formats"""
    try:
        parsed = urlparse(url)
        
        # youtu.be/VIDEO_ID
        if 'youtu.be' in parsed.netloc:
            return parsed.path.strip('/')
        
        # youtube.com/watch?v=VIDEO_ID
        if 'v' in parse_qs(parsed.query):
            return parse_qs(parsed.query)['v'][0]
        
        # youtube.com/embed/VIDEO_ID
        if '/embed/' in parsed.path:
            return parsed.path.split('/embed/')[1].split('/')[0].split('?')[0]
        
        # youtube.com/v/VIDEO_ID
        if '/v/' in parsed.path:
            return parsed.path.split('/v/')[1].split('/')[0].split('?')[0]
        
        return None
    except Exception:
        return None


def extract_vimeo_id(url):
    """Extract Vimeo video ID from URL"""
    try:
        parsed = urlparse(url)
        
        # vimeo.com/VIDEO_ID
        path_parts = parsed.path.strip('/').split('/')
        for part in path_parts:
            if part.isdigit():
                return part
        
        return None
    except Exception:
        return None


def get_embed_url(url):
    """
    Convert a video URL to its embeddable version.
    Returns None if URL is not from an allowed domain.
    """
    if not url or not is_allowed_domain(url):
        return None
    
    platform = get_video_platform(url)
    
    if platform == 'youtube':
        video_id = extract_youtube_id(url)
        if video_id:
            # Use youtube-nocookie for privacy
            return f'https://www.youtube-nocookie.com/embed/{video_id}'
    
    elif platform == 'vimeo':
        video_id = extract_vimeo_id(url)
        if video_id:
            return f'https://player.vimeo.com/video/{video_id}'
    
    elif platform == 'peertube':
        # PeerTube embeds use /videos/embed/ path
        if '/videos/watch/' in url:
            video_path = url.replace('/videos/watch/', '/videos/embed/')
            return video_path
        elif '/w/' in url:
            # Short URL format
            video_path = url.replace('/w/', '/videos/embed/')
            return video_path
        # Already an embed URL
        if '/videos/embed/' in url:
            return url
    
    return None


def sanitize_video_data(videos_list):
    """
    Sanitize a list of video entries.
    Each entry should have: title, embed_url, platform
    Returns sanitized list with only valid entries.
    """
    sanitized = []
    
    for video in videos_list:
        if not isinstance(video, dict):
            continue
        
        title = video.get('title', '').strip()
        url = video.get('embed_url', '').strip()
        
        if not title or not url:
            continue
        
        # Try to get embed URL
        embed_url = get_embed_url(url)
        
        if embed_url:
            sanitized.append({
                'title': title[:200],  # Limit title length
                'embed_url': embed_url,
                'platform': get_video_platform(url)
            })
    
    return sanitized


def validate_video_url(url):
    """
    Validate a single video URL.
    Returns (is_valid, embed_url, platform, error_message)
    """
    if not url:
        return False, None, None, 'URL is required'
    
    url = url.strip()
    
    if not is_allowed_domain(url):
        return False, None, None, 'Video platform not allowed. Supported: YouTube, Vimeo, PeerTube'
    
    platform = get_video_platform(url)
    embed_url = get_embed_url(url)
    
    if not embed_url:
        return False, None, platform, 'Could not extract video ID from URL'
    
    return True, embed_url, platform, None


def add_peertube_domain(domain):
    """Add a PeerTube instance domain to the whitelist"""
    domain = domain.lower().strip()
    if domain and domain not in PEERTUBE_DOMAINS:
        PEERTUBE_DOMAINS.append(domain)
        return True
    return False
