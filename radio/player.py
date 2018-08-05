#!/usr/bin/env python3.6
# -*- coding: utf-8 -*-
#!/usr/bin/env python3.6
# -*- coding: utf-8 -*-

from mpd import MPDClient
from mpd.base import CommandError
from collections import OrderedDict
import time
import os
import arrow
import logging
import errno



class Player():
    def __init__(self):
        self.logger= logging.getLogger(__name__)
        client = MPDClient()
        client.timeout = 10
        client.idletimeout = None
        client.connect("localhost", 6600)
        self.logger.info("Started Player")
        self.client = client

    def close(self):
        self.client.close()
        self.client.disconnect()

    @property
    def status(self):
        return self.client.status()

    @property
    def stats(self):
        self.client.update()
        return self.client.stats()

    @property
    def artists(self):
        """
        The number of Artists
        """
        return int(self.stats["artists"])

    @property
    def albums(self):
        """
        The number of Albums
        """
        return int(self.stats["albums"])

    @property
    def n_songs(self):
        """
        The number of songs
        """
        return int(self.stats["songs"])

    @property
    def uptime(self):
        """
        Daemon uptime in seconds
        """
        return int(self.stats["uptime"])

    @property
    def total_playtime(self):
        """
        The sum of all songs in the db
        """
        return int(self.stats["db_playtime"])

    @property
    def last_update(self):
        """
        The sum of all songs in the db
        """
        return arrow.get(int(self.stats["db_update"]))

    @property
    def currentsong(self):
        return self.client.currentsong()

    @property
    def currentsong_formatted(self):
        return self.format_song(self.currentsong)

    def format_song(self, songdict):
        position = songdict["pos"].zfill(4)
        song_id = songdict["id"]
        file = songdict["file"]
        name = songdict["name"] if "name" in songdict.keys() else ""
        title = songdict["title"] if "title" in songdict.keys() else ""
        string = "["+str(position)+"][ID: "+str(song_id)+"] "+(name+" "+title).strip()+" (File: "+str(file)+")"
        return string

    @property
    def stopped(self):
        return self.status["status"] == "stop"

    @property
    def paused(self):
        return self.status["state"] == "pause"

    @property
    def playing(self):
        return self.status["state"] == "play"

    @property
    def currentindex(self):
        """
        Queue Index number of the current song stopped or playing
        """
        try:
            return int(self.status["song"])
        except KeyError:
            return None

    @property
    def songid(self):
        """
        Queue Song ID of the current song stopped or playing
        """
        return int(self.status["songid"])

    @property
    def nextsong(self):
        """
        Queue Song number of the current song stopped or playing
        """
        try:
            return int(self.status["nextsong"])
        except KeyError:
            return None

    @property
    def nextsongid(self):
        """
        Queue Song ID of the current song stopped or playing
        """
        try:
            return int(self.status["nextsongid"])
        except KeyError:
            return None

    @property
    def elapsed(self):
        """
        Total time elapsed within the current song
        """
        return self.status["elapsed"]

    @property
    def duration(self):
        """
        Total tduration of the current song
        """
        return self.status["duration"]

    @property
    def queuelength(self):

        return int(self.status["playlistlength"])

    @property
    def seek(self, songpos, time):
        """
        Seeks to the position TIME (in seconds; fractions allowed) of entry SONGPOS in the playlist.
        """
        self.client.seek(songpos, time)

    @property
    def seekid(self, songid, time):
        """
        Seeks to the position TIME (in seconds; fractions allowed) of song SONGID.
        """
        self.client.seekid(songid, time)

    @property
    def seekcurrent(self, time):
        """
        Seeks to the position TIME (in seconds; fractions allowed) within the current song. If prefixed by ‘+’ or ‘-‘, then the time is relative to the current playing position.
        """
        self.client.seekcur(time)

    @property
    def volume(self):
        return int(self.status["volume"])

    @volume.setter
    def volume(self, value):
        if value > 100: value = 100
        if value < 0: value = 0
        pvol = self.volume
        self.client.setvol(value)
        if value == 0:
            self.logger.info("[🔈]: Set volume to "+str(value))
        elif pvol > value:
            self.logger.info("[🔉]: Decreased volume to "+str(value))
        else:
            self.logger.info("[🔊] Increased volume to "+str(value))

    @property
    def repeat(self):
        return int(self.status["repeat"]) == 1

    @repeat.setter
    def repeat(self, value):
        if value:
            self.client.repeat(1)
            self.logger.info("[⭯]: Repeat set True")
        else:
            self.client.repeat(0)
            self.logger.info("[➝]: Repeat set False")

    @property
    def consume(self):
        return int(self.status["consume"]) == 1

    @consume.setter
    def consume(self, value):
        if value:
            self.client.consume(1)
            self.logger.info("[⚺]: Consume set True")
        else:
            self.client.consume(0)
            self.logger.info("[⚻]: Consume set False")

    @property
    def random(self):
        return int(self.status["random"]) == 1

    @random.setter
    def random(self, value):
        if value:
            self.client.random(1)
            self.logger.info("[🔀]: Random set True")
        else:
            self.client.random(0)
            self.logger.info("[⮆]: Random set False")

    @property
    def single(self):
        return int(self.status["single"]) == 1

    @single.setter
    def single(self, value):
        if value:
            self.client.single(1)
            self.logger.info("[⭲]: Single set True")
        else:
            self.client.single(0)
            self.logger.info("[⮒]: Single set False")

    @property
    def replay_gain_mode(self):
        return self.client.replay_gain_status()

    @replay_gain_mode.setter
    def replay_gain_mode(self, mode):
        mode = mode.strip().lower()
        options = ["off", "track", "album", "auto"]
        if mode in options:
            self.client.replay_gain_mode(mode)
            self.logger.info("[🎛]: Set Replay Gain Mode to "+str(mode))
        else:
            self.logger.warning("[🎛][❌]: client.replay_gain_mode has no option "+str(mode)+". Available options are: "+", ".join(options))

    def next(self):
        """
        Switch to the next song in the queue
        Catch out of bounds
        """
        pindex = self.currentindex
        if self.currentindex is None:
            self.play()
        elif self.currentindex < self.queuelength-1:
            try:
                self.client.next()
                self.client.update()
                self.logger.info("[⏭]["+str(pindex)+"]->["+str(self.currentindex)+"]: Switched to next song: "+str(self.currentsong_formatted))
            except CommandError as e:
                self.logger.warning("[⏭][❌]: "+str(e))
        else:
            self.logger.warning("[⏭][❌]: Couldn't switch to next song. Would be out of index.. ("+str(self.currentindex+1)+" would be >= "+str(self.queuelength-1)+")")

    def previous(self):
        """
        Switch to the previous song in the queue
        Catch out of bounds
        """
        pindex = self.currentindex
        if self.currentindex > 0:
            self.client.previous()
            self.client.update()
            self.logger.info("[⏮]["+str(self.currentindex)+"]<-["+str(pindex)+"]: Switched to previous song : "+str(self.currentsong_formatted))
        else:
            self.logger.warning("[⏮][❌]: Couldn't switch to previous song. Would be out of index ("+str(self.currentindex-1)+" would be < 0)")

    def pause(self):
        self.client.pause(1)
        self.logger.info("[⏸]: Paused Playback")

    def unpause(self):
        self.client.pause(0)
        self.logger.info("[⏯]: Unpaused Playback")

    def toggle_pause(self):
        if self.paused:
            self.unpause()
        else:
            self.pause()

    def play(self, songpos=None):
        if songpos is None and self.currentindex is None:
            songpos = 0
        elif songpos is None:
            songpos = self.currentindex
        if self.queuelength == 0:
            self.logger.warning("[▶][❌]:Couldn't start playing. There are no songs..")
        elif songpos < 0:
            self.logger.warning("[▶][❌]:Couldn't play song at ["+str(songpos)+"]!")
        elif songpos > self.queuelength:
            self.logger.warning("[▶][❌]:Couldn't play song at ["+str(songpos)+"]. The biggest index is "+str(self.queuelength))
        else:
            self.client.play(songpos)
            self.client.update()
            self.logger.info("[▶]["+str(songpos)+"]: "+str(self.currentsong_formatted))

    def stop(self):
        self.client.stop()
        self.logger.info("[⯀]: Stopped Playback")

    def enqueue(self, uri):
        """
        Adds the file URI to the queue (directories add recursively). URI can also be a single file.
        """
        self.client.add(uri)
        self.client.idle()
        self.logger.info("[➕]: Enqueued song(s) with URI ("+str(uri)+")")

    def dequeue(self, uri):
        """
        Dequeue a song by uri.
        """
        self.deleteuri(uri)

    def enqueueid(self, uri, position):
        """
        Adds a song to the queue (non-recursive) and returns the song id.
        URI is always a single file or URL. For example: foo.mp3
        """
        self.client.addid(uri, position)
        self.logger.info("[➕]: Enqueued song with ID ("+str(uri)+") at position ["+str(position)+"]")

    def clear(self):
        """
        Clear the current queue
        """
        self.client.clear()
        self.logger.info("[◠]: Cleared the current queue")

    def delete(self, songpos):
        """
        Delete a song from the queue by position
        """
        self.client.delete(songpos)
        self.logger.info("[➖]: Deleted song at position ["+str(songpos)+"]")

    def deleteuri(self, uri):
        matches = [song["id"] for song in self.queue if uri in song["file"]]
        for match in matches:
            self.deleteid(match)

    def deleteid(self, songid):
        self.client.deleteid(songid)
        self.logger.info("[➖]: Deleted song with ID ("+str(songid)+")")

    def move(self, source, targetposition):
        """
        Moves the song at FROM or range of songs at START:END to TO in the queue.
        """
        self.client.move(source, targetposition)
        self.logger.info("[⮓]: Moved song(s) from ["+str(source)+"] to ["+str(targetposition)+"]")

    def moveid(self, songid, targetposition):
        """
        Moves the song with FROM (songid) to TO (queue index) in the queue. 
        If TO is negative, it is relative to the current song in the queue (if there is one).
        """
        self.client.moveid(songid, targetposition)
        self.logger.info("[⮓]: Moved song(s) with ID ("+str(songid)+") to ["+str(targetposition)+"]")

    @property
    def queue(self, songpos=""):
        """
        Return a list of dicts for all songs in the queue, or if the optional argument is given, 
        displays information only for the song SONGPOS or the range of songs START:END
        """
        if songpos == "":
            return self.client.playlistinfo()
        else:
            return self.client.playlistinfo(songpos)

    @property
    def queue_formatted(self):
        lines = []
        for song in self.queueinfo:
            lines.append(self.format_song(song))
        return "\n".join(lines)







if __name__ == "__main__":
    logging.basicConfig(format=('[%(levelname)-8s]:\t')+('%(message)s'), level=logging.INFO)
    # basepath = "/var/lib/mpd/playlists/"

    player = Player()
    player.clear()
    # player.volume = 100
    # player.enqueue("http://mp3stream1.apasf.apa.at:8000")
    # player.enqueue("http://mp3stream3.apasf.apa.at:8000")
    # player.enqueue("http://st02.dlf.de/dlf/02/128/mp3/stream.mp3")
    # player.enqueue("http://st01.dlf.de/dlf/01/128/mp3/stream.mp3")
    # player.enqueue("http://ice1.somafm.com/groovesalad-128-mp3")
    # player.enqueue("http://ice1.somafm.com/lush-128-mp3")
    # player.enqueue("http://ice1.somafm.com/sonicuniverse-128-mp3")
    # player.enqueue("http://ice1.somafm.com/missioncontrol-128-mp3")
    # player.enqueue("http://ice1.somafm.com/illstreet-128-mp3")
    # player.enqueue("http://ice1.somafm.com/suburbsofgoa-128-mp3")
    # player.enqueue("http://ice1.somafm.com/u80s-128-mp3")
    # player.enqueue("http://ice1.somafm.com/7soul-128-mp3")
    # player.enqueue("http://ice1.somafm.com/secretagent-128-mp3")
    # player.enqueue("http://ice1.somafm.com/cliqhop-128-mp3")
    # player.enqueue("http://ice1.somafm.com/fluid-128-mp3")
    # player.enqueue("http://ice1.somafm.com/defcon-256-mp3")
    # player.enqueue("http://ice1.somafm.com/brfm-128-mp3")

    # player.dequeue("http://ice1.somafm.com/brfm-128-mp3")

    # print(player.queue_formatted)
    # interval = 2
    # player.play()
    # time.sleep(interval)
    # player.next()
    # time.sleep(interval)
    # player.next()
    # time.sleep(interval)
    # player.next()
    # time.sleep(interval)
    # player.next()
    # time.sleep(interval)
    # player.next()
    # time.sleep(interval)
    # player.next()
    # time.sleep(interval)
    # player.next()
    # time.sleep(interval)
    # player.next()
    # time.sleep(interval)
    # player.next()
    # time.sleep(interval)
    # player.next()
    # time.sleep(interval)
    # player.next()
    # time.sleep(interval)
    # player.next()
    # time.sleep(interval)
    # player.next()
    # time.sleep(interval)
    # player.next()
    # time.sleep(interval)
    # player.next()
    # time.sleep(interval)
    # player.next()
    # time.sleep(interval)
    # player.next()
    # time.sleep(interval)
    # player.stop()

