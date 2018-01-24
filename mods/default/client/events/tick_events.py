from api.packets import *

from threading import Thread
import pygame
from copy import deepcopy

def onTickGenerateWorld(game, tick):
    '''
    Event Hook: onTick
    Handles the generation of the world when necessary
    '''
    if game.openGUI[0] == game.getModInstance('ClientMod').gameGui:
        # If the player has moved more than a certain distance, generate the world
        absRelPos = [abs(a) for a in game.player.relPos]
        if (game.player.synced and not game.world.isWorldLoaded()) or max(absRelPos) > 26:
            # Set the second relative position to start iterating
            props = game.player.getProperty('relPos2')

            if props.props['ready']:
                return

            # Generate the world on the client
            t = Thread(target=genWorld, args=(game, props))
            t.daemon = True
            t.start()


def onTickHandleMovement(game, tick):
    '''
    Event Hook: onTick
    Handle the motion of other players and the main client player
    '''
    if game.openGUI[0] == game.getModInstance('ClientMod').gameGui:
        # Interpolate the movement of the other players
        for p in range(len(game.world.players)):
            props = game.world.players[p].getProperty('worldUpdate')

            # Get the number of ticks since the last sync to server
            moduloTick = 5-(game.tick-props.props['updateTick'])%5

            # Calculate the change in position
            pos = game.world.players[p].pos
            deltaPos = [props.props['newPos'][a]-pos[a] for a in (0, 1)]
            deltaPos = [deltaPos[0]/moduloTick, deltaPos[1]/moduloTick]

            # Apply the position transform to the player
            pos = [pos[a]+deltaPos[a] for a in (0, 1)]
            game.world.players[p].pos = deepcopy(pos)

        # Interpolate the movement of the entities
        for e in range(len(game.world.entities)):
            props = game.world.entities[e].getProperty('worldUpdate')

            # Get the number of ticks since the last sync to server
            moduloTick = 5-(game.tick-props.props['updateTick'])%5

            # Calculate the change in position
            pos = game.world.entities[e].pos
            deltaPos = [props.props['newPos'][a]-pos[a] for a in (0, 1)]
            deltaPos = [deltaPos[0]/moduloTick, deltaPos[1]/moduloTick]

            # Apply the position transform to the player
            pos = [pos[a]+deltaPos[a] for a in (0, 1)]
            game.world.entities[e].pos = deepcopy(pos)

        # Handle player movement
        keys = pygame.key.get_pressed()
        speed = 0.2

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
        if tick%3 == 0:
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

def genWorld(game, props):
    '''
    Generate the small area of the world
    '''
    # Set the abs pos of the player
    preGenPos = game.player.getAbsPos()
    print('genning world')
    props.props['ready'] = True
    game.player.setProperty('relPos2', props)

    # Generate the world
    dimension = game.getDimension(game.player.dimension)
    dimension.generate(preGenPos, game.modLoader.gameRegistry)
    game.world.setTileMap(dimension.getWorldObj().getTileMap())
    print('world gen done')

    # Fetch the player property
    props = game.player.getProperty('relPos2')

    # Move the player
    game.player.pos = preGenPos
    game.player.relPos = list(props.props['pos'])

    # Update the player property
    props.props['ready'] = False
    props.props['pos'] = [0, 0]

    # Set the property back into the player
    game.player.setProperty('relPos2', props)
