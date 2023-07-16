import yt_dlp

SCAN_LAST_N_VIDEOS = 10
POST_PROCESSING_DONE = "POST_PROCESSING_DONE"

YDL_OPTS_CHANNEL_NAME = {
        'forceprint': {'video': ['%(channel)s']},
        'noprogress': True,
        'playlist_items': '1',
        'quiet': True,
        'simulate': True}

YDL_OPTS_BULK_DOWNLOAD = {
        'concurrent_fragment_downloads': 12,
        'allow_playlist_files': False,
        'download_archive': 'archive.txt',
        'format': 'bestvideo[height>=720]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        'getcomments': False,
        'match_filter': yt_dlp.match_filter_func("title ~=.* & !is_post_live_dvr"),
        'merge_output_format': 'mp4',
        'outtmpl': {'default': '%(title)s.%(ext)s',
                    'description': '%(title)s/%(title)s.%(ext)s',
                    'infojson': '%(title)s/%(title)s.%(ext)s',
                    'thumbnail': '%(title)s/%(title)s.%(ext)s'},
        'postprocessors': [{'format': 'jpg',
                            'key': 'FFmpegThumbnailsConvertor',
                            'when': 'before_dl'},
                            {'add_chapters': True,
                            'add_infojson': 'if_exists',
                            'add_metadata': True,
                            'key': 'FFmpegMetadata'},
                            {'already_have_thumbnail': True, 'key': 'EmbedThumbnail'}],
        'writedescription': True,
        'writeinfojson': True,
        'writethumbnail': True,}

YDL_OPTS_SINGLE_DOWNLOAD = {'concurrent_fragment_downloads': 12,
        'format': 'bestvideo[height>=720]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        'merge_output_format': 'mp4',
        'match_filter': yt_dlp.match_filter_func("!is_post_live_dvr"),
        'outtmpl': {'default': f'%(title)s.%(ext)s', 'pl_thumbnail': ''},
        'postprocessors': [{'add_chapters': True,
                            'add_infojson': 'if_exists',
                            'add_metadata': True,
                            'key': 'FFmpegMetadata'},
                            {'already_have_thumbnail': False, 'key': 'EmbedThumbnail'}],
        'writethumbnail': True}