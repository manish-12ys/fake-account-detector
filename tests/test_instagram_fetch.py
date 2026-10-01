import json
import unittest

from utils.instagram_fetch import _extract_profile_from_html


class InstagramProfileParserTests(unittest.TestCase):
    def test_nested_graphql_profile_uses_edges_and_actual_bio(self):
        payload = {
            'data': {'user': {
                'username': 'real_handle',
                'full_name': 'Real Name',
                'biography': '✨ line one\nline two',
                'edge_followed_by': {'count': 222},
                'edge_follow': {'count': 236},
                'edge_owner_to_timeline_media': {'count': 17},
            }}
        }
        html = '<script type="application/json">' + json.dumps(payload) + '</script>'
        profile = _extract_profile_from_html(html, expected_username='real_handle')

        self.assertEqual(profile.username, 'real_handle')
        self.assertEqual(profile.bio, '✨ line one\nline two')
        self.assertEqual(profile.followers_count, 222)
        self.assertEqual(profile.following_count, 236)
        self.assertEqual(profile.media_count, 17)
        self.assertEqual(profile.data_source, 'json')
        self.assertEqual(profile.warnings, [])

    def test_rendered_profile_header_overrides_stale_metadata(self):
        html = '''
        <meta property="og:title" content="Display Name (@real_handle) • Instagram">
        <meta property="og:description" content="500 Followers, 236 Following, 17 Posts - See Instagram photos">
        <header>
          <a href="/real_handle/followers/"><span title="222">500</span></a>
          <a href="/real_handle/following/"><span title="236">236</span></a>
          <ul><li>17 posts</li></ul>
          <div data-testid="profile-bio">🌈 actual bio\nwith a newline</div>
        </header>
        '''
        profile = _extract_profile_from_html(html, expected_username='real_handle')

        self.assertEqual(profile.username, 'real_handle')
        self.assertEqual(profile.followers_count, 222)
        self.assertEqual(profile.following_count, 236)
        self.assertEqual(profile.media_count, 17)
        self.assertEqual(profile.bio, '🌈 actual bio\nwith a newline')
        self.assertIn('metadata', profile.data_source)
        self.assertIn('rendered_header', profile.data_source)

    def test_metadata_does_not_turn_stats_or_unrelated_text_into_bio(self):
        html = '''
        <meta property="og:title" content="Display Name (@real_handle) • Instagram">
        <meta property="og:description" content="222 Followers, 236 Following, 17 Posts - See Instagram photos and videos from Display Name (@real_handle)">
        <p>999 Followers unrelated page</p>
        '''
        profile = _extract_profile_from_html(html, expected_username='real_handle')

        self.assertEqual(profile.username, 'real_handle')
        self.assertEqual(profile.bio, '')
        self.assertIn('may be stale', profile.warnings[0])
        self.assertTrue(any('Biography unavailable' in warning for warning in profile.warnings))

    def test_nested_rendered_posts_stat_and_accessibility_labels(self):
        html = '''
        <meta property="og:title" content="Display Name (@real_handle) • Instagram">
        <header>
          <a href="/real_handle/followers/">222 Followers</a>
          <a href="/real_handle/following/">236 Following</a>
          <ul><li data-testid="profile-posts"><span>1,234</span><span> posts</span></li></ul>
        </header>
        '''
        profile = _extract_profile_from_html(html, expected_username='real_handle')

        self.assertEqual(profile.media_count, 1234)

    def test_json_media_count_takes_precedence_over_rendered_header(self):
        payload = {'data': {'user': {
            'username': 'real_handle', 'full_name': 'Real Name',
            'media_count': 0, 'follower_count': 2, 'following_count': 3,
        }}}
        html = (
            '<script type="application/json">' + json.dumps(payload) + '</script>'
            '<header data-testid="profile-header">'
            '<a href="/real_handle/followers/">2 Followers</a>'
            '<a href="/real_handle/following/">3 Following</a>'
            '<div aria-label="17 posts"><span>17</span><span>posts</span></div>'
            '</header>'
        )
        profile = _extract_profile_from_html(html, expected_username='real_handle')

        self.assertEqual(profile.media_count, 0)

    def test_zero_json_media_count_uses_unique_rendered_post_permalinks(self):
        payload = {'data': {'user': {
            'username': 'real_handle', 'full_name': 'Real Name',
            'media_count': 0, 'follower_count': 2, 'following_count': 3,
        }}}
        html = (
            '<script type="application/json">' + json.dumps(payload) + '</script>'
            '<header data-testid="profile-header">'
            '<a href="/real_handle/followers/">2 Followers</a>'
            '<a href="/real_handle/following/">3 Following</a>'
            '</header>'
            '<main>'
            '<a href="/p/first/">First</a>'
            '<a href="/reel/second/">Second</a>'
            '<a href="/tv/third">Third</a>'
            '<a href="/p/first/">Duplicate</a>'
            '<a href="/explore/tags/example/">Not a post</a>'
            '</main>'
        )
        profile = _extract_profile_from_html(html, expected_username='real_handle')

        self.assertEqual(profile.media_count, 3)

    def test_absolute_rendered_post_permalinks_are_counted_and_deduplicated(self):
        html = '''
        <meta property="og:title" content="Display Name (@real_handle) • Instagram">
        <a href="https://www.instagram.com/p/First/?utm_source=grid">First</a>
        <a href="https://www.instagram.com/p/First/">Duplicate</a>
        <a href="https://www.instagram.com/reel/Second/#clip">Second</a>
        <a href="https://www.instagram.com/tv/Third/">Third</a>
        <a href="https://instagram.com/p/Other/">Not www.instagram.com</a>
        '''
        profile = _extract_profile_from_html(html, expected_username='real_handle')

        self.assertEqual(profile.media_count, 3)

    def test_rendered_post_count_fills_zero_json_media_count(self):
        payload = {'data': {'user': {
            'username': 'real_handle', 'full_name': 'Real Name',
            'media_count': 0, 'follower_count': 2, 'following_count': 3,
        }}}
        html = '<script type="application/json">' + json.dumps(payload) + '</script>'
        profile = _extract_profile_from_html(
            html,
            expected_username='real_handle',
            rendered_post_count=3,
        )

        self.assertEqual(profile.media_count, 3)

    def test_positive_json_media_count_remains_authoritative_over_rendered_count(self):
        payload = {'data': {'user': {
            'username': 'real_handle', 'full_name': 'Real Name',
            'media_count': 17,
        }}}
        html = '<script type="application/json">' + json.dumps(payload) + '</script>'
        profile = _extract_profile_from_html(
            html,
            expected_username='real_handle',
            rendered_post_count=3,
        )

        self.assertEqual(profile.media_count, 17)

    def test_zero_graphql_media_count_uses_loaded_timeline_edges(self):
        payload = {'data': {'user': {
            'username': 'real_handle',
            'edge_owner_to_timeline_media': {
                'count': 0,
                'edges': [{'node': {}}, {'node': {}}, {'node': {}}],
            },
        }}}
        html = '<script type="application/json">' + json.dumps(payload) + '</script>'
        profile = _extract_profile_from_html(html, expected_username='real_handle')

        self.assertEqual(profile.media_count, 3)


if __name__ == '__main__':
    unittest.main()
