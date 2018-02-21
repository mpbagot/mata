from api.packets import *
from api.properties import *
from api.entity import Entity, Player
from api.vehicle import Vehicle

from threading import Thread
from multiprocessing import Process, Queue
import pygame
from copy import deepcopy

import util

def onTickGenerateWorld(game, tick):
    '''
    Event Hook: onTick
    Handles the generation of the world when necessary
    '''
    if game.getGui() and game.getGui()[0] == game.getModInstance('ClientMod').gameGui:
        # If the player has moved more than a certain distance, generate the world
        deltaPos = [abs(game.player.pos[a] - game.getModInstance('ClientMod').oldPlayerPos[a]) for a in (0, 1)]
        # TODO This still has the lag spikes (probably the thread copying the surfaces is causing it.)
        if (game.player.synced and not game.world.isWorldLoaded()) or max(deltaPos) > 16:
            if game.getModInstance('ClientMod').genLock:
                return

            # Generate the world on the client
            queue = Queue()
            p = Process(target=genWorld, args=(game, queue))
            t = Thread(target=handleProcess, args=(game, queue))
            p.daemon = True
            t.daemon = True
            p.start()
            t.start()

def onTickHandleMovement(game, tick):
    '''
    Event Hook: onTick
    Handle the motion of other players and the main client player
    '''
    animTicks = util.FPS//6
    if game.getGui() and game.getGui()[0] == game.getModInstance('ClientMod').gameGui:
        # Concatenate everything into a single list
        everythingList = game.world.players+game.world.entities
        # Interpolate the movement of every entity
        for o, obj in enumerate(everythingList):
            props = obj.getProperty('worldUpdate')

            if not props:
                continue

            # Get the number of ticks since the last sync to server
            moduloTick = animTicks-(game.tick-props.props['updateTick'])%animTicks

            # Calculate the change in position
            pos = obj.pos
            deltaPos = [props.props['newPos'][a]-pos[a] for a in (0, 1)]
            deltaPos = [deltaPos[0]/moduloTick, deltaPos[1]/moduloTick]

            # Apply the position transform to the player
            pos = [pos[a]+deltaPos[a] for a in (0, 1)]
            everythingList[o].pos = deepcopy(pos)

        # Split the objects into their respective lists again
        game.world.players = [a for a in everythingList if isinstance(a, Player)]
        game.world.entities = [a for a in everythingList if isinstance(a, Entity)]

        # Iterate and update the vehicle positions
        for v, vehicle in enumerate(game.world.vehicles):
            # If someone is driving, lock the vehicle to the driver position
            if game.world.vehicles[v].riders['driver'] is not None:
                p = game.getPlayer(game.world.vehicles[v].riders['driver'])
                if p:
                    game.world.vehicles[v].pos = list(p.pos)

            # Otherwise, interpolate the position based on the change since the last update
            else:
                props = vehicle.getProperty('worldUpdate')

                if not props:
                    continue

                # Get the number of ticks since the last sync to server
                moduloTick = animTicks-(game.tick-props.props['updateTick'])%animTicks

                # Calculate the change in position
                pos = vehicle.pos
                deltaPos = [props.props['newPos'][a]-pos[a] for a in (0, 1)]
                deltaPos = [deltaPos[0]/moduloTick, deltaPos[1]/moduloTick]

                # Apply the position transform to the player
                pos = [pos[a]+deltaPos[a] for a in (0, 1)]
                game.world.vehicles[v].pos = deepcopy(pos)

        # Handle player movement
        keys = pygame.key.get_pressed()
        speed = game.player.getSpeed(game)

        # Update the relative position
        if keys[pygame.K_UP]:
            game.player.pos[1] -= speed
        if keys[pygame.K_DOWN]:
            game.player.pos[1] += speed
        if keys[pygame.K_LEFT]:
            game.player.pos[0] -= speed
        if keys[pygame.K_RIGHT]:
            game.player.pos[0] += speed

def onTickSyncPlayer(game, tick):
    '''
    Event Hook: onTick
    Handle the synchronisation of the player information between the client and server
    '''
    # Check if this client has connected to a server
    if game.getModInstance('ClientMod').packetPipeline.connections:
        # Sync player data back to the server periodically
        if tick%(util.FPS//20) == 0:
            # Check if the player has moved
            if game.player.pos != game.getModInstance('ClientMod').oldPlayerPos:
                game.player.synced = False
                # Duplicate the player and set the position
                playerCopy = deepcopy(game.player)
                # Store the current relative position in the mod instance for later comparison
                game.getModInstance('ClientMod').oldPlayerPos = list(game.player.pos)
                # Send the copy of the player object in the packet
                game.packetPipeline.sendToServer(SyncPlayerPacket(playerCopy))

def handleProcess(game, queue):
    '''
    Handle the genWorld queue and link it back into the main thread
    '''
    # Enable the world generation lock
    game.getModInstance('ClientMod').genLock = True
    while True:
        data = queue.get()
        # If it's a list, update the world centre pos
        if isinstance(data, list):
            game.world.centrePos = data
        # If it's a tilemap, update that
        elif data != "end":
            for y, row in enumerate(data.map):
                for x, tile in enumerate(row):
                    data.map[y][x].resetTile(game.modLoader.gameRegistry.resources)

            game.world.setTileMap(data)

        # Otherwise, end the thread
        else:
            # Disable the world generation lock again
            game.getModInstance('ClientMod').genLock = False
            return

def genWorld(game, queue):
    '''
    Generate the small area of the world
    '''
    # Set the abs pos of the player
    preGenPos = game.player.pos
    print('genning world')

    # Generate the world
    dimension = game.getDimension(game.player.dimension)
    dimension.generate(preGenPos, game.modLoader.gameRegistry)
    # Fix the pygame surface breaking when sent through the Queue
    queue.put(dimension.getWorldObj().getTileMap())
    print('world gen done')
    queue.put(preGenPos)
