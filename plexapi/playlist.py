# -*- coding: utf-8 -*-
from plexapi import utils
from plexapi.base import PlexPartialObject, Playable
from plexapi.exceptions import BadRequest
from plexapi.playqueue import PlayQueue
from plexapi.utils import cast, toDatetime


@utils.registerPlexObject
class Playlist(PlexPartialObject, Playable):
    """ Represents a single Playlist object.
        # TODO: Document attributes
    """
    TAG = 'Playlist'
    TYPE = 'playlist'

    def _loadData(self, data):
        """ Load attribute values from Plex XML response. """
        Playable._loadData(self, data)
        self.addedAt = toDatetime(data.attrib.get('addedAt'))
        self.composite = data.attrib.get('composite')  # url to thumbnail
        self.duration = cast(int, data.attrib.get('duration'))
        self.durationInSeconds = cast(int, data.attrib.get('durationInSeconds'))
        self.guid = data.attrib.get('guid')
        self.key = data.attrib.get('key')
        self.key = self.key.replace('/items', '') if self.key else self.key  # FIX_BUG_50
        self.leafCount = cast(int, data.attrib.get('leafCount'))
        self.playlistType = data.attrib.get('playlistType')
        self.ratingKey = cast(int, data.attrib.get('ratingKey'))
        self.smart = cast(bool, data.attrib.get('smart'))
        self.summary = data.attrib.get('summary')
        self.title = data.attrib.get('title')
        self.type = data.attrib.get('type')
        self.updatedAt = toDatetime(data.attrib.get('updatedAt'))

    def items(self):
        """ Returns a list of all items in the playlist. """
        key = '%s/items' % self.key
        return self.fetchItems(key)

    def addItems(self, items):
        """ Add items to a playlist. """
        if not isinstance(items, (list, tuple)):
            items = [items]
        ratingKeys = []
        for item in items:
            if item.listType != self.playlistType:
                raise BadRequest('Can not mix media types when building a playlist: %s and %s' %
                    (self.playlistType, item.listType))
            ratingKeys.append(str(item.ratingKey))
        uuid = items[0].section().uuid
        ratingKeys = ','.join(ratingKeys)
        key = '%s/items%s' % (self.key, utils.joinArgs({
            'uri': 'library://%s/directory//library/metadata/%s' % (uuid, ratingKeys)
        }))
        return self._server.query(key, method=self._server._session.put)

    def removeItem(self, item):
        """ Remove a file from a playlist. """
        key = '%s/items/%s' % (self.key, item.playlistItemID)
        return self._server.query(key, method=self._server._session.delete)

    def moveItem(self, item, after=None):
        """ Move a to a new position in playlist. """
        key = '%s/items/%s/move' % (self.key, item.playlistItemID)
        if after:
            key += '?after=%s' % after.playlistItemID
        return self._server.query(key, method=self._server._session.put)

    def edit(self, title=None, summary=None):
        """ Edit playlist. """
        key = '/library/metadata/%s%s' % (self.ratingKey, utils.joinArgs({'title': title, 'summary': summary}))
        return self._server.query(key, method=self._server._session.put)

    def delete(self):
        """ Delete playlist. """
        return self._server.query(self.key, method=self._server._session.delete)

    def playQueue(self, *args, **kwargs):
        """ Create a playqueue from this playlist. """
        return PlayQueue.create(self._server, self, *args, **kwargs)

    @classmethod
    def create(cls, server, title, items):
        """ Create a playlist. """
        if not isinstance(items, (list, tuple)):
            items = [items]
        ratingKeys = []
        for item in items:
            if item.listType != items[0].listType:
                raise BadRequest('Can not mix media types when building a playlist')
            ratingKeys.append(str(item.ratingKey))
        ratingKeys = ','.join(ratingKeys)
        uuid = items[0].section().uuid
        key = '/playlists%s' % utils.joinArgs({
            'uri': 'library://%s/directory//library/metadata/%s' % (uuid, ratingKeys),
            'type': items[0].listType,
            'title': title,
            'smart': 0
        })
        data = server.query(key, method=server._session.post)[0]
        return cls(server, data, initpath=key)
