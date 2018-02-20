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
        absRelPos = [abs(a) for a in game.player.relPos]
        # TODO This still has the lag spikes (probably the thread copying the surfaces is causing it.)
        if (game.player.synced and not game.world.isWorldLoaded()) or max(absRelPos) > 16:
            # Set the second relative position to start iterating
            props = game.player.getProperty('relPos2')

            if props.props['ready']:
                return

            # Generate the world on the client
            queue = Queue()
            p = Process(target=genWorld, args=(game, props, queue))
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
        everythingList = game.world.players+game.world.entities+game.world.vehicles
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
        game.world.vehicles = [a for a in everythingList if isinstance(a, Vehicle)]

        # Handle player movement
        keys = pygame.key.get_pressed()
        speed = game.player.getSpeed()

        # Update the secondary relative position
        props = game.player.getProperty('relPos2')
        if props.props['ready']:
            if keys[pygame.K_UP]:
                props.props['pos'][1] -= speed
            if keys[pygame.K_DOWN]:
                props.props['pos'][1] += speed
            if keys[pygame.K_LEFT]:
                props.props['pos'][0] -= speed
            if keys[pygame.K_RIGHT]:
                props.props['pos'][0] += speed
            game.player.setProperty('relPos2', props)

        # Update the relative position
        if keys[pygame.K_UP]:
            game.player.relPos[1] -= speed
        if keys[pygame.K_DOWN]:
            game.player.relPos[1] += speed
        if keys[pygame.K_LEFT]:
            game.player.relPos[0] -= speed
        if keys[pygame.K_RIGHT]:
            game.player.relPos[0] += speed

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
            if game.player.relPos != game.getModInstance('ClientMod').oldPlayerPos:
                game.player.synced = False
                # Duplicate the player and set the position
                playerCopy = deepcopy(game.player)
                playerCopy.pos = list(game.player.getAbsPos())
                # Store the current relative position in the mod instance for later comparison
                game.getModInstance('ClientMod').oldPlayerPos = list(game.player.relPos)
                # Send the copy of the player object in the packet
                game.getModInstance('ClientMod').packetPipeline.sendToServer(SyncPlayerPacket(playerCopy))
                print('syncing player')

def handleProcess(game, queue):
    '''
    Handle the genWorld queue and link it back into the main thread
    '''
    while True:
        data = queue.get()
        # If it's a player property, update the player
        if isinstance(data, Property):
            game.player.setProperty('relPos2', data)
        # If it's a player, update the whole player
        elif isinstance(data, Player):
            game.player = data
        # If it's a tilemap, update that
        elif data != "end":
            for y, row in enumerate(data.map):
                for x, tile in enumerate(row):
                    data.map[y][x].resetTile(game.modLoader.gameRegistry.resources)

            game.world.setTileMap(data)
            queue.put(game.player.getProperty('relPos2'))

        # Otherwise, end the thread
        else:
            return

def genWorld(game, props, queue):
    '''
    Generate the small area of the world
    '''
    # Set the abs pos of the player
    preGenPos = game.player.getAbsPos()
    print('genning world')
    props.props['ready'] = True
    queue.put(props)

    # Generate the world
    dimension = game.getDimension(game.player.dimension)
    dimension.generate(preGenPos, game.modLoader.gameRegistry)
    # Fix the pygame surface breaking when sent through the Queue
    queue.put(dimension.getWorldObj().getTileMap())
    print('world gen done')

    # Fetch the player property
    props = queue.get()
    #props = game.player.getProperty('relPos2')

    # Move the player
    game.player.pos = preGenPos
    game.player.relPos = list(props.props['pos'])
    queue.put(game.player)

    # Update the player property
    props.props['ready'] = False
    props.props['pos'] = [0, 0]

    # Set the property back into the player
    queue.put(props)
    queue.put('end')
