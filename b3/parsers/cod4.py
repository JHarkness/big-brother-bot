# BigBrotherBot(B3) (www.bigbrotherbot.com)
# Copyright (C) 2005 Michael "ThorN" Thornton
# 
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
#
# $Id: $

__author__  = 'ThorN'
__version__ = '1.0'

import b3.parsers.cod2
import b3.parsers.q3a
import re

class Cod4Parser(b3.parsers.cod2.Cod2Parser):
    gameName = 'cod4'

    def getClient(self, match=None, attacker=None, victim=None):
        """Get a client object using the best availible data.
        Prefer GUID first, then Client ID (CID)
        """
        if attacker:
            keys = ['aguid', 'acid']
        else:
            keys = ['guid', 'cid']

        methods = [self.clients.getByGUID, self.clients.getByCID]

        match = attacker or victim or match

        for k, m in zip(keys, methods):
            client = m(match.group(k))
            if client:
                return client

    # join
    def OnJ(self, action, data, match=None):
        # COD4 stores the PBID in the log file
        pbguid = match.group('guid')

        client = self.getClient(match)

        if client:
            # update existing client
            client.state = b3.STATE_ALIVE
            # possible name changed
            client.name = match.group('name')
        else:
            # make a new client
            if self.PunkBuster:        
                # we will use punkbuster's guid
                guid = None # Set to none so PB_SV_PLIST is triggered in clients.authorizeClients for the ip address
                pbid = pbguid
            else:
                # use cod guid - is this reliable without punkbuster?
                guid = pbguid 

            client = self.clients.newClient(match.group('cid'), name=match.group('name'), state=b3.STATE_ALIVE, guid=guid)

        return b3.events.Event(b3.events.EVT_CLIENT_JOIN, None, client)

    # kill
    def OnK(self, action, data, match=None):
        victim = self.getClient(victim=match)
        if not victim:
            self.debug('No victim %s' % match.groupdict())
            self.OnJ(action, data, match)
            return None

        attacker = self.getClient(attacker=match)
        if not attacker:
            self.debug('No attacker %s' % match.groupdict())
            return None

        # COD4 doesn't report the team on kill, only use it if it's set
        # Hopefully the team has been set on another event
        if match.group('ateam'):
            attacker.team = self.getTeam(match.group('ateam'))

        if match.group('team'):
            victim.team = self.getTeam(match.group('team'))


        attacker.name = match.group('aname')
        victim.name = match.group('name')

        event = b3.events.EVT_CLIENT_KILL

        if attacker.cid == victim.cid:
            event = b3.events.EVT_CLIENT_SUICIDE
        elif attacker.team != b3.TEAM_UNKNOWN and \
             attacker.team and \
             victim.team and \
             attacker.team == victim.team:
            event = b3.events.EVT_CLIENT_KILL_TEAM

        victim.state = b3.STATE_DEAD
        return b3.events.Event(event, (float(match.group('damage')), match.group('aweap'), match.group('dlocation'), match.group('dtype')), attacker, victim)
