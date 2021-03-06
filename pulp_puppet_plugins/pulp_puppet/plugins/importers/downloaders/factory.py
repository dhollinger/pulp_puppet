"""
Determines the correct downloader implementation to return based on the
feed type.
"""

from gettext import gettext as _
import logging
import urlparse

from pulp_puppet.plugins.importers.downloaders.exceptions import UnsupportedFeedType, InvalidFeed
from pulp_puppet.plugins.importers.downloaders.web import HttpDownloader
from pulp_puppet.plugins.importers.downloaders.local import LocalDownloader


# Mapping from feed prefix to downloader class
MAPPINGS = {
    'file': LocalDownloader,
    'http': HttpDownloader,
    'https': HttpDownloader,
}

logger = logging.getLogger(__name__)


def get_downloader(feed, repo, conduit, config):
    """
    Returns an instance of the correct downloader to use for the given feed.

    :param feed: location from which to sync modules
    :type  feed: str

    :param repo: describes the repository being synchronized
    :type  repo: pulp.plugins.model.Repository

    :param conduit: sync conduit used during the sync process
    :type  conduit: pulp.plugins.conduits.repo_sync.RepoSyncConduit

    :param config: configuration of the importer and call
    :type  config: pulp.plugins.config.PluginCallConfiguration

    :return: downloader instance to use for the given feed

    :raise UnsupportedFeedType: if there is no applicable downloader for the
           given feed
    :raise InvalidFeed: if the feed cannot be parsed to determine the type
    """

    feed_type = _determine_feed_type(feed)

    if feed_type not in MAPPINGS:
        raise UnsupportedFeedType(feed_type)

    downloader = MAPPINGS[feed_type](repo, conduit, config)
    return downloader


def is_valid_feed(feed):
    """
    Returns whether or not the feed is valid.

    :param feed: repository source
    :type  feed: str

    :return: true if the feed is valid; false otherwise
    :rtype:  bool
    """
    try:
        feed_type = _determine_feed_type(feed)
        is_valid = feed_type in MAPPINGS
        return is_valid
    except InvalidFeed:
        return False


def _determine_feed_type(feed):
    """
    Returns the type of feed represented by the given feed.

    :param feed: feed being synchronized
    :type  feed: str

    :return: type to use to retrieve the downloader instance
    :rtype:  str

    :raise InvalidFeed: if the feed is invalid and a feed cannot be
           determined
    """
    try:
        proto, netloc, path, params, query, frag = urlparse.urlparse(feed)
        return proto
    except Exception:
        msg = _('Exception parsing feed type for feed <%(feed)s>')
        msg_dict = {'feed': feed}
        logger.exception(msg, msg_dict)
        raise InvalidFeed(feed)
