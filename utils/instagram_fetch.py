import os
import logging
import json
import asyncio
import re
from typing import Optional, Tuple, List, Dict, Any
from dataclasses import dataclass, asdict, field
from bs4 import BeautifulSoup

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class InstagramProfile:
    """Data class for Instagram profile information"""
    username: str
    full_name: str
    bio: str
    followers_count: int
    following_count: int
    media_count: int
    is_private: bool = False
    profile_pic_url: Optional[str] = None
    is_verified: bool = False
    followers: List[Dict[str, Any]] = field(default_factory=list)
    following: List[Dict[str, Any]] = field(default_factory=list)
    posts: List[Dict[str, Any]] = field(default_factory=list)
    data_source: str = "unknown"
    warnings: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert profile to dictionary"""
        return asdict(self)




def _normalise_username(username: Optional[str]) -> str:
    return (username or '').strip().lstrip('@').lower()


def _parse_count(value: Any) -> int:
    """Parse Instagram integer and abbreviated count values."""
    if isinstance(value, bool) or value is None:
        return 0
    if isinstance(value, (int, float)):
        return int(value)

    text = str(value).strip().replace(',', '')
    match = re.search(r'(\d+(?:\.\d+)?)\s*([KMB])?', text, re.IGNORECASE)
    if not match:
        return 0
    multiplier = {'k': 1_000, 'm': 1_000_000, 'b': 1_000_000_000}.get(
        (match.group(2) or '').lower(), 1
    )
    return int(float(match.group(1)) * multiplier)


def _explicit_media_count(user: Dict[str, Any]) -> Tuple[bool, int]:
    """Return whether a profile payload contains a parseable total post count."""
    for key in ('media_count', 'post_count', 'posts_count'):
        if key in user and _is_parseable_count(user.get(key)):
            return True, _parse_count(user.get(key))

    edge = user.get('edge_owner_to_timeline_media')
    if isinstance(edge, dict) and 'count' in edge and _is_parseable_count(edge.get('count')):
        count = _parse_count(edge.get('count'))
        if count == 0 and isinstance(edge.get('edges'), list):
            count = len(edge['edges'])
        return True, count
    return False, 0


def _is_parseable_count(value: Any) -> bool:
    if isinstance(value, bool) or value is None:
        return False
    if isinstance(value, (int, float)):
        return True
    return bool(re.search(r'\d+(?:\.\d+)?\s*[KMB]?', str(value).strip(), re.IGNORECASE))


def _edge_count(user: Dict[str, Any], rest_key: str, graphql_key: str) -> int:
    value = user.get(rest_key)
    if value is None:
        edge = user.get(graphql_key)
        if isinstance(edge, dict):
            value = edge.get('count')
            # Some Instagram responses report a zero count while still
            # including the loaded timeline edges.
            if _parse_count(value) == 0 and isinstance(edge.get('edges'), list):
                value = len(edge['edges'])
        else:
            value = edge
    return _parse_count(value)


def _find_profile_json(data: Any, expected_username: Optional[str]) -> Optional[Dict[str, Any]]:
    """Find a nested profile object, preferring an exact requested-username match."""
    expected = _normalise_username(expected_username)
    candidates: List[Dict[str, Any]] = []

    def visit(value: Any) -> None:
        if isinstance(value, dict):
            username = value.get('username')
            has_profile_fields = any(key in value for key in (
                'biography', 'full_name', 'follower_count', 'following_count',
                'media_count', 'post_count', 'posts_count',
                'edge_followed_by', 'edge_follow',
                'edge_owner_to_timeline_media',
            ))
            if isinstance(username, str) and has_profile_fields:
                candidates.append(value)
            for child in value.values():
                visit(child)
        elif isinstance(value, list):
            for child in value:
                visit(child)

    visit(data)
    if expected:
        matching = [candidate for candidate in candidates
                    if _normalise_username(candidate.get('username')) == expected]
        if matching:
            # Instagram may embed several copies of the profile. Prefer a
            # matching object that actually carries the total post count,
            # then prefer the richest copy while retaining document order for
            # otherwise identical candidates.
            return max(
                matching,
                key=lambda candidate: (
                    _explicit_media_count(candidate)[0],
                    len(candidate),
                ),
            )
        return None
    return candidates[0] if candidates else None


def _meta_profile(soup: BeautifulSoup, expected_username: Optional[str]) -> Optional[Dict[str, Any]]:
    title_tag = soup.find('meta', {'property': 'og:title'})
    description_tag = soup.find('meta', {'property': 'og:description'})
    image_tag = soup.find('meta', {'property': 'og:image'})
    title = title_tag.get('content', '') if title_tag else ''
    description = description_tag.get('content', '') if description_tag else ''

    handle_match = re.search(r'\(@([A-Za-z0-9._]+)\)', title)
    username = handle_match.group(1) if handle_match else (expected_username or '')
    if not username:
        return None
    if expected_username and _normalise_username(username) != _normalise_username(expected_username):
        return None

    full_name = title[:handle_match.start()].strip() if handle_match else ''
    counts = {}
    for key, label in (
        ('followers_count', 'Followers?'),
        ('following_count', 'Following'),
        ('media_count', 'Posts?'),
    ):
        match = re.search(rf'([\d,.]+\s*[KMB]?)\s+{label}\b', description, re.IGNORECASE)
        counts[key] = _parse_count(match.group(1)) if match else 0

    # Only accept an explicitly quoted Instagram biography. The text after the
    # stats is often merely "See photos ... from Name (@handle)", not a bio.
    biography = ''
    bio_match = re.search(
        r'(?:on\s+Instagram|Instagram)\s*:\s*["“](.*?)["”]\s*$',
        description,
        re.IGNORECASE | re.DOTALL,
    )
    if bio_match:
        biography = bio_match.group(1)

    return {
        'username': username,
        'full_name': full_name or username,
        'biography': biography,
        'profile_pic_url': image_tag.get('content') if image_tag else None,
        **counts,
    }


def _metadata_media_count(soup: BeautifulSoup, expected_username: Optional[str]) -> Optional[int]:
    """Return an explicitly published Posts total for the requested profile."""
    profile = _meta_profile(soup, expected_username)
    if not profile:
        return None
    description_tag = soup.find('meta', {'property': 'og:description'})
    description = description_tag.get('content', '') if description_tag else ''
    match = re.search(r'([\d,.]+\s*[KMB]?)\s+Posts?\b', description, re.IGNORECASE)
    return _parse_count(match.group(1)) if match else None


def _rendered_profile_values(
    soup: BeautifulSoup,
    username: str,
) -> Tuple[Dict[str, int], Optional[str]]:
    """Read only explicitly profile-scoped rendered header values."""
    counts: Dict[str, int] = {}

    # Some profile layouts omit the textual posts stat altogether.  The grid is
    # still rendered with post permalinks, so count only Instagram content URL
    # shapes (and de-duplicate anchors pointing at the same item).  Keep this
    # separate from the regular rendered stat so a textual header value does
    # not accidentally override authoritative JSON.
    post_permalink = re.compile(
        r'^(?:/(?:p|reel|tv)/|https://www\.instagram\.com/(?:p|reel|tv)/)'
        r'[^/?#]+/?$',
        re.IGNORECASE,
    )

    def normalise_post_href(href: str) -> str:
        return href.split('?', 1)[0].split('#', 1)[0].rstrip('/').lower()

    post_hrefs = {
        normalise_post_href(link.get('href', ''))
        for link in soup.find_all('a', href=True)
        if post_permalink.match(normalise_post_href(link.get('href', '')))
    }
    if post_hrefs:
        counts['_permalink_media_count'] = len(post_hrefs)

    header = soup.find('header')
    if not header:
        if '_permalink_media_count' in counts:
            counts['media_count'] = counts['_permalink_media_count']
        return counts, None

    escaped = re.escape(username.strip().lstrip('@'))
    profile_link = re.compile(rf'^/{escaped}/(?:followers|following)/?$', re.IGNORECASE)
    scoped_links = [
        link for link in header.find_all('a', href=True)
        if profile_link.match(link.get('href', '').split('?')[0])
    ]
    explicitly_scoped = bool(scoped_links) or header.get('data-testid') == 'profile-header'
    if not explicitly_scoped:
        # The grid permalink count is still profile-scoped by URL shape even
        # when Instagram changes the header's internal markers.
        if '_permalink_media_count' in counts:
            counts['media_count'] = counts['_permalink_media_count']
        return counts, None

    for link in scoped_links:
        href = link.get('href', '').split('?')[0].rstrip('/').lower()
        key = 'followers_count' if href.endswith('/followers') else 'following_count'
        titled = link.find(attrs={'title': True})
        counts[key] = _parse_count(titled.get('title') if titled else link.get_text(' ', strip=True))

    # A posts value has no dedicated URL, so constrain it to a labelled item
    # inside a header already proven to belong to this profile.  React often
    # renders the number and label in separate spans, and accessibility
    # attributes are more stable than the visible markup.
    count_pattern = r'([\d,.]+\s*[KMB]?)'
    post_pattern = re.compile(rf'{count_pattern}\s*posts?\b', re.IGNORECASE)
    reverse_post_pattern = re.compile(rf'posts?\s*{count_pattern}\b', re.IGNORECASE)

    def post_count(value: Any, *, label_only: bool = False) -> int:
        text = str(value or '').strip()
        match = post_pattern.search(text) or reverse_post_pattern.search(text)
        if match:
            return _parse_count(match.group(1))
        if label_only and re.fullmatch(r'[\d,.]+\s*[KMB]?', text, re.IGNORECASE):
            return _parse_count(text)
        return 0

    # First inspect explicit labels (including data-testid values).  This also
    # handles <div aria-label="17 posts"> and nested number/label spans.
    for item in header.find_all(True):
        for attribute in ('aria-label', 'title', 'label', 'data-testid'):
            value = item.get(attribute)
            if not value:
                continue
            parsed = post_count(value)
            if not parsed and re.search(r'posts?', str(value), re.IGNORECASE):
                parsed = post_count(item.get_text(' ', strip=True), label_only=True)
            if parsed:
                counts['media_count'] = parsed
                break
        if 'media_count' in counts:
            break

    if 'media_count' not in counts:
        # Keep the fallback limited to stat-like nodes.  The header is already
        # profile-scoped, but scanning all text could mistake a bio sentence
        # for the post count.
        for item in header.find_all(['li', 'span', 'div']):
            parsed = post_count(item.get_text(' ', strip=True))
            if parsed:
                counts['media_count'] = parsed
                break

    if 'media_count' not in counts and '_permalink_media_count' in counts:
        counts['media_count'] = counts['_permalink_media_count']

    bio_node = header.select_one(
        '[data-testid="profile-bio"], [data-testid="user-bio"], '
        '[itemprop="description"], [aria-label="Bio"]'
    )
    biography = bio_node.get_text('\n', strip=True) if bio_node else None
    return counts, biography


def _extract_profile_from_html(
    html_content: str,
    expected_username: Optional[str] = None,
    rendered_post_count: Optional[int] = None,
) -> Optional[InstagramProfile]:
    """
    Extract Instagram profile data from HTML using BeautifulSoup4
    
    Args:
        html_content: HTML content of Instagram profile page
        
    Returns:
        InstagramProfile or None
    """
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        
        scripts = soup.find_all('script', {'type': 'application/json'})
        user_info = None
        for script in scripts:
            try:
                data = json.loads(script.string or script.get_text())
                candidate = _find_profile_json(data, expected_username)
                if candidate and (
                        user_info is None or
                        (_explicit_media_count(candidate)[0], len(candidate)) >
                        (_explicit_media_count(user_info)[0], len(user_info))):
                    user_info = candidate
            except (json.JSONDecodeError, TypeError):
                continue

        source = 'json'
        warnings: List[str] = []
        if not user_info:
            user_info = _meta_profile(soup, expected_username)
            source = 'metadata'
            if not user_info:
                return None
            warnings.append('Profile counts came from page metadata and may be stale.')

        username = user_info.get('username') or expected_username or ''
        followers_count = _edge_count(user_info, 'follower_count', 'edge_followed_by')
        following_count = _edge_count(user_info, 'following_count', 'edge_follow')
        has_explicit_media_count, explicit_media_count = _explicit_media_count(user_info)
        media_count = (explicit_media_count if has_explicit_media_count else
                       _edge_count(user_info, 'media_count', 'edge_owner_to_timeline_media'))
        metadata_media_count_used = False
        # Some profile JSON copies contain identity fields but omit all total
        # post-count fields. In that case, use the profile-scoped OG metadata;
        # unlike a rendered grid, it represents the complete known total.
        if source == 'metadata':
            metadata_media_count = _metadata_media_count(soup, expected_username)
            if metadata_media_count is not None:
                media_count = metadata_media_count
                metadata_media_count_used = True
                warnings.append('Post count sourced from page metadata.')
        elif not has_explicit_media_count:
            metadata_media_count = _metadata_media_count(soup, expected_username)
            if metadata_media_count is not None:
                media_count = metadata_media_count
                metadata_media_count_used = True
                warnings.append('Post count sourced from page metadata.')

        # Positive JSON totals and page metadata totals are authoritative. A
        # zero JSON placeholder may be filled by a rendered grid/live DOM when
        # no explicit labelled post stat is present.
        has_json_media_count = source == 'json' and has_explicit_media_count
        biography = user_info.get('biography') or ''

        rendered_counts, rendered_bio = _rendered_profile_values(soup, username)
        if rendered_counts:
            followers_count = rendered_counts.get('followers_count', followers_count)
            following_count = rendered_counts.get('following_count', following_count)
            permalink_media_count = rendered_counts.get('_permalink_media_count', 0)
            has_rendered_label = (
                'media_count' in rendered_counts and
                '_permalink_media_count' not in rendered_counts
            )
            if (permalink_media_count and media_count == 0 and
                    not metadata_media_count_used and
                    (not has_json_media_count or not has_rendered_label)):
                media_count = permalink_media_count
            elif not has_json_media_count and not metadata_media_count_used:
                media_count = rendered_counts.get('media_count', media_count)
            source += '+rendered_header'
        if rendered_bio is not None:
            biography = rendered_bio
            if 'rendered_header' not in source:
                source += '+rendered_header'

        # The live DOM can contain posts that are not present in the captured
        # HTML.  Only use that count to fill a zero; positive profile JSON is
        # authoritative and must not be replaced by rendered data.
        has_rendered_label = (
            'media_count' in rendered_counts and
            '_permalink_media_count' not in rendered_counts
        )
        if (media_count == 0 and rendered_post_count and rendered_post_count > 0 and
                not metadata_media_count_used and
                (not has_json_media_count or not has_rendered_label)):
            media_count = int(rendered_post_count)
            if 'rendered' not in source:
                source += '+rendered'

        if not biography:
            warnings.append('Biography unavailable; it may not be empty.')

        return InstagramProfile(
            username=username,
            full_name=user_info.get('full_name', ''),
            bio=biography,
            followers_count=followers_count,
            following_count=following_count,
            media_count=media_count,
            is_private=user_info.get('is_private', False),
            profile_pic_url=(user_info.get('profile_pic_url_hd') or
                             user_info.get('profile_pic_url')),
            is_verified=user_info.get('is_verified', False),
            data_source=source,
            warnings=warnings,
        )
        
    except Exception as e:
        logger.warning(f"Error extracting profile from HTML: {e}")
        return None


async def _fetch_via_playwright(
    username: str,
    headless: bool = True,
) -> Tuple[Optional[InstagramProfile], Optional[str]]:
    """
    Fetch Instagram profile using Playwright browser automation
    
    Args:
        username: Instagram username
        headless: Whether to run browser in headless mode
        
    Returns:
        Tuple of (InstagramProfile, error_message)
    """
    try:
        from playwright.async_api import async_playwright
        
        async with async_playwright() as p:
            # Launch browser
            browser = await p.chromium.launch(headless=headless)
            context = await browser.new_context(
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            )
            page = await context.new_page()
            
            try:
                # Navigate to Instagram profile
                await page.goto(f'https://www.instagram.com/{username}/', 
                              wait_until='domcontentloaded',
                              timeout=20000)
                
                # Wait for content to load
                # Wait for page to be interactive (faster than networkidle)
                try:
                    await asyncio.wait_for(
                        page.wait_for_load_state('networkidle'),
                        timeout=5
                    )
                except asyncio.TimeoutError:
                    logger.debug(f"Network idle timeout for {username}, continuing with current content")
                    pass

                # Instagram can keep analytics requests open indefinitely. A
                # profile-scoped header is a better bounded readiness signal.
                try:
                    await page.wait_for_selector(
                        f'header a[href="/{username}/followers/"], '
                        f'header a[href="/{username}/following/"]',
                        timeout=8000,
                    )
                except Exception:
                    logger.debug(f"Rendered profile header not observed for {username}")

                # The grid is client-rendered and may not be represented in
                # page.content(). Count a bounded set of unique post links
                # from the live DOM as a parser fallback.
                rendered_post_count = 0
                try:
                    post_links = page.locator(
                        'a[href*="/p/"], a[href*="/reel/"], a[href*="/tv/"]'
                    )
                    link_count = min(await post_links.count(), 1000)
                    post_hrefs = set()
                    post_permalink = re.compile(
                        r'^(?:/(?:p|reel|tv)/|https://www\.instagram\.com/'
                        r'(?:p|reel|tv)/)[^/?#]+/?$',
                        re.IGNORECASE,
                    )
                    for index in range(link_count):
                        href = await post_links.nth(index).get_attribute('href')
                        if not href:
                            continue
                        normalized_href = href.split('?', 1)[0].split('#', 1)[0].rstrip('/').lower()
                        if post_permalink.match(normalized_href):
                            post_hrefs.add(normalized_href)
                    rendered_post_count = len(post_hrefs)
                except Exception:
                    logger.debug(f"Could not count rendered post links for {username}")
                
                # Get page content
                content = await page.content()
                
                # Extract profile from HTML
                profile = _extract_profile_from_html(
                    content,
                    expected_username=username,
                    rendered_post_count=rendered_post_count,
                )
                
                if profile:
                    logger.info(f"Successfully fetched profile for {username} via Playwright")
                    return profile, None
                else:
                    return None, "Could not extract profile data from HTML"
                    
            finally:
                await context.close()
                await browser.close()
                
    except Exception as e:
        error_msg = f"Playwright error: {str(e)}"
        logger.warning(error_msg)
        return None, error_msg


def _fetch_via_playwright_sync(
    username: str,
    headless: bool = True,
) -> Tuple[Optional[InstagramProfile], Optional[str]]:
    """
    Synchronous wrapper for Playwright fetching
    
    Args:
        username: Instagram username
        headless: Whether to run browser in headless mode
        
    Returns:
        Tuple of (InstagramProfile, error_message)
    """
    try:
        # Try to get existing event loop, if not, create a new one
        try:
            loop = asyncio.get_running_loop()
            # If we're here, there's a running loop (e.g., in Jupyter)
            import concurrent.futures
            import threading
            
            # Run in a separate thread to avoid blocking
            with concurrent.futures.ThreadPoolExecutor() as pool:
                future = pool.submit(asyncio.run, _fetch_via_playwright(username, headless))
                return future.result(timeout=120)
        except RuntimeError:
            # No running loop, safe to use asyncio.run()
            return asyncio.run(_fetch_via_playwright(username, headless))
    except Exception:
        logger.exception("Playwright sync wrapper error")
        return None, "Unable to fetch Instagram profile at this time."


def fetch_instagram_profile(
    username: str,
    *,
    session_id: Optional[str] = None,
    fetch_details: bool = False,
    headless: bool = True,
) -> Tuple[Optional[InstagramProfile], Optional[str]]:
    """
    Fetch Instagram profile using Playwright browser automation
    
    Args:
        username: Instagram username to fetch
        session_id: Session ID (for future use)
        fetch_details: Whether to fetch followers, following, and posts (not yet implemented)
        headless: Whether to run Playwright in headless mode
        
    Returns:
        Tuple of (InstagramProfile object, error message)
        - Returns profile if successful, error message otherwise
    """
    if not username:
        return None, "Username is required"
    
    username = username.strip()
    logger.info(f"Fetching Instagram profile for {username} using Playwright")
    
    try:
        result = _fetch_via_playwright_sync(username, headless)
        if isinstance(result, tuple):
            return result
        # Handle case where result is future/promise
        import concurrent.futures
        if isinstance(result, concurrent.futures.Future):
            return result.result(timeout=60)
    except Exception:
        logger.exception("Playwright method failed")
        return None, "Unable to fetch Instagram profile at this time."
    
    return None, "Unable to fetch Instagram profile"


# Legacy function for backward compatibility
def get_instagram_data(username: str) -> Dict[str, Any]:
    """
    Legacy function for backward compatibility
    
    Args:
        username: Instagram username
        
    Returns:
        Dictionary with profile data or error
    """
    profile, error = fetch_instagram_profile(username)
    
    if error:
        return {"error": error}
    
    return profile.to_dict()


# Test
if __name__ == "__main__":
    username = input("Enter username: ")
    result = fetch_instagram_profile(username)
    if result[0]:
        print(json.dumps(result[0].to_dict(), indent=2))
    else:
        print(f"Error: {result[1]}")
